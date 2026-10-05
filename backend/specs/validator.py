from collections import defaultdict, deque
from typing import NamedTuple
from backend.specs.models import DatasetSpec, FieldType

class DiagnosticError(NamedTuple):
    code: str
    path: str
    message: str

class SpecValidationError(Exception):
    def __init__(self, diagnostics: list[DiagnosticError]):
        self.diagnostics = diagnostics
        super().__init__(f"Specification failed semantic validation with {len(diagnostics)} errors")

def validate_spec_semantics(spec: DatasetSpec) -> list[DiagnosticError]:
    """Validates structural semantics, field references, and dependency constraints."""
    diagnostics: list[DiagnosticError] = []
    field_map = {f.name: f for f in spec.fields}
    field_names = set(field_map.keys())

    # Build dependency graph
    dependency_graph: dict[str, set[str]] = defaultdict(set)

    for idx, field in enumerate(spec.fields):
        path = f"fields[{idx}].{field.name}"
        gen = field.generator

        # 1. Check generator dependency references
        if gen.kind == "conditional_categorical":
            if gen.depends_on not in field_names:
                diagnostics.append(DiagnosticError(
                    code="MISSING_DEPENDENCY",
                    path=f"{path}.generator.depends_on",
                    message=f"Referenced dependency '{gen.depends_on}' does not exist in schema.",
                ))
            else:
                dep_field = field_map[gen.depends_on]
                if dep_field.type != FieldType.CATEGORY:
                    diagnostics.append(DiagnosticError(
                        code="INVALID_DEPENDENCY_TYPE",
                        path=f"{path}.generator.depends_on",
                        message=f"Parent field '{gen.depends_on}' must be of type 'category', got '{dep_field.type.value}'.",
                    ))
                dependency_graph[field.name].add(gen.depends_on)

        elif gen.kind == "derived_datetime":
            if gen.created_field not in field_names:
                diagnostics.append(DiagnosticError(
                    code="MISSING_DEPENDENCY",
                    path=f"{path}.generator.created_field",
                    message=f"Referenced created_field '{gen.created_field}' does not exist.",
                ))
            else:
                if field_map[gen.created_field].type != FieldType.DATETIME:
                    diagnostics.append(DiagnosticError(
                        code="INVALID_DEPENDENCY_TYPE",
                        path=f"{path}.generator.created_field",
                        message=f"Field '{gen.created_field}' must be of type 'datetime'.",
                    ))
                dependency_graph[field.name].add(gen.created_field)

            if gen.status_field not in field_names:
                diagnostics.append(DiagnosticError(
                    code="MISSING_DEPENDENCY",
                    path=f"{path}.generator.status_field",
                    message=f"Referenced status_field '{gen.status_field}' does not exist.",
                ))
            else:
                if field_map[gen.status_field].type != FieldType.CATEGORY:
                    diagnostics.append(DiagnosticError(
                        code="INVALID_DEPENDENCY_TYPE",
                        path=f"{path}.generator.status_field",
                        message=f"Field '{gen.status_field}' must be of type 'category'.",
                    ))
                dependency_graph[field.name].add(gen.status_field)

        elif gen.kind == "llm_text":
            for dep in gen.depends_on:
                if dep not in field_names:
                    diagnostics.append(DiagnosticError(
                        code="MISSING_DEPENDENCY",
                        path=f"{path}.generator.depends_on",
                        message=f"LLM text dependency '{dep}' does not exist in schema.",
                    ))
                else:
                    if field_map[dep].type == FieldType.TEXT:
                        diagnostics.append(DiagnosticError(
                            code="INVALID_DEPENDENCY_CHAIN",
                            path=f"{path}.generator.depends_on",
                            message=f"Text field cannot depend on another text field ('{dep}').",
                        ))
                    dependency_graph[field.name].add(dep)

    # 2. Check constraint field references
    for idx, c in enumerate(spec.constraints):
        path = f"constraints[{idx}].{c.kind}"
        if c.field not in field_names:
            diagnostics.append(DiagnosticError(
                code="CONSTRAINT_UNKNOWN_FIELD",
                path=f"{path}.field",
                message=f"Constraint references unknown field '{c.field}'.",
            ))
        if c.target_field and c.target_field not in field_names:
            diagnostics.append(DiagnosticError(
                code="CONSTRAINT_UNKNOWN_FIELD",
                path=f"{path}.target_field",
                message=f"Constraint references unknown target field '{c.target_field}'.",
            ))
        if c.condition_field and c.condition_field not in field_names:
            diagnostics.append(DiagnosticError(
                code="CONSTRAINT_UNKNOWN_FIELD",
                path=f"{path}.condition_field",
                message=f"Constraint references unknown condition field '{c.condition_field}'.",
            ))

    # 3. Detect dependency cycles
    has_cycle, cycle_fields = detect_cycle(field_names, dependency_graph)
    if has_cycle:
        diagnostics.append(DiagnosticError(
            code="CIRCULAR_DEPENDENCY",
            path="fields",
            message=f"Circular dependency cycle detected involving fields: {', '.join(cycle_fields)}",
        ))

    return diagnostics

def detect_cycle(all_nodes: set[str], graph: dict[str, set[str]]) -> tuple[bool, list[str]]:
    """Detects if a directed dependency graph has cycles using Kahn's algorithm."""
    in_degree: dict[str, int] = {node: 0 for node in all_nodes}
    adj: dict[str, list[str]] = defaultdict(list)

    # graph[u] = {v} means u depends on v (edge v -> u: v must be computed before u)
    for u, deps in graph.items():
        for v in deps:
            if v in in_degree:
                adj[v].append(u)
                in_degree[u] += 1

    queue = deque([node for node, deg in in_degree.items() if deg == 0])
    visited_count = 0

    while queue:
        node = queue.popleft()
        visited_count += 1
        for neighbor in adj[node]:
            in_degree[neighbor] -= 1
            if in_degree[neighbor] == 0:
                queue.append(neighbor)

    if visited_count < len(all_nodes):
        # Nodes that could not be freed belong to or are blocked by cycles
        cycle_nodes = sorted([node for node, deg in in_degree.items() if deg > 0])
        return True, cycle_nodes
    return False, []

def get_topological_generation_order(spec: DatasetSpec) -> list[str]:
    """Returns a deterministic topological evaluation order for fields in the spec."""
    diagnostics = validate_spec_semantics(spec)
    if diagnostics:
        raise SpecValidationError(diagnostics)

    all_nodes = [f.name for f in spec.fields]
    in_degree = {name: 0 for name in all_nodes}
    adj = defaultdict(list)

    # Reconstruct edges: if u depends on v, then v -> u
    for field in spec.fields:
        gen = field.generator
        deps: set[str] = set()
        if gen.kind == "conditional_categorical":
            deps.add(gen.depends_on)
        elif gen.kind == "derived_datetime":
            deps.add(gen.created_field)
            deps.add(gen.status_field)
        elif gen.kind == "llm_text":
            deps.update(gen.depends_on)

        for v in deps:
            adj[v].append(field.name)
            in_degree[field.name] += 1

    # Preserve declared schema order as tie-breaker
    queue = deque([name for name in all_nodes if in_degree[name] == 0])
    order: list[str] = []

    while queue:
        node = queue.popleft()
        order.append(node)
        for neighbor in adj[node]:
            in_degree[neighbor] -= 1
            if in_degree[neighbor] == 0:
                queue.append(neighbor)

    return order
