# Running the Telecom Complaint Resolution Assistant (Backend)

This covers environment setup, one-time data preparation, starting the API,
and example requests for each use case the workflow is designed to handle.

---

## 1. Prerequisites

- Python 3.11+ (tested with 3.13)
- A Google API key with access to the Gemini API (free tier is fine)
  - Get one at https://aistudio.google.com/apikey

No local LLM, no paid infra, no internet access required at request time
except for calling the Gemini API.

---

## 2. Set up the environment

From the project root (`telecom-complaint-assistant/`):

```bash
python -m venv .venv
```

Activate it:

```powershell
# PowerShell
.\.venv\Scripts\Activate.ps1
```

```bash
# macOS / Linux
source .venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

> If you're behind a corporate SSL-inspecting proxy and package installs or
> model downloads fail with `CERTIFICATE_VERIFY_FAILED`, install
> `pip-system-certs` (`pip install pip-system-certs`) so Python trusts the
> same certificates as your OS/browser.

---

## 3. Configure secrets

Copy the example env file and fill in your key:

```bash
cp .env.example .env
```

Edit `.env`:

```env
GOOGLE_API_KEY=your_real_key_here
GEMINI_MODEL=gemini-3.5-flash-lite
GEMINI_TEMPERATURE=0.2

TOP_K=3
MAX_RETRIES=2
```

`.env` is gitignored — never commit real keys.

---

## 4. One-time data preparation

These build local artifacts from `knowledge_base/` and `data/`. Re-run them
whenever those source files change.

**Build the FAISS index** (embeds the knowledge base with
`all-MiniLM-L6-v2` and saves it to `backend/rag/index/`):

```bash
python scripts/build_faiss_index.py
```

**Sanity-check retrieval** (optional but recommended — confirms each sample
query surfaces the expected policy document):

```bash
python scripts/test_retrieval.py
```

**Load complaint history into SQLite** (used for repeated-contact
detection, from `data/complaint_history.csv` into `data/complaint_history.db`):

```bash
python scripts/init_db.py
```

---

## 5. Install and run the frontend (React + Vite)

From the `frontend/` directory:

```bash
cd frontend
npm install
npm run dev
```

The UI is now live at `http://127.0.0.1:5173`. The vite config proxies
`/api/*` requests to the backend at `127.0.0.1:8000`.

---

## 6. Run the API (backend)

From the project root:

```bash
python -m uvicorn backend.main:app --reload
```

The API is now live at `http://127.0.0.1:8000`.

- `GET /health` — liveness check
- `POST /complaint` — runs the full LangGraph workflow (blocking, returns full result)
- `POST /complaint-stream` — streams progress events + final result via SSE (used by the React UI)
- `GET /docs` — interactive Swagger UI (FastAPI auto-generated)

### Request format

```json
{
  "customer_id": "CUST0025",
  "complaint": "My internet has been down since yesterday."
}
```

### Response format

```json
{
  "request_id": "...",
  "category": "INTERNET_OUTAGE",
  "sentiment": "VERY_NEGATIVE",
  "summary": "...",
  "response": "...",
  "validation_status": "PASS | FAIL | ESCALATED",
  "validation_reason": "...",
  "repeated_contact": true,
  "escalated": false,
  "policy_sources": [
    { "document": "...", "chunk_text": "...", "similarity_score": 0.62 }
  ]
}
```

---

## 7. Full-stack setup (run both backend and frontend)

**Terminal 1** — Backend:
```bash
python -m uvicorn backend.main:app --reload
```

**Terminal 2** — Frontend:
```bash
cd frontend
npm run dev
```

Then visit `http://127.0.0.1:5173` in your browser.

---

## 8. Workflow behind each request

```
START
  |
  +--> analyze_sentiment  --\
  +--> categorization     ---+--> summarize --> check_history --> rag_retrieve
                                                                        |
                                                                        v
                                                              generate_response
                                                                        |
                                                                        v
                                                                    validate
                                                             /        |        \
                                                          PASS     retry     max retries
                                                           |          |          |
                                                          END   generate_response  escalate --> END
                                                                    (loops back to validate)
```

- `analyze_sentiment` and `categorization` run in parallel (independent of
  each other) and fan in to `summarize`.
- `check_history` queries SQLite for prior complaints from the same
  customer in the same category → sets `repeated_contact`.
- `rag_retrieve` pulls the top-`K` relevant chunks from the knowledge base.
- `generate_response` is grounded strictly in the retrieved chunks — it
  must not invent refunds, ticket numbers, technician visits, outage
  causes, resolution times, or compensation.
- `validate` checks the draft against the complaint and retrieved policy.
  On `FAIL`, it loops back to `generate_response` (passing the failure
  reason so the next draft can correct it), up to `MAX_RETRIES` (default 2).
  If it still fails after that, the workflow returns a safe fallback
  response and `validation_status: "ESCALATED"`.

---

## 9. Frontend features

The React UI displays real-time progress of the workflow using Server-Sent Events:

- **Live step tracking** — Watch each agent run (sentiment analysis, categorization,
  summarization, history check, RAG retrieval, response generation, validation).
