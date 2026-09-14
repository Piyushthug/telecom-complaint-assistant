# Telecom Customer Complaint Resolution Assistant
## 0-Cost Local Project — Step-by-Step Execution Plan

## 1. Project Goal

Build a simple local AI-powered Telecom Customer Complaint Resolution Assistant that can:

1. Accept a customer complaint.
2. Analyze customer sentiment.
3. Categorize the complaint.
4. Summarize the complaint.
5. Retrieve relevant telecom complaint policies/SOPs using RAG.
6. Generate a suggested response.
7. Validate the generated response against the retrieved knowledge.
8. Regenerate the response when validation fails.

The primary focus is **clean agent orchestration using LangGraph**, not production-scale infrastructure.

---

# 2. Project Constraints

## Cost

The project must run at **₹0 / $0 API cost**.

Do not depend on paid APIs or cloud services.

## Local-first technology

Use:

- Python
- FastAPI
- LangGraph
- LangChain where useful
- Ollama for a local LLM
- Sentence Transformers for local embeddings
- FAISS for local vector search
- SQLite for simple local persistence if required
- React for the UI
- Markdown/PDF files for the knowledge base

## Avoid initially

Do not add:

- Pinecone
- Qdrant Cloud
- OpenAI API
- Paid embedding APIs
- Redis
- Kafka
- Kubernetes
- Cloud deployment
- Complex microservices

Only add infrastructure if there is a clear project requirement later.

---

# 3. Target Architecture

```text
                    React UI
                       |
                       v
                 FastAPI Backend
                       |
                       v
                LangGraph Workflow
                       |
              +--------+--------+
              |                 |
          PARALLEL           PARALLEL
              |                 |
              v                 v
       Sentiment Agent    Categorization Agent
              |                 |
              +--------+--------+
                       |
                       v
                Summarization Agent
                       |
                       v
                  RAG Retrieval
                       |
                 +-----+------+
                 |            |
              Embedding      FAISS
               Model        Search
                 |            |
                 +-----+------+
                       |
                       v
              Response Generation
                       |
                       v
                  Validator
                       |
                +------+------+
                |             |
              PASS           FAIL
                |             |
                v             v
              END       Regenerate Response
                              |
                              +----> Validator
```

---

# 4. Phase 1 — Repository Setup

## Goal

Create the basic project structure.

## Tasks

- Create Git repository.
- Create Python virtual environment.
- Create backend directory.
- Create frontend directory.
- Create knowledge base directory.
- Create data directory.
- Create scripts directory.
- Add `.gitignore`.
- Add `README.md`.
- Add `requirements.txt`.

## Target structure

```text
telecom-complaint-assistant/
|
├── backend/
├── frontend/
├── knowledge_base/
├── data/
├── scripts/
├── tests/
├── .gitignore
├── README.md
└── requirements.txt
```

## Completion criteria

- Project starts locally.
- Python environment works.
- Git repository is initialized.
- README explains the project.

---

# 5. Phase 2 — Create Knowledge Base

## Goal

Create synthetic enterprise documents for RAG.

## Documents

```text
knowledge_base/
|
├── internet_outage_policy.md
├── slow_internet_sop.md
├── billing_complaint_policy.md
├── refund_policy.md
└── escalation_policy.md
```

## Content requirements

Each document should contain:

- Document ID
- Version
- Purpose
- Scope
- Rules
- Troubleshooting/resolution guidance
- Escalation conditions
- Restrictions
- Examples

## Important rule

These are completely synthetic documents.

Do not use real customer information.

## Completion criteria

The documents contain enough distinct information that a complaint about:

- Internet outage
- Slow internet
- Billing
- Refund
- Escalation

can retrieve the appropriate policy.

---

# 6. Phase 3 — Generate Synthetic Complaint Dataset

## Goal

Create realistic but fake telecom complaint data.

## Files

```text
data/
├── complaints.json
└── complaint_history.csv
```

## Complaint dataset fields

```text
complaint_id
customer_id
complaint
category
sentiment
channel
created_at
```

