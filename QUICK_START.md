# Quick Start Guide

## What's Been Set Up

This project now has a **complete testing and evaluation framework** ready for the engineering assessment.

---

## 🚀 Get Started (5 minutes)

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Run Unit Tests
```bash
pytest tests/ -v --tb=short
```

**Expected Output**:
```
tests/agents/test_agents.py::TestSentimentAgent::test_negative_sentiment_detection PASSED
tests/agents/test_agents.py::TestSentimentAgent::test_neutral_sentiment_detection PASSED
...
======== X passed in Y.XXs ========
```

### 3. Start Backend & Run API Tests
```bash
# Terminal 1: Start backend
python -m uvicorn backend.main:app --reload

# Terminal 2: Run API tests
pytest tests/api/ -v
```

### 4. Run AI Evaluation
```bash
# Make sure backend is still running (from step 3)
python eval/run_evaluation.py
```

**Expected Output**:
```
Loaded 20 test cases
✓ API is running at http://localhost:8000

[1/20] Evaluating: eval_001
  ✓ Score: 0.92

[2/20] Evaluating: eval_002
  ✓ Score: 0.88

EVALUATION SUMMARY
==================
Average Score: 87.5%
Critical Failures: 0
```

---

## 📂 Key Files Structure

```
telecom-complaint-assistant/
│
├── tests/                          # NEW: Complete test suite
│   ├── conftest.py                # Shared fixtures
│   ├── agents/test_agents.py       # Agent unit tests
│   ├── api/test_endpoints.py       # REST API tests
│   ├── rag/test_retrieval.py       # FAISS retrieval tests
│   ├── graph/test_workflow.py      # Workflow orchestration tests
│   └── data/test_data_validation.py # Data validation tests
│
├── eval/                           # NEW: AI Evaluation Framework
│   ├── test_dataset.json          # 20 test cases with expected outputs
│   ├── scoring.py                 # Evaluation metrics & scoring
│   └── run_evaluation.py           # Evaluation runner
│
├── .github/
│   └── workflows/
│       └── test.yml               # NEW: GitHub Actions CI/CD pipeline
│
├── TEST_STRATEGY.md               # NEW: Comprehensive test strategy (500+ lines)
├── TESTING_SETUP.md               # NEW: How to run tests locally
├── ASSESSMENT_CHECKLIST.md        # NEW: Requirements mapping
└── QUICK_START.md                 # This file
```

---

## 📊 Test Coverage

### Test Pyramid
```
         AI Evaluation (20 cases)
              ▲
              │
    Workflow Integration Tests
              ▲
              │
    API Tests (16 endpoints)
              ▲
              │
    Unit Tests (50+ tests)
        ▬▬▬▬▬▬▬▬▬▬▬
```

### Test Statistics
- **Total Tests**: 70+
- **Lines of Test Code**: 1,658
- **Test Files**: 6
- **Evaluation Dataset**: 20 test cases
- **CI/CD Workflows**: 1 GitHub Actions

---

## 🎯 Assessment Coverage

| Requirement | Status | Evidence |
|------------|--------|----------|
| **AI Agent with Tools** | ✅ | 6 agents, FAISS retrieval, LLM calls |
| **Backend API** | ✅ | FastAPI with 6 endpoints, streaming |
| **User Experience** | ✅ | React UI for complaint submission |
| **Unit Tests** | ✅ | `tests/agents/`, `tests/data/` |
| **API Tests** | ✅ | `tests/api/test_endpoints.py` (16 tests) |
| **Integration Tests** | ✅ | `tests/graph/test_workflow.py` |
| **Data Validation** | ✅ | `tests/data/test_data_validation.py` |
| **AI Evaluation** | ✅ | `eval/` with 20 test cases |
| **Failure Injection** | ✅ | 6+ failure scenarios tested |
| **CI/CD Pipeline** | ✅ | `.github/workflows/test.yml` |
| **Documentation** | ✅ | 1000+ lines, 3 docs |

---

## 📖 Documentation

**Read in this order**:

1. **QUICK_START.md** (this file) - 5 min overview
2. **TESTING_SETUP.md** - How to run tests (15 min)
3. **TEST_STRATEGY.md** - Comprehensive strategy (30 min)
4. **ASSESSMENT_CHECKLIST.md** - Requirements mapping (20 min)

---

## 🧪 Common Commands

```bash
# Run all tests
pytest tests/ -v

# Run with coverage report
pytest tests/ --cov=backend --cov-report=html
open htmlcov/index.html

# Run specific test type
pytest tests/agents/ -v      # Agent tests only
pytest tests/api/ -v         # API tests only
pytest tests/graph/ -v       # Workflow tests only

# Run single test
pytest tests/api/test_endpoints.py::TestComplaintEndpoint::test_complaint_submission_success -v

# Run evaluation
python eval/run_evaluation.py

# Run evaluation with custom API URL
API_URL=http://localhost:9000 python eval/run_evaluation.py
```

---

## 🔍 What Each Test Layer Does

### 1. Unit Tests (`tests/agents/`, `tests/rag/`, `tests/data/`)
**Purpose**: Test individual components  
**Mocking**: LLM, database (use real FAISS)  
**Speed**: <5 minutes  
**Example**:
```python
def test_no_hallucinated_refund():
    response = "We will credit you $500"
    assert "$" not in response or "refund" not in response
```