- **Intermediate messages** — See what each step is doing as it executes (e.g.,
  "Retrieving relevant policies..." becomes "Retrieved 3 policy excerpts").
- **Final results** — Once complete, displays:
  - Complaint category, sentiment, and summary
  - AI-generated response grounded in policy
  - Validation status (PASS / FAIL / ESCALATED)
  - Policy sources with relevance scores
  - Repeated-contact flag and validation details
- **Beautiful design** — Gradient background, responsive grid layout, animated
  spinners and progress indicators.

---

## 10. Example use cases

Each example below is a PowerShell one-liner; swap in `curl` if you prefer.

### Internet outage

```powershell
$body = @{ customer_id = "CUST0025"; complaint = "My internet has been down since yesterday. I already contacted support twice but nobody fixed it." } | ConvertTo-Json
Invoke-RestMethod -Uri "http://127.0.0.1:8000/complaint" -Method Post -Body $body -ContentType "application/json"
```
Expected: `category = INTERNET_OUTAGE`, policy sources drawn from
`Internet Outage Complaint Policy.md` (and likely
`Customer Complaint Escalation Policy.md` given the repeated contact).

### Slow internet

```powershell
$body = @{ customer_id = "CUST0036"; complaint = "My internet is working but very slow since this morning." } | ConvertTo-Json
Invoke-RestMethod -Uri "http://127.0.0.1:8000/complaint" -Method Post -Body $body -ContentType "application/json"
```
Expected: `category = SLOW_INTERNET`, policy sources from
`Slow Internet Troubleshooting SOP.md`.

### Billing dispute

```powershell
$body = @{ customer_id = "CUST0015"; complaint = "I was charged twice for the same service this month. Can you please fix my bill?" } | ConvertTo-Json
Invoke-RestMethod -Uri "http://127.0.0.1:8000/complaint" -Method Post -Body $body -ContentType "application/json"
```
Expected: `category = BILLING`, policy sources from
`Billing Complaint Policy.md`.

### Refund request

```powershell
$body = @{ customer_id = "CUST0069"; complaint = "Can I get my money back for the service outage last week?" } | ConvertTo-Json
Invoke-RestMethod -Uri "http://127.0.0.1:8000/complaint" -Method Post -Body $body -ContentType "application/json"
```
Expected: `category = REFUND`, policy sources from `Customer Refund Policy.md`.

### General / repeated-contact escalation

```powershell
$body = @{ customer_id = "CUST0070"; complaint = "I have contacted support three times and my issue is still unresolved. This is unacceptable." } | ConvertTo-Json
Invoke-RestMethod -Uri "http://127.0.0.1:8000/complaint" -Method Post -Body $body -ContentType "application/json"
```
Expected: `category = CUSTOMER_SERVICE`, `repeated_contact = true`
(customer `CUST0070` already has history in `data/complaint_history.csv`),
policy sources include `Customer Complaint Escalation Policy.md`.

### Unsupported / insufficient-information case

```powershell
$body = @{ customer_id = "CUST0099"; complaint = "Can you upgrade my plan to include international roaming in Japan?" } | ConvertTo-Json
Invoke-RestMethod -Uri "http://127.0.0.1:8000/complaint" -Method Post -Body $body -ContentType "application/json"
```
Nothing in the knowledge base covers international roaming plan changes, so
the assistant should avoid inventing an answer — expect a generic
acknowledgement, low-relevance policy sources, and a good chance of
`validation_status: "ESCALATED"` after retries are exhausted, since the
response agent has nothing solid to ground a specific answer in.

### Retry-and-escalate path (manually observed)

If the validator fails a draft twice in a row (e.g. because the response
agent's phrasing strays from what the policy actually supports), the graph
automatically retries the response generation with the validator's failure
reason fed back in, and — if it still fails after `MAX_RETRIES` — returns:

```json
{
  "validation_status": "ESCALATED",
  "escalated": true,
  "response": "Thank you for reaching out, and I'm sorry for the ongoing trouble. ..."
}
```

This is the conditional-retry / escalation logic in
`backend/graph/workflow.py` (`_route_after_validation`), capped so the graph
can never loop indefinitely.

---

## 8. Troubleshooting

| Symptom | Fix |
|---|---|
| `RuntimeError: GOOGLE_API_KEY is not set` | Fill in `.env`, not `.env.example` |
| `FileNotFoundError: FAISS index not found` | Run `python scripts/build_faiss_index.py` |
| `no such table: complaint_history` | Run `python scripts/init_db.py` |
| `CERTIFICATE_VERIFY_FAILED` during pip install / model download | `pip install pip-system-certs`, then retry |
| Every response gets `ESCALATED` | Check `validation_reason` in the response — the validator may be flagging a genuine unsupported claim; check the LLM key/quota if reasons look like parsing failures |
| Frontend won't connect to backend | Ensure backend is running on `127.0.0.1:8000` and frontend on `127.0.0.1:5173`; check browser console for CORS or connection errors |
| `npm install` fails | Delete `node_modules/` and `package-lock.json`, then retry; ensure Node.js 16+ is installed |
| Progress events not showing | The `/complaint-stream` endpoint streams SSE; check browser Network tab to see raw event-stream response |
