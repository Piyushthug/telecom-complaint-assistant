# Telecom Customer Complaint Resolution Assistant

A zero-cost, local-first AI system for triaging and responding to telecom customer complaints using **LangGraph**, **FastAPI**, **React**, and **Gemini API**.

## 🎯 Problem

Telecom support teams handle thousands of complaints daily across multiple channels (chat, email, phone). Manual triage, categorization, and response drafting is time-consuming and inconsistent. Responses often fail to follow policy, invent unsupported claims, or escalate unnecessarily.

## ✨ Solution

An AI-powered assistant that:
- **Analyzes sentiment** and **categorizes complaints** in parallel
- **Retrieves relevant policies** using local vector search (RAG)
- **Generates policy-grounded responses** that never invent facts
- **Validates responses** against policy before returning them
- **Retries with feedback** when validation fails (up to 2x), then escalates safely
- **Detects repeated contacts** using complaint history
- **Streams progress in real-time** so users see what's happening

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         React UI (Vite)                             │
│              Live progress tracking • Beautiful results              │
└────────────────────────┬────────────────────────────────────────────┘
                         │ SSE /complaint-stream
                         │
┌────────────────────────▼────────────────────────────────────────────┐
│                    FastAPI Backend                                  │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │              LangGraph Workflow                              │  │
│  │  ┌─────────┐         ┌──────────────┐                        │  │
│  │  │ Analyze ├────┬────┤              │                        │  │
│  │  │Sentiment│    │    │ Categorize   │                        │  │
│  │  └─────────┘    │    │ (parallel)   │    ┌──────────────┐   │  │
│  │                 │    └──────────────┘    │              │   │  │
│  │                 └────────────────┬───────┤ Summarize    │   │  │
│  │                                  │       │              │   │  │
│  │                                  └──────►└──────────────┘   │  │
│  │                                          │                 │  │
│  │   ┌─────────────────────────────────────▼────────────┐   │  │
│  │   │ Check Complaint History (SQLite)                │   │  │
│  │   │ → Detect repeated contact                       │   │  │
│  │   └─────────────────────────────────────┬───────────┘   │  │
│  │                                          │               │  │
│  │   ┌─────────────────────────────────────▼────────────┐   │  │
│  │   │ RAG: Retrieve Policies (FAISS)                  │   │  │
│  │   │ → Top-K chunks from knowledge base              │   │  │
│  │   └─────────────────────────────────────┬───────────┘   │  │
│  │                                          │               │  │
│  │   ┌─────────────────────────────────────▼────────────┐   │  │
│  │   │ Generate Response (Gemini LLM)                  │   │  │
│  │   │ → Grounded strictly in retrieved policies       │   │  │
│  │   └─────────────────────────────────────┬───────────┘   │  │
│  │                                          │               │  │
│  │   ┌─────────────────────────────────────▼────────────┐   │  │
│  │   │ Validate Response                               │   │  │
│  │   │ ├─ PASS → Return result                         │   │  │
│  │   │ ├─ FAIL → Regenerate (max 2 retries)            │   │  │
│  │   │ └─ FAIL after retries → Safe escalation         │   │  │
│  │   └─────────────────────────────────────────────────┘   │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                               │  │
│  Components:                                                 │  │
│  • LLM: ChatGoogleGenerativeAI (Gemini 3.5 Flash)          │  │
│  • Embeddings: all-MiniLM-L6-v2 (384-dim)                  │  │
│  • Vector DB: FAISS (local, ~150 MB)                       │  │
│  • DB: SQLite (complaint history)                          │  │
│  • Logging: Standard Python logging                        │  │
│                                                               │  │
│  Progress tracking: Thread-safe queue emits events as nodes  │  │
│  complete, streamed to frontend via SSE                     │  │
└──────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────┐
│     Local Knowledge Base (FAISS)     │
│  • Internet Outage Policy            │
│  • Slow Internet SOP                 │
│  • Billing Complaint Policy          │
│  • Refund Policy                     │
│  • Escalation Policy                 │
└──────────────────────────────────────┘

