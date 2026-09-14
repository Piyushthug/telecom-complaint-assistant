# Telecom Complaint Assistant — Complete API & Project Documentation

## 📋 Table of Contents
1. [Project Overview](#project-overview)
2. [Architecture](#architecture)
3. [API Endpoints](#api-endpoints)
4. [Workflow Stages](#workflow-stages)
5. [Data Models](#data-models)
6. [Integration Flow](#integration-flow)
7. [Setup Instructions](#setup-instructions)
8. [Example Scenarios](#example-scenarios)

---

## 🎯 Project Overview

### Vision
Build a **zero-cost, local-first AI system** that automates telecom customer complaint resolution using intelligent routing, policy-grounded responses, and real-time validation.

### Key Features
✅ **AI-Powered Triage** — Sentiment analysis + automatic categorization  
✅ **Policy-Grounded Responses** — Never invents facts or promises  
✅ **Real-Time Progress** — Stream workflow status to UI via SSE  
✅ **Complaint Lookup** — Fetch real customer history via API  
✅ **Validation + Retry** — Regenerates responses if validation fails  
✅ **Escalation Handling** — Safe fallback when AI can't resolve  
✅ **Beautiful UI** — React frontend with live progress tracking  
✅ **Zero Cost** — Local embeddings + Gemini free tier

### Tech Stack

| Component | Technology | Purpose |
|-----------|-----------|---------|
| **Backend API** | FastAPI | REST endpoints + SSE streaming |
| **Workflow Engine** | LangGraph | Orchestrate agents, handle parallelism & routing |
| **LLM** | Google Gemini API | Sentiment, categorization, response generation, validation |
| **Embeddings** | Sentence Transformers | Local, offline embedding model (384-dim) |
| **Vector DB** | FAISS | Local vector search for policy retrieval |
| **Database** | SQLite | Complaint history + metadata |
| **Frontend** | React + Vite | Real-time UI with progress tracking |
| **Web Framework** | Uvicorn | ASGI server for FastAPI |

---

## 🏗️ Architecture

### High-Level Flow

```
User Request (Web UI)
        ↓
    FastAPI
        ↓
   LangGraph Workflow
   (parallel nodes + conditional routing)
        ↓
   [Sentiment] [Categorization] ← Run in parallel
        ↓
   Summarization
        ↓
   Complaint History Lookup (via API)
        ↓
   RAG: Policy Retrieval (FAISS)
        ↓
   Response Generation (Gemini)
        ↓
   Validation (Gemini)
   ├─ PASS → Return result
   ├─ FAIL → Retry (max 2x)
   └─ MAX_RETRIES → Escalate & return fallback
        ↓
   Stream Result + Progress Events to UI
        ↓
   Display Results (React)
```

### Component Responsibilities

#### Backend (`backend/`)
| Module | Responsibility |
|--------|-----------------|
| `main.py` | FastAPI app, HTTP endpoints, SSE streaming |
| `llm/llm_client.py` | LLM abstraction (pluggable provider) |
| `rag/` | Document loading, chunking, embedding, vector search |
| `db/database.py` | SQLite queries (no direct SQL from agents) |
| `services/complaint_service.py` | **Business logic for complaint operations** |
| `graph/workflow.py` | LangGraph node definitions + routing |
| `graph/progress.py` | Progress event tracking (thread-safe queue) |
| `agents/` | Specialized agents (sentiment, categorization, etc.) |
| `utils/` | Helpers (logging, JSON parsing) |

#### Frontend (`frontend/`)
| Component | Responsibility |
|-----------|-----------------|
| `App.jsx` | Main container, state management, SSE subscription |
| `ComplaintForm.jsx` | Input form (customer ID, complaint text) |
| `ProgressTracker.jsx` | Real-time step visualization |
| `ResultsDisplay.jsx` | Results grid + policy sources |
| `styles.css` | Responsive design, animations |

---

## 🔌 API Endpoints

### Base URL
```
http://127.0.0.1:8000
```

### 1. Health Check
```http
GET /health
```

**Response (200 OK):**
```json
{
  "status": "ok"
}
```

---

### 2. Submit Complaint (Blocking)
```http
POST /complaint
Content-Type: application/json
```

**Request:**
```json
{
  "customer_id": "CUST0025",
  "complaint": "My internet has been down since yesterday."
}
```

**Response (200 OK):**
```json
{
  "request_id": "550e8400-e29b-41d4-a716-446655440000",
  "category": "INTERNET_OUTAGE",
  "sentiment": "VERY_NEGATIVE",
  "sentiment_confidence": 0.98,
  "summary": "Customer reports internet outage for 24+ hours...",
  "response": "I'm very sorry to hear your internet is down...",
  "validation_status": "PASS",
  "validation_reason": "Response addresses issue and follows policy",
  "repeated_contact": true,
  "previous_complaint_count": 2,
  "escalated": false,
  "policy_sources": [
    {
      "document": "Internet Outage Complaint Policy.md",
      "chunk_text": "...",
      "similarity_score": 0.62
    }
  ]
}
```

**Response Status Codes:**
- `200 OK` — Complaint processed successfully
- `500 Internal Server Error` — Workflow execution failed

---

### 3. Submit Complaint with Progress Streaming (SSE)
```http
POST /complaint-stream
Content-Type: application/json
```

**Request:** (Same as `/complaint`)
```json
{
  "customer_id": "CUST0025",
  "complaint": "My internet has been down..."
}
```

**Response (200 OK):**
```
Transfer-Encoding: chunked
Content-Type: text/event-stream

data: {"type":"progress","step":"analyze_sentiment","status":"started","message":"Analyzing sentiment..."}

data: {"type":"progress","step":"analyze_sentiment","status":"completed","message":"Analyzing sentiment complete"}

data: {"type":"progress","step":"categorization","status":"started","message":"Categorizing complaint..."}

data: {"type":"progress","step":"categorization","status":"completed","message":"Categorizing complaint complete"}

...

data: {"type":"result","data":{...full result object...}}
```

**Event Types:**
- `progress` — Workflow node started/completed
- `result` — Final result (complaintResponse)
- `error` — Error occurred

---

### 4. Get Customer Complaints
```http
GET /complaints/{customer_id}
```

**Path Parameters:**
- `customer_id` (string) — e.g., `CUST0025`

**Response (200 OK):**
```json
{
  "customer_id": "CUST0025",
  "complaint_count": 2,
  "complaints": [
    {
      "complaint_id": "CMP0008",
      "category": "INTERNET_OUTAGE",
      "status": "OPEN",
      "created_at": "2026-07-24T23:27:32",
      "resolution_time_hours": null
    },
    {
      "complaint_id": "CMP0063",
      "category": "INTERNET_OUTAGE",
      "status": "ESCALATED",
      "created_at": "2026-05-04T02:01:32",
      "resolution_time_hours": null
    }
  ]
}
```

**Used by:** Response agent to provide accurate status updates when customer asks for complaint history.

---

### 5. Get Recent Complaint
```http
GET /complaints/{customer_id}/recent
```

**Path Parameters:**
- `customer_id` (string) — e.g., `CUST0070`

**Response (200 OK):**
```json
{
  "complaint_id": "CMP0025",
  "category": "SLOW_INTERNET",
  "status": "ESCALATED",
  "created_at": "2026-08-03T04:56:32"
}
```

**Response (when no complaints found):**
```json
{
  "error": "No complaints found for customer CUST0099"
}
```

---

### 6. Interactive API Docs
```http
GET /docs
```

**Opens:** Swagger UI for interactive endpoint testing

---

## 🔄 Workflow Stages

### Stage 1: Parallel Analysis
```
INPUT: complaint text
↓
[analyze_sentiment] ──┐
                      ├──→ Merged state
[categorization] ─────┘

OUTPUT: sentiment, sentiment_confidence, category, category_confidence
TIME: ~2-3 seconds per agent (parallel = ~3 seconds total)
```

**Agents:**
- `sentiment_agent.py` — Classifies into POSITIVE, NEUTRAL, NEGATIVE, VERY_NEGATIVE
- `categorization_agent.py` — Classifies into INTERNET_OUTAGE, SLOW_INTERNET, BILLING, REFUND, CUSTOMER_SERVICE

---

### Stage 2: Summarization
```
INPUT: complaint, sentiment, category
↓
summarization_agent
↓
OUTPUT: summary (1-3 sentence recap)
TIME: ~2 seconds
```

---

### Stage 3: History & Context
```
INPUT: customer_id, category
↓
check_history_agent (queries SQLite)
↓
OUTPUT: repeated_contact (bool), previous_complaint_count (int)
TIME: ~100ms
```

**Used for escalation signals:**
- Repeated contact = customer has complained ≥2 times in same category
- Not alone sufficient for escalation; combined with sentiment, category, policy

---

### Stage 4: Policy Retrieval (RAG)
```
INPUT: category, complaint
↓
1. Embed query → 384-dim vector
2. FAISS search (top-3 chunks)
3. Return with similarity scores
↓
OUTPUT: retrieved_documents (3 policy chunks)
TIME: ~800ms
```

**Search Process:**
```
Query: "My internet is completely down."
         ↓ (embedded)
     [Vector]
         ↓ (FAISS search)
   Top-3 chunks from index
   ├─ Internet Outage Policy (0.62 similarity)
   ├─ Slow Internet SOP (0.55)
   └─ Escalation Policy (0.48)
```

---

### Stage 5: Response Generation
```
INPUT: complaint, category, sentiment, summary, 
       repeated_contact, previous_complaint_count,
       retrieved_documents
↓
response_agent (calls Gemini LLM)
   ├─ Detects if customer asking for complaint status
   ├─ If yes: Calls /complaints/{customer_id} API
   └─ Includes real complaint history in prompt
↓
OUTPUT: suggested_response (grounded in policy)
TIME: ~3-4 seconds
```

**Critical Constraints:**
- ❌ Cannot invent refunds, ticket numbers, technician visits, outage causes, resolution times, compensation
- ✅ Can only claim what retrieved policies explicitly support
- ✅ Can reference complaint history fetched from API
- ✅ Should acknowledge frustration before providing next steps

---

### Stage 6: Validation
```
INPUT: complaint, suggested_response, retrieved_documents
↓
validator_agent (calls Gemini LLM)
   ├─ Checks: addresses complaint?
   ├─ Checks: grounded in policy?
   ├─ Checks: no unsupported promises?
   └─ Checks: no invented facts?
↓
OUTPUT: validation_status (PASS/FAIL), validation_reason
TIME: ~2-3 seconds
```

**Routing:**
```
validation_status
├─ PASS (60-70% typical)
│  └─ Return result + END
├─ FAIL (20-30% typical)
│  └─ retry_count++
│     if retry_count < MAX_RETRIES:
│        → regenerate_response (with failure reason)
│     else:
│        → escalate
└─ ESCALATED
   └─ Return safe fallback
```

---

### Stage 7: Escalation (if needed)
```
INPUT: retry_count >= MAX_RETRIES
↓
escalate_node
   ├─ Generate safe fallback response
   ├─ Set validation_status = "ESCALATED"
   ├─ Set escalated = true
   └─ Log policy sources for human review
↓
OUTPUT: Safe fallback response
```

**Safe Fallback:**
```
"Thank you for reaching out, and I'm sorry for the ongoing trouble. 
I wasn't able to confidently confirm a resolution for this from our current 
policy information, so I'm escalating this complaint to a human support 
representative who can review your account and take the next steps."
```

---

## 📊 Data Models

### ComplaintState (LangGraph)
```python
class ComplaintState(TypedDict):
    # Input
    complaint: str
    customer_id: str
    
    # Analysis output
    sentiment: str  # POSITIVE, NEUTRAL, NEGATIVE, VERY_NEGATIVE
    sentiment_confidence: float
    category: str  # INTERNET_OUTAGE, SLOW_INTERNET, BILLING, REFUND, CUSTOMER_SERVICE
    category_confidence: float
    
    # Summarization
    summary: str
    
    # Context
    retrieved_documents: List[Dict]
    repeated_contact: bool
    previous_complaint_count: int
    
    # Response & validation
    suggested_response: str
    validation_status: str  # PASS, FAIL, ESCALATED
    validation_reason: str
    retry_count: int
    escalated: bool
```

### ComplaintResponse (API)
```python
class PolicySource(BaseModel):
    document: str
    chunk_text: str
    similarity_score: float

class ComplaintResponse(BaseModel):
    request_id: str
    category: str
    sentiment: str
    summary: str
    response: str
    validation_status: str
    validation_reason: str
    repeated_contact: bool
    escalated: bool
    policy_sources: List[PolicySource]
```

### ProgressEvent
```python
@dataclass
class ProgressEvent:
    step: str  # analyze_sentiment, categorization, summarize, etc.
    status: str  # started, completed
    message: str  # "Analyzing sentiment...", "Retrieved 3 policy excerpts"
    timestamp: float
```

### Complaint (from DB)
```json
{
  "complaint_id": "CMP0008",
  "customer_id": "CUST0025",
  "category": "INTERNET_OUTAGE",
  "status": "OPEN",
  "created_at": "2026-07-24T23:27:32",
  "resolution_time_hours": null
}
```

---

## 🔗 Integration Flow

### Frontend → Backend Flow

```mermaid
User Submits Form
    ↓
React App (App.jsx)
    ↓
POST /complaint-stream (with SSE EventSource)
    ↓
FastAPI: resolve_complaint_stream()
    ├─ Create ProgressTracker
    ├─ Set global tracker (workflow can emit events)
    ├─ Invoke LangGraph in thread pool
    └─ Stream events + result to frontend
    ↓
LangGraph Workflow
    ├─ Each node calls record_progress()
    ├─ Events added to tracker queue
    └─ Main thread reads queue → streams SSE events
    ↓
React: EventSource listener
    ├─ Receives progress events → updates ProgressTracker
    ├─ Receives result event → displays ResultsDisplay
    └─ Receives error event → shows error message
```

### Agent → API Flow (Complaint Lookup)

```
response_agent.run(state)
    ↓
_should_lookup_complaint(complaint_text)?
    ├─ YES: Keywords found (status, complaint id, etc.)
    │  ├─ _fetch_complaint_history(customer_id)
    │  │  └─ requests.get("http://127.0.0.1:8000/complaints/{customer_id}")
    │  │     ↓ (FastAPI endpoint)
    │  │  ├─ complaint_service.get_customer_complaints()
    │  │  │  └─ database.get_customer_history(customer_id)
    │  │  │     └─ SQLite query
    │  │  └─ Returns: {customer_id, complaint_count, complaints}
    │  │
    │  └─ _format_complaint_history() → readable string
    │
    └─ NO: Normal response path
        ↓
    Include complaint history in LLM prompt (if found)
    ↓
    Gemini LLM generates response with real data
```

---

## 🚀 Setup Instructions

### Prerequisites
```
Python 3.11+
Node.js 16+
Google API Key (free at https://aistudio.google.com/apikey)
~2 GB disk space
```

### Step 1: Backend Setup
```bash
cd telecom-complaint-assistant
python -m venv .venv
.venv\Scripts\Activate.ps1  # Windows PowerShell
# OR
source .venv/bin/activate  # macOS/Linux

pip install -r requirements.txt
```

### Step 2: Configure Secrets
```bash
cp .env.example .env
# Edit .env and add GOOGLE_API_KEY
```

### Step 3: Build Local Artifacts
```bash
python scripts/build_faiss_index.py    # ~30 seconds
python scripts/init_db.py              # ~1 second
python scripts/test_retrieval.py       # Verify RAG works
```

### Step 4: Frontend Setup
```bash
cd frontend
npm install
```

### Step 5: Run Full Stack

**Terminal 1 (Backend):**
```bash
python -m uvicorn backend.main:app --reload
# Opens at http://127.0.0.1:8000
```

**Terminal 2 (Frontend):**
```bash
cd frontend
npm run dev
# Opens at http://127.0.0.1:5173
```

### Step 6: Access UI
```
http://127.0.0.1:5173
```

---

## 📋 Example Scenarios

### Scenario 1: Internet Outage with Repeated Contact

**Request:**
```json
{
  "customer_id": "CUST0025",
  "complaint": "My internet has been down since yesterday. I already contacted support twice but nobody fixed it."
}
```

**Expected Flow:**
```
analyze_sentiment → VERY_NEGATIVE (0.98)
categorization → INTERNET_OUTAGE (0.99)
summarize → "Customer reports unresolved 24-hour outage, has contacted support twice"
check_history → repeated_contact=true, previous_complaint_count=2
rag_retrieve → [Internet Outage Policy, Escalation Policy, ...]
generate_response → "I understand this is frustrating. Since you've contacted us multiple times..."
validate → Likely PASS (policy supports acknowledgment + escalation info)
```

**Response:**
```json
{
  "category": "INTERNET_OUTAGE",
  "sentiment": "VERY_NEGATIVE",
  "validation_status": "PASS",
  "repeated_contact": true,
  "escalated": false,
  "policy_sources": [
    {"document": "Internet Outage Complaint Policy.md", "similarity_score": 0.62},
    {"document": "Customer Complaint Escalation Policy.md", "similarity_score": 0.59}
  ]
}
```

---

### Scenario 2: Billing Dispute with Complaint Lookup

**Request:**
```json
{
  "customer_id": "CUST0015",
  "complaint": "I was charged twice for the same service. What's the status of my complaint CMP0004?"
}
```

**Expected Flow:**
```
analyze_sentiment → NEGATIVE (0.95)
categorization → BILLING (0.98)
summarize → "Duplicate charge complaint + request for status on CMP0004"
check_history → repeated_contact=true, previous_complaint_count=2
rag_retrieve → [Billing Complaint Policy, Refund Policy, ...]
generate_response:
  ├─ _should_lookup_complaint() → YES (found "status of my complaint")
  ├─ _fetch_complaint_history("CUST0015")
  │  └─ API returns: complaints=[{CMP0004, status: IN_PROGRESS}, ...]
  ├─ _format_complaint_history() → "Your complaint CMP0004: BILLING (IN_PROGRESS) - 2026-07-03"
  └─ Includes history in LLM prompt
validate → PASS (response grounds claims in policy + real complaint data)
```

**Response:**
```json
{
  "category": "BILLING",
  "sentiment": "NEGATIVE",
  "response": "Thank you for reaching out. I can see your complaint CMP0004 is currently in progress. Our team is reviewing the duplicate charge on your account...",
  "validation_status": "PASS",
  "policy_sources": [
    {"document": "Billing Complaint Policy.md", "similarity_score": 0.68}
  ]
}
```

---

### Scenario 3: Unsupported Request (Escalation)

**Request:**
```json
{
  "customer_id": "CUST0099",
  "complaint": "Can you upgrade my plan to include international roaming in Japan?"
}
```

**Expected Flow:**
```
analyze_sentiment → NEUTRAL (0.75)
categorization → CUSTOMER_SERVICE (0.82)
summarize → "Request for plan upgrade to Japan international roaming"
check_history → repeated_contact=false, previous_complaint_count=0
rag_retrieve → [low-relevance chunks, no international roaming policy]
generate_response → Attempts response but lacks grounding
validate → FAIL ("Response doesn't cite policy for roaming eligibility")
retry_count=1 → regenerate_response (with failure feedback)
generate_response (attempt 2) → Still can't ground properly
validate → FAIL (same reason)
retry_count=2 → MAX_RETRIES reached
escalate → Return safe fallback
```

**Response:**
```json
{
  "category": "CUSTOMER_SERVICE",
  "sentiment": "NEUTRAL",
  "response": "Thank you for reaching out, and I'm sorry for the ongoing trouble. I wasn't able to confidently confirm a resolution for this from our current policy information, so I'm escalating this complaint to a human support representative who can review your account and take the next steps.",
  "validation_status": "ESCALATED",
  "escalated": true,
  "policy_sources": []
}
```

---

### Scenario 4: Happy Path (Slow Internet)

**Request:**
```json
{
  "customer_id": "CUST0036",
  "complaint": "My internet is working but very slow since this morning."
}
```

**Expected Flow:**
```
analyze_sentiment → NEGATIVE (0.92)
categorization → SLOW_INTERNET (0.96)
summarize → "Customer reports degraded internet performance starting this morning"
check_history → repeated_contact=false
rag_retrieve → [Slow Internet Troubleshooting SOP (0.79), ...]
generate_response → Detailed troubleshooting steps from SOP
validate → PASS ✓ (First try! All steps grounded in SOP)
```

**Response (PASS on first attempt):**
```json
{
  "category": "SLOW_INTERNET",
  "sentiment": "NEGATIVE",
  "validation_status": "PASS",
  "retry_count": 0,
  "escalated": false,
  "response": "I'm sorry your internet is running slowly. Here are some troubleshooting steps: 1. Restart your router... [etc]"
}
```

---

## 📊 Performance Metrics

| Operation | Time | Notes |
|-----------|------|-------|
| Sentiment analysis | ~2s | Gemini LLM call |
| Categorization | ~2s | Parallel with sentiment |
| Summarization | ~2s | Sequential |
| History lookup | ~100ms | SQLite query |
| Policy embedding | ~800ms | Vector search + FAISS |
| Response generation | ~3-4s | Gemini LLM call |
| Validation | ~2-3s | Gemini LLM call |
| **Total workflow** | **~12-15s** | End-to-end (can retry) |
| **SSE streaming** | Real-time | Progress events every ~1s |

---

## 🔐 Security Considerations

### ✅ What's Protected
- `.env` file with API keys is gitignored
- Agents cannot execute arbitrary SQL (only via API)
- All LLM calls constrained by policy documents
- Responses validated before returning
- No secrets logged to console

### ⚠️ What's NOT Implemented (Future)
- Customer authentication (assumes pre-auth)
- Rate limiting per customer
- PII masking in logs
- Encryption at rest for SQLite
- CORS policy configuration
- API key rotation

---

## 🎓 Key Architectural Decisions

### 1. Why LangGraph?
- **Parallel execution** of independent agents (sentiment + categorization)
- **Conditional routing** (validation → retry or escalate)
- **Type-safe state** across nodes (TypedDict)
- **Easy to test** each node independently

### 2. Why SSE instead of WebSocket?
- One-way streaming (perfect for progress updates)
- Simpler client (EventSource API)
- No server-side connection management
- Works over HTTP/HTTPS

### 3. Why SQLite instead of PostgreSQL?
- Zero setup, zero operations
- Sufficient for complaint history (200+ records)
- Scales to millions of rows
- Easier to deploy locally

### 4. Why Local Embeddings (Sentence Transformers)?
- No API calls for every embedding
- Fast (~100ms per query)
- Cached after first run
- ~384 MB disk (small model, good quality)

### 5. Why Gemini Free Tier?
- $0 cost (project requirement)
- Sufficient latency for customer support (3-4 seconds acceptable)
- Easy to swap for Gemini Pro later (same API)
- No request batching needed

---

## 📚 API Usage Examples

### cURL Examples

**Submit complaint (blocking):**
```bash
curl -X POST http://127.0.0.1:8000/complaint \
  -H "Content-Type: application/json" \
  -d '{"customer_id":"CUST0025","complaint":"My internet is down"}'
```

**Submit complaint (streaming):**
```bash
curl -N -X POST http://127.0.0.1:8000/complaint-stream \
  -H "Content-Type: application/json" \
  -d '{"customer_id":"CUST0025","complaint":"My internet is down"}'
```

**Get complaint history:**
```bash
curl http://127.0.0.1:8000/complaints/CUST0025
```

**Get recent complaint:**
```bash
curl http://127.0.0.1:8000/complaints/CUST0070/recent
```

---

### Python Examples

**Using requests:**
```python
import requests
import json

response = requests.post(
    "http://127.0.0.1:8000/complaint",
    json={
        "customer_id": "CUST0025",
        "complaint": "My internet has been down since yesterday."
    }
)
result = response.json()
print(json.dumps(result, indent=2))
```

**Using SSE (streaming):**
```python
import requests
import json

response = requests.post(
    "http://127.0.0.1:8000/complaint-stream",
    json={"customer_id": "CUST0025", "complaint": "..."},
    stream=True
)

for line in response.iter_lines():
    if line:
        data = json.loads(line[6:])  # Remove "data: " prefix
        print(f"Event: {data['type']}")
        if data['type'] == 'progress':
            print(f"  {data['step']}: {data['message']}")
        elif data['type'] == 'result':
            print(f"  Final response: {data['data']['response']}")
```

---

## 🚨 Troubleshooting

### Backend won't start
```bash
# Check if port 8000 is in use
netstat -ano | findstr :8000

# Kill process using port 8000 (Windows)
taskkill /PID <PID> /F
```

### FAISS index not found
```bash
python scripts/build_faiss_index.py
```

### Complaints table doesn't exist
```bash
python scripts/init_db.py
```

### Gemini API calls failing
```bash
# Check .env has valid GOOGLE_API_KEY
echo $GOOGLE_API_KEY  # Should print your key

# Test directly
python -c "from backend.llm import llm_client; print(llm_client.generate('Test'))"
```

### Frontend can't reach backend
```bash
# Verify backend is running on port 8000
curl http://127.0.0.1:8000/health

# Check vite.config.js proxy settings
# Should proxy /api/ to http://127.0.0.1:8000
```

---

## 📝 Summary

This system demonstrates:
- ✅ **LangGraph** for orchestrating AI agents with parallelism & conditional logic
- ✅ **RAG** with local embeddings and FAISS for policy grounding
- ✅ **FastAPI** for async HTTP + SSE streaming
- ✅ **Real-time UI** showing workflow progress in React
- ✅ **Safe escalation** when AI can't confidently resolve
- ✅ **Zero-cost** operation (local + free Gemini tier)
- ✅ **API-driven** architecture (no direct SQL from agents)

**Perfect for:** Telecom support automation, complaint triage, policy-grounded AI responses.

---

**For questions, see [RUNNING.md](RUNNING.md) and [README.md](README.md)**
