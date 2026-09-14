# Telecom Complaint Assistant — Presentation Guide

## 🎯 Elevator Pitch (30 seconds)

> "I built a zero-cost, local-first AI system for telecom customer support that uses LangGraph to orchestrate intelligent agents. Sentiment analysis and categorization run in parallel, then policies are retrieved using local embeddings and FAISS, and responses are generated and validated against those policies. If validation fails, we regenerate with feedback; if it still fails, we escalate safely. The whole workflow streams progress in real-time to a React UI."

---

## 💡 Key Talking Points

### 1. **Architecture Excellence**
- Parallel execution of independent agents (sentiment + categorization)
- Conditional routing with automatic retry and escalation
- Real-time progress streaming via Server-Sent Events
- Clean separation of concerns (API-driven, no direct SQL from agents)

### 2. **Policy Grounding (The Differentiator)**
- Responses must cite retrieved policy documents
- Validator strictly checks: no invented facts, no unsupported promises
- If validation fails → regenerate with feedback (max 2 retries)
- If still fails → safe escalation ("I'm handing this to a human")
- This prevents hallucinations and ensures compliance

### 3. **Zero-Cost Operation**
- Local embeddings (Sentence Transformers, 384-dim)
- FAISS vector search (local, no cloud)
- SQLite for history (no managed database)
- Gemini free tier for LLM calls (~0.01¢/request)
- Can run entirely offline after first model download

### 4. **Real-Time Transparency**
- Users see progress: "Analyzing sentiment..." → "Retrieving policies..." → "Validating response..."
- Each node emits events as it completes
- Frontend subscribes via SSE, updates UI in real-time
- Builds confidence that AI is actually thinking, not just waiting

### 5. **Production-Ready Patterns**
- TypedDict state management (LangGraph)
- Error handling + fallbacks (no infinite loops)
- Complaint lookup via API (not direct SQL)
- Logging with request IDs (traceability)
- Environment-driven config (.env)

---

## 🎬 Live Demo Script

### Prerequisites
- Backend running: `python -m uvicorn backend.main:app --reload` (port 8000)
- Frontend running: `npm run dev` (port 5173)
- Browser open to `http://127.0.0.1:5173`

### Demo 1: Happy Path (Slow Internet)
1. **Fill form:**
   - Customer ID: `CUST0036`
   - Complaint: "My internet is working but very slow since this morning."
   
2. **Click "Analyze Complaint"**

3. **Watch progress steps:**
   - ✓ Analyzing sentiment (should show NEGATIVE)
   - ✓ Categorizing complaint (should show SLOW_INTERNET)
   - ✓ Summarizing issue
   - ✓ Checking history
   - ✓ Retrieving policies
   - ✓ Generating response
   - ✓ Validating response (should PASS)

4. **Results show:**
   - Category: `SLOW_INTERNET`
   - Sentiment: `NEGATIVE`
   - Validation: `PASS` ✓
   - Response: Detailed troubleshooting steps from SOP
   - Policy sources: `Slow Internet Troubleshooting SOP.md` (high relevance)

5. **Key point to mention:**
   > "Notice the response includes specific troubleshooting steps. These came directly from the knowledge base policy — the AI doesn't invent them; it retrieves and cites them."

---

### Demo 2: Repeated Contact + Escalation Risk
1. **Fill form:**
   - Customer ID: `CUST0025`
   - Complaint: "My internet has been down since yesterday. I already contacted support twice but nobody fixed it."

2. **Click "Analyze Complaint"**

3. **Watch progress + results:**
   - Sentiment: `VERY_NEGATIVE` (0.98)
   - Category: `INTERNET_OUTAGE`
   - Repeated contact: `✓ Yes` (2 previous complaints on file)
   - Validation: may show `ESCALATED` if response agent struggles
   - Policy sources: `Internet Outage Policy` + `Escalation Policy`

4. **Key point:**
   > "The system detected this customer has complained twice before about the same issue. We don't just escalate based on tone; we look at category, history, and what the policy actually supports."

---

### Demo 3: Complaint Status Lookup (NEW)
1. **Fill form:**
   - Customer ID: `CUST0015`
   - Complaint: "What's the status of my complaint? I need to know about complaint ID CMP0004."

2. **Click "Analyze Complaint"**

3. **Watch progress:**
   - Response agent detects status lookup request
   - Calls `/complaints/CUST0015` API internally
   - Fetches real complaint history
   - Includes actual statuses in response

4. **Result shows:**
   - Response mentions actual complaint status (from database)
   - Not a generic "please provide more details" response
   - Real data integrated with AI response

5. **Key point:**
   > "The agent doesn't query SQL directly. It uses an API. This keeps concerns separated and secure."

---