┌──────────────────────────────────────┐
│    Complaint History (SQLite)        │
│  200+ synthetic complaints with:     │
│  • Category, status, resolution time │
│  → Used for repeated-contact detect  │
└──────────────────────────────────────┘
```

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- Node.js 16+
- Google API key (free Gemini access at https://aistudio.google.com/apikey)
- ~2 GB disk (models + dependencies)

### Setup (5 minutes)

1. **Clone and navigate:**
   ```bash
   cd telecom-complaint-assistant
   ```

2. **Set up Python backend:**
   ```bash
   python -m venv .venv
   .venv\Scripts\Activate.ps1  # or source .venv/bin/activate on macOS/Linux
   pip install -r requirements.txt
   ```

3. **Configure environment:**
   ```bash
   cp .env.example .env
   # Edit .env and add your GOOGLE_API_KEY
   ```

4. **Build local artifacts (one-time):**
   ```bash
   python scripts/build_faiss_index.py       # Embed knowledge base
   python scripts/init_db.py                 # Load complaint history
   python scripts/test_retrieval.py          # Verify RAG works
   ```

5. **Set up React frontend:**
   ```bash
   cd frontend
   npm install
   ```

6. **Run the full stack** (two terminals):

   **Terminal 1** — Backend:
   ```bash
   python -m uvicorn backend.main:app --reload
   ```

   **Terminal 2** — Frontend:
   ```bash
   cd frontend
   npm run dev
   ```

7. **Open the UI:**
   Visit `http://127.0.0.1:5173` in your browser

---

## 📊 Core Features

### 1. Parallel Sentiment + Categorization
- Both agents analyze the complaint independently
- Results fan in to summarization, reducing latency
- Interview-level talking point: "Sentiment and categorization are independent, so they run in parallel"

### 2. Policy-Grounded RAG
- Queries are embedded with `all-MiniLM-L6-v2`
- Top-3 chunks retrieved from a 23-chunk FAISS index
- Response agent **must** ground all claims in retrieved context
- No invented refunds, technician visits, or timelines

### 3. Validation + Conditional Retry
- Validator checks: Does it address the complaint? Is it grounded in policy? No unsupported promises?
- On FAIL: regenerate response with failure reason fed back
- After 2 retries: return safe fallback and `validation_status: ESCALATED`
- Prevents infinite loops

### 4. Real-Time Progress Streaming
- Backend emits `ProgressEvent` as each LangGraph node completes
- Frontend subscribes via Server-Sent Events (`/complaint-stream`)
- Users see "Analyzing sentiment..." → "Categorizing complaint..." → etc.
- Animated spinners, color-coded status (active/completed)

### 5. Repeated-Contact Detection
- Queries SQLite for prior complaints from same customer in same category
- Sets `repeated_contact: true` if threshold met (≥2 priors)
- **Does NOT alone determine escalation** — combined with sentiment, category, policy

---

## 📝 Example Requests

All examples assume the UI is running at `http://127.0.0.1:5173`. Alternatively, use `curl`:

### Internet Outage (Repeated Contact + Escalation)
```bash
curl -X POST http://127.0.0.1:8000/complaint \
  -H "Content-Type: application/json" \
  -d '{
    "customer_id": "CUST0025",
    "complaint": "My internet has been down since yesterday. I already contacted support twice but nobody fixed it."
  }'
```

**Expected:**
- `category: INTERNET_OUTAGE`
- `sentiment: VERY_NEGATIVE`
- `repeated_contact: true` (CUST0025 has 2 prior complaints)
- Policy sources: `Internet Outage Complaint Policy.md`, `Customer Complaint Escalation Policy.md`
- May escalate if validator rejects first draft multiple times

### Slow Internet (Happy Path)
```bash
curl -X POST http://127.0.0.1:8000/complaint \
  -H "Content-Type: application/json" \
  -d '{
    "customer_id": "CUST0036",
    "complaint": "My internet is working but very slow since this morning."
  }'
```

**Expected:**
- `category: SLOW_INTERNET`
- `sentiment: NEGATIVE`
- Policy sources: `Slow Internet Troubleshooting SOP.md`
- `validation_status: PASS` (usually passes on first draft)

