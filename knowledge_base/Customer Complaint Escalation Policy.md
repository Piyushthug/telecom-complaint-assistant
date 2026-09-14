# Customer Complaint Escalation Policy

**Document Type:** Customer Support Escalation Policy  
**Document ID:** KB-ESC-001  
**Version:** 1.0  
**Status:** Active

## 1. Purpose

This policy defines when a customer complaint should be considered for escalation to a specialized support team or human support representative.

## 2. Escalation Indicators

A complaint may require escalation when:

- The issue remains unresolved after supported troubleshooting.
- The customer has repeatedly contacted support about the same issue.
- The complaint requires access to an internal system unavailable to the assistant.
- The issue requires manual approval.
- The complaint falls outside the assistant's supported policies.
- The customer disputes a previous resolution.

## 3. Repeated Complaints

Repeated contact is an important escalation signal.

Examples:

- Three or more contacts about the same unresolved issue.
- Multiple complaints within a short period.
- Previous troubleshooting was unsuccessful.

Repeated contact does not automatically determine the final resolution.

## 4. High-Frustration Customers

When a customer expresses strong frustration:

- Acknowledge the customer's concern.
- Avoid argumentative language.
- Provide the next appropriate step.
- Consider escalation when the complaint also meets an escalation condition.

Sentiment alone should not determine the final business resolution.

## 5. Human Handoff

A human handoff should be considered when:

- The assistant cannot find sufficient information in the knowledge base.
- The complaint requires an action that the assistant cannot perform.
- The policy requires human approval.
- The assistant's response cannot be confidently grounded in the available information.

## 6. Important Restrictions

The assistant must not claim:

- That a ticket has been created unless the ticketing system confirms it.
- That a human agent has been assigned unless confirmed.
- That an escalation has been completed unless an authorized system confirms it.
- That compensation has been approved without confirmation.

## 7. Example

**Customer:**  
"I have contacted support three times and my internet is still not working."

**Signals:**

- Category: `INTERNET_OUTAGE`
- Repeated contact: `TRUE`
- Sentiment: likely `NEGATIVE`

**Recommended handling:**

Acknowledge the repeated issue, review the applicable outage policy, and evaluate the complaint for escalation.