Example:

```json
{
  "complaint_id": "CMP001",
  "customer_id": "C001",
  "complaint": "My internet has been down since yesterday.",
  "category": "INTERNET_OUTAGE",
  "sentiment": "NEGATIVE",
  "channel": "CHAT"
}
```

## Categories

Start with:

```text
INTERNET_OUTAGE
SLOW_INTERNET
BILLING
REFUND
CUSTOMER_SERVICE
```

## Sentiments

Use:

```text
POSITIVE
NEUTRAL
NEGATIVE
VERY_NEGATIVE
```

## Generate

Start with approximately:

```text
100–300 synthetic complaints
```

Do not spend time generating thousands of records.

## Completion criteria

Dataset contains varied:

- complaint categories
- sentiment levels
- short complaints
- long complaints
- repeated complaints
- ambiguous complaints

---

# 7. Phase 4 — Build Local Embedding Pipeline

## Goal

Convert knowledge-base chunks into vectors locally.

## Technology

Use:

```text
sentence-transformers
```

Start with a small free embedding model such as:

```text
all-MiniLM-L6-v2
```

## Pipeline

```text
Markdown Documents
       |
       v
Document Loader
       |
       v
Chunking
       |
       v
Sentence Transformer
       |
       v
Embedding Vectors
```

## Files

```text
backend/rag/
├── document_loader.py
├── chunker.py
└── embeddings.py
```

## Completion criteria

A test script should:

1. Load knowledge-base documents.
2. Split them into chunks.
3. Generate embeddings.
4. Print the embedding dimensions.

---

# 8. Phase 5 — Build FAISS Vector Store

## Goal

Store and search embeddings locally.

## Technology

```text
FAISS
```

## Pipeline

```text
Document Chunk
      |
      v
Embedding
      |
      v
FAISS Index
      |
      v
Local Disk
```

## Files

```text
backend/rag/
└── faiss_store.py
```

## Required functionality

Implement:

```python
build_index()
save_index()
load_index()
search(query, top_k)
```

## Initial retrieval setting

Start with:

```text
top_k = 3
```

Keep the value configurable.

## Completion criteria

Given:

```text
"My internet is completely down."
```

the retriever should return chunks from:

```text
internet_outage_policy.md
```

For:

```text
"My internet is working but very slow."
```

it should favor:

```text
slow_internet_sop.md
```

---

# 9. Phase 6 — Build Local LLM Service

## Goal

Use an LLM without paying for an API.

## Technology

Use:

```text
Ollama
```

with a suitable local instruct model.

The exact model can depend on the user's machine hardware.

## Create

```text
backend/llm/
└── ollama_client.py
```

## Required function

```python
generate(prompt)
```

The rest of the application should not directly depend on Ollama.

This keeps the LLM provider replaceable.

## Completion criteria

A Python test can send:

```text
"Classify this telecom complaint..."
```

and receive a response from the local model.

---

# 10. Phase 7 — Define LangGraph State

## Goal

Create the shared state passed between agents.

## File

```text
backend/graph/state.py
```

## Initial state

```python
class ComplaintState:
    complaint: str
    customer_id: str

    sentiment: str
    sentiment_score: float

    category: str
    category_confidence: float

    summary: str

    retrieved_documents: list

    suggested_response: str

    validation_status: str
    validation_reason: str

    retry_count: int
```

The state is the main communication mechanism between agents.

---

# 11. Phase 8 — Build Sentiment Agent

## Goal

Analyze customer sentiment.

## File

```text
backend/agents/sentiment_agent.py
```

## Input

```text
complaint
```

## Output

```json
{
  "sentiment": "VERY_NEGATIVE",
  "confidence": 0.91
}
```

## Important

The sentiment agent should update LangGraph state.

It should not directly call another agent.

---

# 12. Phase 9 — Build Categorization Agent

## Goal

Determine complaint category.

## File

```text
backend/agents/categorization_agent.py
```

## Example

Input:

```text
"I was charged twice this month."
```

Output:

```text
BILLING
```

## Important

Use a controlled list of categories.

Do not allow the LLM to generate unlimited category names.

---

# 13. Phase 10 — Implement Parallel Execution

## Goal

Run independent agents at the same time.

Sentiment and categorization do not depend on each other's output.

Therefore:

```text
                 Complaint
                     |
              LangGraph Node
                /                        /                         v             v
         Sentiment      Categorization
              \             /
               \           /
                +----+----+
                     |
                     v
                Next Node
```

## Why this matters

This is one of the core architectural requirements of the project.

Explain in interviews:

> Sentiment and categorization are independent analysis tasks, so they can execute in parallel to reduce workflow latency.

## Completion criteria

LangGraph successfully merges both results into shared state.

---

# 14. Phase 11 — Build Summarization Agent

## Goal

Create a concise complaint summary.

## File

```text
backend/agents/summarization_agent.py
```

## Input

```text
complaint
sentiment
category
```

## Output

Example:

```text
Customer has experienced an internet outage
for two days and has contacted support multiple
times without resolution.
```

---

# 15. Phase 12 — Integrate RAG

## Goal

Retrieve relevant policy information before generating the response.

## Pipeline

```text
Complaint
   |
   v
Category
   |
   v
Query
   |
   v
Embedding Model
   |
   v
FAISS
   |
   v
Top 3 Chunks
```

## File

```text
backend/rag/retriever.py
```

## Retrieval output

Store results in:

```python
state.retrieved_documents
```

Each result should preserve:

```text
document name
chunk text
similarity score
metadata
```

---

# 16. Phase 13 — Build Response Generation Agent

## Goal

Generate a customer-facing suggested response.

## File

```text
backend/agents/response_agent.py
```

## Prompt context

The agent should receive:

```text
Original complaint
+
Complaint category
+
Sentiment
+
Summary
+
Retrieved policy chunks
```

## Critical instruction

The response must use retrieved policy information and must not invent:

- refunds
- ticket numbers
- technician visits
- outage causes
- resolution times
- compensation

unless the provided context explicitly supports them.

---

# 17. Phase 14 — Build Validation Agent

## Goal

Check the generated response before returning it.

## File

```text
backend/agents/validator_agent.py
```

## Validate

Check whether:

1. Response addresses the complaint.
2. Response is supported by retrieved policy.
3. Response does not invent facts.
4. Response does not make unsupported promises.
5. Response follows complaint policy.

## Output

```json
{
  "status": "PASS",
  "reason": "Response is supported by retrieved policy."
}
```

or:

```json
{
  "status": "FAIL",
  "reason": "Response promises a refund without policy support."
}
```

---

# 18. Phase 15 — Add Conditional Retry

## Goal

Demonstrate LangGraph conditional routing.

```text
                  Validator
                     |
              +------+------+
              |             |
             PASS          FAIL
              |             |
              v             v
             END       Generate Again
                            |
                            v
                         Validator
```

Use a retry limit.

Start with:

```text
MAX_RETRIES = 2
```

If validation still fails after the retry limit:

```text
Escalate / return safe fallback response
```

This prevents infinite loops.

---

# 19. Phase 16 — Build FastAPI

## Goal

Expose the workflow through an API.

## File

```text
backend/main.py
```

## Endpoint

```http
POST /complaint
```

## Request

```json
{
  "customer_id": "C001",
  "complaint": "My internet has been down since yesterday."
}
```

## Response

```json
{
  "category": "INTERNET_OUTAGE",
  "sentiment": "NEGATIVE",
  "summary": "...",
  "response": "...",
  "validation_status": "PASS"
}
```

---

# 20. Phase 17 — Build Simple React UI

## Goal

Create a minimal demo interface.

## UI should contain

- Complaint text box
- Customer ID input
- Submit button
- Complaint summary
- Sentiment
- Category
- Suggested response
- Retrieved policy references
- Validation status

## Example

