from datetime import datetime, timedelta, timezone
import numpy as np
from scipy import stats

def get_rng(seed: int | None = 42) -> np.random.Generator:
    """Creates a seeded NumPy random number generator."""
    return np.random.default_rng(seed)

def sample_categorical(
    categories: list[str],
    probabilities: list[float] | None,
    count: int,
    rng: np.random.Generator,
) -> list[str]:
    """Seeded probabilistic categorical draws."""
    if count <= 0:
        return []
    p = np.array(probabilities) if probabilities is not None else None
    if p is not None:
        p = p / p.sum()  # Normalize to guarantee exact float sum of 1.0
    indices = rng.choice(len(categories), size=count, replace=True, p=p)
    return [categories[i] for i in indices]

def allocate_fixed_proportions(
    categories: list[str],
    probabilities: list[float] | None,
    count: int,
    rng: np.random.Generator,
) -> list[str]:
    """Largest-remainder (Hare-Niemeyer) allocation for exact category counts.
    
    Guarantees exact quotas even for small or uneven row counts, with stable
    tie-breaking and deterministic seed shuffling.
    """
    if count <= 0:
        return []
    k = len(categories)
    if probabilities is None:
        probs = np.full(k, 1.0 / k)
    else:
        probs = np.array(probabilities, dtype=float)
        probs = probs / probs.sum()

    exact_counts = count * probs
    floored_counts = np.floor(exact_counts).astype(int)
    remainders = exact_counts - floored_counts
    remainder_to_distribute = count - int(floored_counts.sum())

    # Stable tie-break by remainder descending, then original index ascending
    indices = list(range(k))
    indices.sort(key=lambda i: (-remainders[i], i))

    for i in range(remainder_to_distribute):
        floored_counts[indices[i]] += 1

    allocated: list[str] = []
    for cat, c in zip(categories, floored_counts):
        allocated.extend([cat] * int(c))

    # Deterministic permutation using the provided rng
    permuted_indices = rng.permutation(count)
    return [allocated[i] for i in permuted_indices]

def sample_boolean(
    probability_true: float,
    count: int,
    rng: np.random.Generator,
) -> list[bool]:
    """Samples boolean values with specified probability of True."""
    if count <= 0:
        return []
    draws = rng.uniform(0.0, 1.0, size=count)
    return [bool(x < probability_true) for x in draws]

def sample_uniform(
    min_value: float,
    max_value: float,
    count: int,
    precision: int | None,
    rng: np.random.Generator,
    as_integer: bool = False,
) -> list[float | int]:
    """Samples uniform distribution within [min_value, max_value]."""
    if count <= 0:
        return []
    if as_integer:
        # rng.integers is high-exclusive, so max_value + 1 for inclusion
        low = int(np.floor(min_value))
        high = int(np.floor(max_value)) + 1
        return [int(x) for x in rng.integers(low, high, size=count)]

    draws = rng.uniform(min_value, max_value, size=count)
    if precision is not None:
        return [round(float(x), precision) for x in draws]
    return [float(x) for x in draws]

def sample_truncated_normal(
    mean: float,
    std_dev: float,
    lower: float,
    upper: float,
    count: int,
    precision: int | None,
    rng: np.random.Generator,
    as_integer: bool = False,
) -> list[float | int]:
    """Samples truncated normal distribution strictly within [lower, upper]."""
    if count <= 0:
        return []
    a = (lower - mean) / std_dev
    b = (upper - mean) / std_dev

    # Use scipy's truncnorm with NumPy generator
    draws = stats.truncnorm.rvs(a, b, loc=mean, scale=std_dev, size=count, random_state=rng)
    # Clip in case of extreme floating point edge cases
    clipped = np.clip(draws, lower, upper)

    if as_integer:
        return [int(np.round(x)) for x in clipped]
    if precision is not None:
        return [round(float(x), precision) for x in clipped]
    return [float(x) for x in clipped]

def generate_identifiers(
    prefix: str,
    start_index: int,
    pad_width: int,
    count: int,
) -> list[str]:
    """Generates visibly synthetic, strictly unique sequential identifiers."""
    return [f"{prefix}{start_index + i:0{pad_width}d}" for i in range(count)]

def sample_datetimes(
    start_date: datetime,
    end_date: datetime,
    count: int,
    rng: np.random.Generator,
) -> list[datetime]:
    """Samples UTC datetimes uniformly between start_date and end_date."""
    if count <= 0:
        return []
    # Ensure UTC timezone
    if start_date.tzinfo is None:
        start_date = start_date.replace(tzinfo=timezone.utc)
    if end_date.tzinfo is None:
        end_date = end_date.replace(tzinfo=timezone.utc)

    start_ts = start_date.timestamp()
    end_ts = end_date.timestamp()
    draws = rng.uniform(start_ts, end_ts, size=count)

    return [datetime.fromtimestamp(ts, tz=timezone.utc) for ts in draws]