### Billing Dispute
```bash
curl -X POST http://127.0.0.1:8000/complaint \
  -H "Content-Type: application/json" \
  -d '{
    "customer_id": "CUST0015",
    "complaint": "I was charged twice for the same service this month. Can you please fix my bill?"
  }'
```

**Expected:**
- `category: BILLING`
- Policy sources: `Billing Complaint Policy.md`

### Unsupported Request (Will Escalate)
```bash
curl -X POST http://127.0.0.1:8000/complaint \
  -H "Content-Type: application/json" \
  -d '{
    "customer_id": "CUST0099",
    "complaint": "Can you upgrade my plan to include international roaming in Japan?"
  }'
```

**Expected:**
- No policy covers international roaming
- `validation_status: ESCALATED` (after retries exhaust)
- Safe fallback response

---

## 🗂️ Project Structure

```
telecom-complaint-assistant/
├── backend/
│   ├── config.py                 # Env-driven settings (model, keys, TOP_K, MAX_RETRIES)
│   ├── main.py                   # FastAPI app (POST /complaint, POST /complaint-stream, GET /health)
│   ├── llm/
│   │   └── llm_client.py        # ChatGoogleGenerativeAI wrapper
│   ├── rag/
│   │   ├── document_loader.py   # Load .md from knowledge_base/
│   │   ├── chunker.py           # Split into overlapping chunks
│   │   ├── embeddings.py        # Sentence Transformers wrapper
│   │   ├── faiss_store.py       # Build/save/load FAISS index + search
│   │   └── retriever.py         # High-level retrieve(query) API
│   ├── db/
│   │   └── database.py          # SQLite complaint history queries
│   ├── graph/
│   │   ├── state.py             # ComplaintState TypedDict (shared across agents)
│   │   ├── progress.py          # ProgressTracker (thread-safe queue)
│   │   └── workflow.py          # LangGraph: node definitions + conditional routing
│   ├── agents/
│   │   ├── sentiment_agent.py   # Outputs: sentiment, sentiment_confidence
│   │   ├── categorization_agent.py  # Outputs: category, category_confidence
│   │   ├── summarization_agent.py   # Outputs: summary
│   │   ├── history_agent.py     # Outputs: repeated_contact, previous_complaint_count
│   │   ├── response_agent.py    # Outputs: suggested_response
│   │   └── validator_agent.py   # Outputs: validation_status, validation_reason, retry_count
│   └── utils/
│       ├── logging_config.py    # Standard Python logging
│       └── parsing.py           # extract_json() helper
│
├── frontend/
│   ├── package.json
│   ├── vite.config.js
│   ├── index.html
│   ├── src/
│   │   ├── main.jsx
│   │   ├── styles.css          # Gradient background, responsive grid
│   │   ├── App.jsx             # Main: form + progress + results
│   │   └── components/
│   │       ├── ComplaintForm.jsx     # Customer ID + complaint textarea
│   │       ├── ProgressTracker.jsx   # Live step visualization
│   │       └── ResultsDisplay.jsx    # Results grid + policy sources
│   └── .gitignore
│
├── knowledge_base/             # 5 .md policy documents
│   ├── Internet Outage Complaint Policy.md
│   ├── Slow Internet Troubleshooting SOP.md
│   ├── Billing Complaint Policy.md
│   ├── Customer Refund Policy.md
│   └── Customer Complaint Escalation Policy.md
│
├── data/
│   ├── complaints.json         # 200+ synthetic complaints (metadata)
│   ├── complaint_history.csv   # 200+ complaint history (for SQLite)
│   └── complaint_history.db    # Generated by init_db.py
│
├── scripts/
│   ├── generate_synthetic_data.py  # (already run; generates complaints.json + .csv)
│   ├── build_faiss_index.py        # Load docs → chunk → embed → FAISS index
│   ├── test_retrieval.py           # Sanity-check RAG (5 sample queries)
│   └── init_db.py                  # Load complaint_history.csv into SQLite
│
├── backend/rag/index/          # Generated by build_faiss_index.py
│   ├── index.faiss             # FAISS index (binary)
│   └── metadata.json           # Chunk metadata
│
├── requirements.txt            # Python dependencies
├── .env.example                # Template for secrets
├── .env                        # Actual secrets (gitignored)
├── .gitignore
├── RUNNING.md                  # Setup + usage guide
├── README.md                   # This file
└── telecom_complaint_assistant_execution_plan.md  # 25-phase design doc
```