```text
------------------------------------------------
 Telecom Complaint Resolution Assistant
------------------------------------------------

Customer ID:
[C001]

Complaint:
[ My internet has been down since yesterday... ]

                 [ Analyze Complaint ]

------------------------------------------------

Category: INTERNET_OUTAGE
Sentiment: VERY_NEGATIVE

Summary:
Customer reports an unresolved internet outage...

Suggested Response:
...

Policy Sources:
- internet_outage_policy.md
- escalation_policy.md

Validation: PASS
------------------------------------------------
```

Keep the UI simple.

---

# 21. Phase 18 — Add Complaint History

## Goal

Demonstrate synthetic enterprise data.

Use SQLite.

Example table:

```text
complaint_history
------------------
complaint_id
customer_id
category
status
created_at
resolution_time
```

Initially, this is only for context/display.

Do not build a complex database architecture.

---

# 22. Phase 19 — Add Repeated Complaint Logic

Use complaint history to identify repeated issues.

Example:

```text
Customer C001

Complaint 1 → Internet outage
Complaint 2 → Internet outage
Complaint 3 → Internet outage
```

The workflow can produce:

```text
repeated_contact = true
```

This can be passed to the escalation decision.

Important:

> Do not make sentiment alone determine escalation.

Use multiple signals:

```text
category
+
previous complaints
+
current complaint
+
policy
```

---

# 23. Phase 20 — Add Final Escalation Path

Final graph:

```text
START
 |
 v
Parallel Analysis
 |          |
 v          v
Sentiment  Category
 |          |
 +----+-----+
      |
      v
 Summary
      |
      v
   RAG
      |
      v
 Generate Response
      |
      v
 Validate
      |
   +--+--+
   |     |
 PASS   FAIL
   |     |
   |     v
   |   Retry
   |     |
   |     v
   |  Validate
   |
   v
  END
```

If validation repeatedly fails:

```text
Human Escalation / Safe Fallback
```

---

# 24. Phase 21 — Testing

## Unit tests

Test each component independently:

```text
test_sentiment_agent
test_category_agent
test_summarization
test_embeddings
test_faiss_search
test_response_generation
test_validator
```

## RAG tests

Test queries such as:

```text
"My internet is completely down."
```

Expected:

```text
internet_outage_policy.md
```

---

```text
"My internet works but is very slow."
```

Expected:

```text
slow_internet_sop.md
```

---

```text
"I was charged twice."
```

Expected:

```text
billing_complaint_policy.md
```

---

```text
"Can I get my money back?"
```

Expected:

```text
refund_policy.md
```

---

```text
"I contacted support three times and nothing happened."
```

Expected:

```text
escalation_policy.md
```

---

# 25. Phase 22 — End-to-End Testing

Test complete scenarios.

## Scenario 1 — Internet outage

```text
Complaint
    ↓
Sentiment
    ↓
Category = INTERNET_OUTAGE
    ↓
RAG
    ↓
Response
    ↓
Validation
    ↓
PASS
```

## Scenario 2 — Billing

```text
Complaint
    ↓
Category = BILLING
    ↓
Billing Policy
    ↓
Response
    ↓
Validation
```

## Scenario 3 — Repeated complaint

```text
Complaint
+
Complaint History
    ↓
Repeated Contact
    ↓
Escalation Policy
    ↓
Response / Escalation
```

## Scenario 4 — Unsupported request

The assistant should not invent an answer.

Expected behavior:

```text
Insufficient information
       ↓
Safe response
       ↓
Human escalation if appropriate
```

---

# 26. Phase 23 — Logging

Add simple local logging.

Log:

```text
request_id
customer_id
category
sentiment
retrieved_documents
validation_status
retry_count
latency
```

Do not log unnecessary sensitive information.

Use normal Python logging.

No paid observability platform is required.

---

# 27. Phase 24 — Evaluation

Create a small evaluation dataset.

For each complaint, define:

```text
expected_category
expected_sentiment
expected_document
```

Example:

```text
Complaint:
"My internet has been down all day."

Expected Category:
INTERNET_OUTAGE

Expected Document:
internet_outage_policy.md
```

Measure simple metrics:

### Categorization accuracy

```text
correct classifications / total complaints
```

### Retrieval accuracy

Check whether the expected policy appears in Top-K.

### Validation rate

Measure how many generated responses pass validation.

Do not overcomplicate evaluation initially.

---

# 28. Phase 25 — Documentation

README should explain:

1. Business problem
2. Architecture
3. Agent responsibilities
4. LangGraph workflow
5. Parallel execution
6. Sequential execution
7. RAG pipeline
8. FAISS
9. Embedding model
10. Local LLM
11. Synthetic data
12. Setup instructions
13. Example requests
14. Example responses
15. Design decisions
16. Limitations
17. Future improvements

---

# 29. Final Project Flow

The finished application should behave like this:

```text
Customer Complaint
       |
       v
     FastAPI
       |
       v
   LangGraph
       |
       +----------------+
       |                |
       v                v
  Sentiment        Categorization
       |                |
       +-------+--------+
               |
               v
          Summarization
               |
               v
             RAG
               |
       +-------+-------+
       |               |
 Embedding Model      FAISS
       |               |
       +-------+-------+
               |
               v
       Retrieved Context
               |
               v
       Response Generator
               |
               v
           Validator
               |
          +----+----+
          |         |
        PASS       FAIL
          |         |
          v         v
        Final     Retry
                   |
                   v
                Validate
```

---

# 30. Definition of Done

The project is complete when:

- [ ] React UI works.
- [ ] FastAPI API works.
- [ ] Complaint can be submitted.
- [ ] LangGraph controls the workflow.
- [ ] Sentiment agent works.
- [ ] Categorization agent works.
- [ ] Sentiment + categorization execute in parallel.
- [ ] Summarization works.
- [ ] Knowledge base is loaded.
- [ ] Local embedding model works.
- [ ] FAISS index works.
- [ ] Top-K retrieval works.
- [ ] Response generation works.
- [ ] Validator works.
- [ ] Failed validation triggers retry.
- [ ] Retry limit prevents infinite loops.
- [ ] Synthetic complaint dataset exists.
- [ ] Complaint history exists.
- [ ] Repeated complaint detection works.
- [ ] Escalation path exists.
- [ ] Basic tests pass.
- [ ] README documents the architecture.
- [ ] Project runs locally without paid APIs.

---

# 31. Recommended Build Order

Do NOT build everything at once.

Build in this exact order:

```text
1. Repository
       ↓
2. Knowledge Base
       ↓
3. Synthetic Dataset
       ↓
4. Embedding Model
       ↓
5. FAISS
       ↓
6. Test RAG independently
       ↓
7. Local LLM
       ↓
8. LangGraph State
       ↓
9. Sentiment Agent
       ↓
10. Categorization Agent
       ↓
11. Parallel Execution
       ↓
12. Summarization Agent
       ↓
13. RAG Integration
       ↓
14. Response Agent
       ↓
15. Validator
       ↓
16. Conditional Retry
       ↓
17. FastAPI
       ↓
18. SQLite Complaint History
       ↓
19. React UI
       ↓
20. Testing
       ↓
21. Documentation
```

## Important Principle

**Build and test one layer at a time.**

For example, before integrating RAG with LangGraph:

```text
Query
  ↓
Embedding
  ↓
FAISS
  ↓
Relevant chunks
```

must work independently.

Then:

```text
LangGraph
  ↓
Agent
  ↓
RAG
```

Then add FastAPI.

Then add React.

This keeps debugging simple and makes it easy to explain every architectural decision during an interview.

---

# 32. Interview-Level Architecture Summary

The project can be explained in one sentence:

> "I built a zero-cost local telecom complaint resolution assistant using FastAPI and LangGraph, where sentiment and categorization agents execute in parallel, followed by summarization, FAISS-based RAG retrieval using local embeddings, response generation, and policy validation with conditional retry."

That is the architecture we should implement.
