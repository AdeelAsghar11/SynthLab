# Phase P6.3: Human Consistency & Screening Review

## Automated Screening Policy Metrics
- **Test Set Size:** 10 hand-crafted edge cases
- **Recall (Safety Catch Rate):** 100.0% (Target > 99%)
- **Precision (Accuracy of Flags):** 100.0% 
- **False Refusal Rate (Safe rows rejected):** 0.0% (Target < 2%)

*Limits Documented:* The regex-based screening reliably blocks standard PII (CNIC, Emails, Credit Cards) but does not do semantic intent filtering. Semantic filtering requires the LLM Adapter safety system prompts.

## Stratified Human Review Rubric

Please review the following samples from the deterministic generator.

### Sample: Category `delivery`
```json
{
  "ticket_id": "SYN-TKT-01001",
  "category": "delivery",
  "priority": "medium",
  "order_value": 1190.28,
  "created_at": "2026-05-29T12:14:48.062274+00:00",
  "status": "open",
  "resolved_at": "NaT",
  "message": "Delivery address confirmation requested for my recent order of PKR 1190.28. Expected arrival was yesterday."
}
```
**Review Criteria:**
- [ ] **Fidelity:** Does the `message` accurately reflect the `category` (delivery)?
- [ ] **Consistency:** Does the `message` contain the correct `order_value` (1190.28)?
- [ ] **Tone:** Is the language appropriate for a synthetic support ticket?
- [ ] **Safety:** Are there any un-flagged PII leaks in the message?
- [ ] **Structure:** Is the JSON structure intact and matching the schema?

### Sample: Category `payment`
```json
{
  "ticket_id": "SYN-TKT-01005",
  "category": "payment",
  "priority": "high",
  "order_value": 6351.19,
  "created_at": "2026-01-25T21:21:52.042045+00:00",
  "status": "resolved",
  "resolved_at": "2026-01-26T19:01:25.714949+00:00",
  "message": "My payment of PKR 6351.19 was deducted twice from my account. Please refund the duplicate transaction."
}
```
**Review Criteria:**
- [ ] **Fidelity:** Does the `message` accurately reflect the `category` (payment)?
- [ ] **Consistency:** Does the `message` contain the correct `order_value` (6351.19)?
- [ ] **Tone:** Is the language appropriate for a synthetic support ticket?
- [ ] **Safety:** Are there any un-flagged PII leaks in the message?
- [ ] **Structure:** Is the JSON structure intact and matching the schema?

### Sample: Category `returns`
```json
{
  "ticket_id": "SYN-TKT-01007",
  "category": "returns",
  "priority": "high",
  "order_value": 5404.5,
  "created_at": "2026-05-21T00:00:08.334721+00:00",
  "status": "open",
  "resolved_at": "NaT",
  "message": "Received damaged item in the parcel. Requesting replacement or return for order value PKR 5404.5."
}
```
**Review Criteria:**
- [ ] **Fidelity:** Does the `message` accurately reflect the `category` (returns)?
- [ ] **Consistency:** Does the `message` contain the correct `order_value` (5404.5)?
- [ ] **Tone:** Is the language appropriate for a synthetic support ticket?
- [ ] **Safety:** Are there any un-flagged PII leaks in the message?
- [ ] **Structure:** Is the JSON structure intact and matching the schema?