---

## 🔄 Workflow Steps (in order)

1. **analyze_sentiment** (parallel)
   - Input: `complaint`
   - Output: `sentiment`, `sentiment_confidence`
   - Uses: Gemini LLM with controlled labels

2. **categorization** (parallel)
   - Input: `complaint`
   - Output: `category`, `category_confidence`
   - Uses: Fixed category list (INTERNET_OUTAGE, SLOW_INTERNET, BILLING, REFUND, CUSTOMER_SERVICE)

3. **summarize** (fan-in point)
   - Input: `complaint`, `sentiment`, `category`
   - Output: `summary`

4. **check_history**
   - Input: `customer_id`, `category`
   - Output: `repeated_contact`, `previous_complaint_count`
   - Uses: SQLite query

5. **rag_retrieve**
   - Input: `category`, `complaint`
   - Output: `retrieved_documents` (3 policy chunks with scores)
   - Uses: FAISS index + embeddings

6. **generate_response**
   - Input: `complaint`, `category`, `sentiment`, `summary`, `repeated_contact`, `previous_complaint_count`, `retrieved_documents`
   - Output: `suggested_response`
   - Uses: Gemini LLM (strictly grounded in retrieved policies)
   - On retry: includes feedback from prior validator rejection

7. **validate**
   - Input: `complaint`, `suggested_response`, `retrieved_documents`
   - Output: `validation_status` (PASS/FAIL), `validation_reason`, `retry_count`
   - Uses: Gemini LLM (strict compliance check)
   - Increments `retry_count` on FAIL

8. **Conditional routing** (after validate)
   - If `validation_status == PASS`: → END (return result)
   - If `retry_count >= MAX_RETRIES`: → escalate
   - Else: → generate_response (loop)

9. **escalate**
   - Output: safe fallback response, `validation_status: ESCALATED`, `escalated: true`

---

## 💡 Interview Talking Points

1. **"Explain your architecture in one sentence"**
   > "I built a zero-cost local telecom complaint resolution assistant using FastAPI and LangGraph, where sentiment and categorization agents execute in parallel, followed by summarization, FAISS-based RAG retrieval using local embeddings, response generation, and policy validation with conditional retry."

2. **"How do you avoid inventing facts?"**
   > "The response agent receives the complaint, customer context, and **only** the top-K retrieved policy chunks. The prompt explicitly forbids inventing refunds, ticket numbers, or timelines unless they appear in the policy. Then a separate validator checks every claim is grounded in policy; if not, it feeds the failure reason back to regenerate with the correction."

3. **"How do you scale this?"**
   > "The local embeddings and FAISS index are already fast (< 200ms per query). The LLM calls are the bottleneck; we could cache responses, batch requests, or switch to a faster model. SQLite works fine for complaint history; if we need true scale, switch to PostgreSQL. The LangGraph workflow runs synchronously; async support is built-in (we use `asyncio.to_thread` in the FastAPI handler)."

4. **"Why SSE and not WebSocket?"**
   > "SSE is simpler for one-way streaming (progress updates). WebSocket would add bidirectional complexity we don't need. SSE integrates cleanly with FastAPI (`StreamingResponse`), and the frontend just opens an `EventSource` connection. If we needed real-time user input to affect the workflow mid-run, we'd upgrade to WebSocket."

5. **"How do you handle validation failures?"**
   > "Retry is built into the workflow. If the validator rejects a response, we feed the failure reason back to the response agent and regenerate. We cap retries at `MAX_RETRIES` (default 2) to prevent loops. If it still fails, we return a safe fallback ('I'm escalating this to a human') and set `escalated: true`. The user knows they didn't get a confident answer."