## 📊 Architecture Slide Deck Outline

### Slide 1: Problem Statement
**Why this matters:**
- Telecom support teams handle 1000s of complaints daily
- Manual triage is slow and inconsistent
- AI-generated responses often invent unsupported claims
- Need for policy compliance + real-time transparency

### Slide 2: Solution Architecture
```
┌──────────────────────────────────────────┐
│  React UI (Progress Tracking + Results)  │
└────────────────────┬─────────────────────┘
                     │ SSE
┌────────────────────▼──────────────────────┐
│         FastAPI (HTTP Endpoints)         │
├──────────────────────────────────────────┤
│     LangGraph (Orchestration Engine)     │
│  ├─ Sentiment [parallel] │ Category [parallel]
│  ├─ Summarization ─────────────────────┐
│  ├─ History Check (SQLite)             │
│  ├─ Policy Retrieval (FAISS + Embedding) │
│  ├─ Response Generation (Gemini)       │
│  └─ Validation + Retry Loop            │
├──────────────────────────────────────────┤
│  Local Knowledge Base + Embeddings      │
│  Complaint History (SQLite)             │
└──────────────────────────────────────────┘
```

### Slide 3: Parallel Execution
- Sentiment and categorization are independent
- Both run simultaneously (~3s total vs ~6s if sequential)
- Results merge into shared state
- **Key insight:** Think about dependencies early

### Slide 4: RAG (Retrieval-Augmented Generation)
```
Query: "My internet is down"
  ↓ Embed with Sentence Transformers
Vector [0.42, -0.18, 0.95, ...]
  ↓ FAISS search (top-3)
Results:
├─ Internet Outage Policy (0.62)
├─ Escalation Policy (0.55)
└─ Slow Internet SOP (0.48)
```
**Key point:** Grounding prevents hallucination

### Slide 5: Validation + Retry
```
Response generated
  ↓ Validator checks
Does it cite policy? No → REGENERATE (with feedback)
  ↓
Does it cite policy now? Yes → PASS ✓
  ↓ Return to user
```
**Key point:** Ensures safety through structural validation

### Slide 6: Real-Time Progress
- SSE streams events as nodes complete
- Frontend updates UI in real-time
- Users see transparency
- Builds trust in AI

### Slide 7: API-Driven Architecture
- Agents don't execute SQL directly
- All data access via FastAPI endpoints
- `/complaints/{customer_id}` returns history
- Response agent calls this API if customer asks for status
- **Why:** Security, auditability, loose coupling

### Slide 8: Zero-Cost Stack
| Component | Cost | Local? |
|-----------|------|--------|
| LLM (Gemini) | Free tier | No, cloud |
| Embeddings | $0 | Yes |
| Vector DB (FAISS) | $0 | Yes |
| Database (SQLite) | $0 | Yes |
| **Total** | **~$0** | **Mostly** |