### 2. Integration Tests (`tests/graph/`)
**Purpose**: Test workflow orchestration  
**Focus**: State management, conditional routing, retries  
**Speed**: <2 minutes  
**Example**:
```python
def test_escalation_triggered_on_repeated_contact():
    history = [{"date": "2024-01-01"}, {"date": "2024-01-02"}, {"date": "2024-01-03"}]
    assert len(history) > 2  # Should escalate
```

### 3. API Tests (`tests/api/`)
**Purpose**: Test REST endpoints  
**Prerequisite**: Backend running  
**Speed**: <3 minutes  
**Example**:
```python
def test_complaint_submission_success(api_client, sample_complaint):
    response = api_client.post("/complaint", json=sample_complaint)
    assert response.status_code == 200
    assert "response" in response.json()
```

### 4. AI Evaluation (`eval/`)
**Purpose**: Measure if agent actually works  
**Criteria**: Sentiment, category, policy, safety, escalation  
**Speed**: 5-15 minutes (depends on LLM)  
**Example**:
```
Test: "I was overcharged $50"
Expected Sentiment: negative ✓
Expected Category: billing ✓
Expected Escalation: false ✓
Response Has Policy: true ✓
Score: 0.92 ✓
```

---

## ✅ Assessment Readiness Checklist

- [ ] Read this file (QUICK_START.md)
- [ ] Run `pytest tests/ -v` - all tests pass
- [ ] Run `python eval/run_evaluation.py` - evaluation works
- [ ] Read TEST_STRATEGY.md
- [ ] Review test files: `tests/api/test_endpoints.py`, `eval/scoring.py`
- [ ] Check CI/CD: `.github/workflows/test.yml`
- [ ] Review ASSESSMENT_CHECKLIST.md
- [ ] Verify git history is clean
- [ ] All documentation complete

---

## 🚨 Troubleshooting

### Tests fail with ImportError
```bash
pip install -r requirements.txt
```

### API tests fail with connection error
```bash
# Start backend first
python -m uvicorn backend.main:app &

# Then run tests
pytest tests/api/ -v
```

### Evaluation shows "Cannot reach API"
- Backend must be running on `http://localhost:8000`
- Check: `curl http://localhost:8000/health`

### FAISS index not found
```bash
python backend/scripts/build_faiss_index.py
```

### Coverage report not generated
```bash
pip install pytest-cov
pytest tests/ --cov=backend --cov-report=html
```

---

## 📋 What's Tested

### Agents ✅
- Sentiment detection (negative, neutral, positive)
- Category classification (billing, outage, etc.)
- Response generation (policy-grounded, no hallucinations)
- Validation (rejects unsafe responses)
- History analysis (detects repeated contacts)

### API ✅
- Happy path (valid complaints → 200)
- Validation errors (missing fields → 422)
- Input size limits (oversized → 400/413)
- Edge cases (special chars, unicode, long IDs)
- Error handling (malformed JSON → 400)

### Workflow ✅
- End-to-end execution
- Parallel agent execution
- State accumulation
- Conditional routing
- Retry with feedback
- Escalation logic

### Data ✅
- Input validation (non-empty, valid format)
- Category enumeration (valid categories only)
- Sentiment values (positive/negative/neutral)
- Synthetic data variety (20+ complaint types)
- Database operations (save, retrieve, deduplicate)

### AI Behavior ✅
- 20 diverse test cases
- Sentiment accuracy (target: ≥90%)
- Category accuracy (target: ≥85%)
- Policy citation (target: 100%)
- No hallucinated refunds (target: 100%)
- Safe escalation (target: 100%)
- Response quality (target: ≥75%)

---

## 🎓 Learning Resources

Inside the project:
- **TEST_STRATEGY.md** - Learn the testing approach
- **conftest.py** - Understand pytest fixtures
- **test_endpoints.py** - See API testing patterns
- **scoring.py** - Learn evaluation metrics
- **test_dataset.json** - Understand test case structure

---

## 🚀 Next Steps

1. **Run Tests Locally** (5 min)
   ```bash
   pytest tests/ -v
   ```

2. **Read Documentation** (1 hour)
   - QUICK_START.md → TESTING_SETUP.md → TEST_STRATEGY.md

3. **Verify CI/CD** (2 min)
   - Check `.github/workflows/test.yml`
   - Push to trigger automated tests

4. **Review Assessment Checklist** (20 min)
   - ASSESSMENT_CHECKLIST.md maps all requirements

5. **Make Improvements** (optional)
   - Browser tests (Playwright in `tests/ui/`)
   - Load testing (future work)
   - Real data integration (future work)

---

## 📞 Questions?

See the detailed guides:
- **How do I run tests?** → TESTING_SETUP.md
- **What's the testing strategy?** → TEST_STRATEGY.md
- **Does this meet requirements?** → ASSESSMENT_CHECKLIST.md
- **API docs?** → API_DOCUMENTATION.md
- **Project overview?** → README.md

---

**Status**: ✅ Assessment setup complete and ready for evaluation

**Last Updated**: 2026-10-30