6. **"How do you detect repeated contacts?"**
   > "After categorization, we query SQLite for prior complaints from the same customer in the same category. If count ≥ threshold (default 2), set `repeated_contact: true`. But sentiment alone doesn't determine escalation — we combine it with category, prior complaints, and policy rules. A frustrated customer with a simple outage might not escalate; a calm customer with 5 unresolved billing issues will."

---

## 🧪 Testing

### Unit tests
```bash
# Run individual components
python scripts/test_retrieval.py    # RAG sanity check (5 queries)
```

### Integration test
```bash
# Start the full stack and send a test request via curl (see Example Requests above)
```

### E2E test (UI)
- Open `http://127.0.0.1:5173`
- Fill in Customer ID and complaint
- Click "Analyze Complaint"
- Watch progress steps update in real-time
- See final results with validation status and policy sources

---

## 📦 Dependencies

**Backend:**
- `fastapi` — async web framework
- `uvicorn` — ASGI server
- `langchain-core` — LLM abstraction
- `langchain-google-genai` — Gemini integration
- `langgraph` — agentic orchestration
- `sentence-transformers` — local embeddings
- `faiss-cpu` — vector search
- `pydantic` — request/response validation
- `python-dotenv` — env config

**Frontend:**
- `react` — component library
- `vite` — build tool
- No external UI framework (pure CSS, simple and fast)

---

## 🛠️ Configuration

Edit `.env` to customize:

```env
GOOGLE_API_KEY=your_key_here
GEMINI_MODEL=gemini-3.5-flash-lite      # Can change to newer Gemini models
GEMINI_TEMPERATURE=0.2                  # Lower = more deterministic

TOP_K=3                                 # Policy chunks to retrieve
MAX_RETRIES=2                           # Retry limit before escalation

CHUNK_SIZE=800                          # Chunk size for embedding
CHUNK_OVERLAP=120                       # Overlap between chunks
REPEATED_CONTACT_THRESHOLD=2            # Prior complaints before flagging
```

---

## 📚 Knowledge Base Format

Each `.md` file in `knowledge_base/` follows this structure:

```markdown
# Title

**Document ID:** KB-XXX-001
**Version:** 1.0
**Status:** Active

## 1. Purpose
...

## 2. Scope
...

## 3. Rules / Process
...

## 7. Prohibited Actions
...

## 8. Examples
...
```

The chunker splits on double-newlines (`\n\n`), so content is structured naturally. Each chunk retains source document name for traceability.

---

## 🐛 Troubleshooting

See [RUNNING.md](RUNNING.md) for detailed troubleshooting steps.

**Quick fixes:**
- `GOOGLE_API_KEY is not set` → Fill in `.env` (not `.env.example`)
- `FAISS index not found` → Run `python scripts/build_faiss_index.py`
- `no such table: complaint_history` → Run `python scripts/init_db.py`
- `CERTIFICATE_VERIFY_FAILED` → `pip install pip-system-certs` (corporate proxy issue)

---

## 📖 Design Philosophy

1. **Zero-cost**: No paid APIs, no cloud. Gemini free tier + local models.
2. **Local-first**: Embeddings, vector search, complaint history all local.
3. **Policy-grounded**: Never invent facts. Responses must cite policy.
4. **Transparent**: Real-time progress streaming so users see what's happening.
5. **Practical**: Handles edge cases (escalation, retries, fallbacks) without complexity.
6. **Explainable**: Every step is traceable; policy sources are shown.

---

## 📄 License

This is a learning project. Use, modify, and distribute freely.

---

## 🎓 Learning Outcomes

Building this project teaches:
- **LangGraph**: agentic workflows, parallel nodes, conditional routing
- **RAG**: embedding, chunking, vector search (FAISS)
- **LLM safety**: validation, grounding, retry logic
- **FastAPI**: async, streaming responses (SSE)
- **React**: real-time updates, form handling, responsive design
- **Telecom domain**: complaint handling, escalation rules, policy compliance

---

**Have questions?** Check [RUNNING.md](RUNNING.md) for setup and usage details.