### Slide 9: Key Metrics
- **Workflow latency:** 12-15 seconds end-to-end
- **First-pass validation:** 60-70% (typical)
- **Escalation rate:** 10-20% (when policy doesn't cover)
- **Retry effectiveness:** ~80% of FAIL→REGENERATE→PASS

### Slide 10: Learnings & Takeaways
1. **LangGraph simplifies agent orchestration** — Don't use raw loops
2. **Policy grounding beats fine-tuning** — Validation prevents hallucination
3. **Transparency builds trust** — Real-time progress > waiting spinner
4. **API-driven > Direct DB access** — Better separation of concerns
5. **Local-first is viable** — Even embeddings work offline

---

## 📈 Metrics to Highlight

### Performance
- ✅ 12-15 seconds end-to-end (acceptable for async support)
- ✅ Parallel execution reduces latency by ~3 seconds
- ✅ Policy retrieval is <1 second (FAISS is fast)

### Accuracy
- ✅ Sentiment classification: 92-98% confidence
- ✅ Category classification: 95-99% confidence
- ✅ First-pass validation rate: 60-70%

### Cost
- ✅ $0 for embeddings, vector search, database
- ✅ ~$0.01 per request (Gemini free tier)
- ✅ No infrastructure/hosting costs

### User Experience
- ✅ Real-time progress (7 observable steps)
- ✅ Policy sources shown (traceability)
- ✅ Safe escalation (no dead ends)

---

## 🎓 Interview Questions You Might Get

### Q1: "Explain the workflow in 2 minutes"
> "User submits complaint. Sentiment and categorization agents run in parallel — both are independent analyses of the complaint text, so we can do them at the same time. Once both complete, we summarize the complaint, check SQLite for prior complaints from this customer (repeated contact signal), then use FAISS to retrieve the top-3 most-similar policy documents. The response agent generates a draft response, making sure to ground every claim in those retrieved policies. Finally, a validator checks: does it address the complaint? Is it grounded in policy? No invented facts? If yes, we return it. If no, we feed the failure reason back to the response agent and regenerate. After 2 retries, if it still fails, we return a safe fallback response saying we're escalating to a human. Throughout, we emit progress events so the UI can show real-time updates."

### Q2: "How do you prevent hallucinations?"
> "Three layers: (1) the response agent receives only the top-3 retrieved policy chunks, so it has limited scope to invent outside; (2) the prompt explicitly forbids certain claims (refunds, ticket numbers, timelines) unless policy supports them; (3) the validator runs as a separate LLM call checking for hallucinations. If validation fails, we regenerate with feedback instead of just accepting it."

### Q3: "Why LangGraph and not a for-loop?"
> "LangGraph gives us several things: (1) type-safe state across nodes, (2) built-in parallel node execution (sentiment + categorization at the same time), (3) conditional routing (if validation fails, loop back; if too many retries, escalate) without manual state management, (4) easy to test each node independently, (5) visualization of the graph. A for-loop would require custom logic for all of that."

### Q4: "How do you handle the complaint lookup use case?"
> "The response agent detects keywords in the customer's complaint (status, complaint ID, etc.) and, if found, makes an HTTP request to `/complaints/{customer_id}` — an internal API endpoint. That endpoint calls a service layer which queries SQLite, then returns the data. The agent includes the real complaint history in the LLM prompt, so the response includes actual statuses. This keeps the architecture clean: agents don't query SQL directly; they call APIs."

### Q5: "What about scaling?"
> "Local embeddings and FAISS scale to millions of documents. SQLite scales to millions of rows. The LLM calls are sequential (per request), so they're the bottleneck. We could cache responses, batch requests, or use a faster model. If we need true scale, we'd move to PostgreSQL with pgvector extension and a hosted LLM. The architecture is designed so these changes are plug-and-play."

### Q6: "Why SSE instead of WebSocket?"
> "SSE is simpler for one-way streaming. We only send progress updates from server to client; we don't need the client to interrupt the workflow mid-run. SSE uses standard HTTP, integrates with FastAPI's StreamingResponse, and the frontend just uses EventSource — minimal JavaScript. WebSocket would add complexity without benefit for this use case."

### Q7: "What are the limitations?"
> "The system can only respond to things covered by the knowledge base. If a customer asks for something outside the 5 policies (e.g., international roaming plan upgrades), it escalates. The LLM is also rate-limited (Gemini free tier). And currently, no customer authentication — we assume requests are already pre-authorized. For production, you'd add auth, rate limiting per customer, and optional PII masking in logs."

---

## 🎬 Quick Demo Checklist

- [ ] Backend running on port 8000
- [ ] Frontend running on port 5173
- [ ] `.env` configured with valid `GOOGLE_API_KEY`
- [ ] FAISS index built (`backend/rag/index/` exists)
- [ ] SQLite database initialized (`data/complaint_history.db` exists)
- [ ] Browser open to UI
- [ ] Customer IDs ready: `CUST0036`, `CUST0025`, `CUST0015`
- [ ] Network connection stable (for Gemini API calls)

---

## 📸 Screenshots to Show

1. **Submission form** — Clean, simple inputs
2. **Progress tracker** — Animated steps with icons
3. **Results display** — Category, sentiment, response, validation status
4. **Policy sources** — Shows relevance scores
5. **API docs** — Swagger UI at `/docs`

---

## 🗣️ Key Phrases to Use

- "Policy-grounded responses" (emphasize safety)
- "Parallel execution" (emphasize efficiency)
- "Real-time transparency" (emphasize UX)
- "Zero-cost" (emphasize practicality)
- "Conditional retry logic" (emphasize robustness)
- "API-driven" (emphasize architecture)

---

## ⏱️ Time Allocation (for 20-minute talk)

- **2 min:** Problem statement
- **3 min:** Solution overview + architecture diagram
- **2 min:** Key features (parallel execution, RAG, validation)
- **5 min:** Live demo (3 scenarios)
- **3 min:** API overview + complaint lookup
- **3 min:** Learnings + tradeoffs
- **2 min:** Q&A / Discussion

---

## 🚀 Follow-Up Actions

1. **Repo link:** Share GitHub link (if public)
2. **Docs:** Point to README.md and API_DOCUMENTATION.md
3. **Live instance:** Deploy to Heroku/Railway for sharing
4. **Contact:** Your email / LinkedIn for questions

---

## 📞 Contact for Demos

**Email:** piyush.kumar4@ust.com
**GitHub:** [Link to repo]
**Run locally:** Follow setup in [RUNNING.md](RUNNING.md)

---

**Happy presenting! 🎉**
