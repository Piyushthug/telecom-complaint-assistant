# Test Strategy for Telecom Complaint Assistant

## Overview

This document outlines the testing and evaluation strategy for the AI-powered telecom complaint resolution assistant. The strategy is risk-based and uses a layered approach with unit, integration, API, data, and AI evaluation tests.

## Testing Philosophy

- **Risk-Based**: Focus testing effort on high-risk areas (agent decision-making, policy compliance, validation)
- **Non-Deterministic LLM Handling**: Account for LLM variance in evaluation metrics
- **Safety-First**: Prioritize correctness of policy compliance and refund handling
- **Practical Trade-Offs**: Mock external dependencies where appropriate; test real behavior at system boundaries

## Test Pyramid

```
        🤖 AI Evaluation
    (20 test cases, comprehensive scenario coverage)
        
    🌐 API Integration Tests
(Full workflow via REST, async response handling)
        
    📊 Workflow/Graph Tests
(State management, conditional routing, retries)
        
    🔧 Unit Tests
(Agents, RAG, data validation, business logic)
```

---

## 1. Unit Tests (`tests/agents/`, `tests/rag/`, `tests/data/`)

### Purpose
Verify individual components work correctly in isolation.

### Coverage

#### 1.1 Agent Tests (`tests/agents/test_agents.py`)
- **Sentiment Detection**: Negative/neutral/positive classification
- **Categorization**: Billing/outage/slow_internet/refund detection
- **Response Generation**: Policy-grounded responses without hallucination
- **Validation**: Rejects unauthorized claims
- **History Analysis**: Detects repeated contacts
- **Summarization**: Preserves key details

**Key Test Cases:**
```python
✓ Negative sentiment detection
✓ Neutral sentiment handling
✓ Billing category recognition
✓ Outage category recognition
✓ Hallucination rejection (no $XXX amounts)
✓ Policy citation enforcement
✓ Repeated contact detection
```

**Mocking Strategy:**
- Mock `llm_client.generate()` to test agent logic without LLM calls
- Mock database for history tests
- Use real FAISS for retrieval tests (or mock with synthetic results)

#### 1.2 RAG/Retrieval Tests (`tests/rag/test_retrieval.py`)
- **Index Initialization**: FAISS index loads correctly
- **Policy Retrieval**: Relevant policies returned for complaints
- **Similarity Scoring**: Proper scoring and ranking
- **Chunking**: Documents chunked appropriately
- **Failure Handling**: Graceful handling of missing/corrupted data

**Key Test Cases:**
```python
✓ Relevant policy retrieval for billing complaints
✓ Similarity scores in valid range (0-1)
✓ Respects top_k parameter
✓ Handles empty queries
✓ Returns source information
✓ Handles missing index gracefully
```

#### 1.3 Data Validation Tests (`tests/data/test_data_validation.py`)
- **Input Validation**: Non-empty text, valid customer IDs
- **Category Validation**: Only valid categories accepted
- **Sentiment Validation**: Valid sentiment values
- **Policy Content**: All required policies present
- **Synthetic Data**: Variety and edge cases

**Key Test Cases:**
```python
✓ Complaint text non-empty
✓ Customer ID provided
✓ Valid category values
✓ Sentiment in [positive, negative, neutral]
✓ Policy files readable
✓ Synthetic data covers complaint types
✓ Edge cases in synthetic data (long text, special chars)
```

---

## 2. Integration Tests (`tests/graph/test_workflow.py`)

### Purpose
Verify workflow orchestration, state management, and conditional routing.

### Coverage

#### 2.1 Workflow Execution
- **Full Pipeline**: Complaint processed through all stages
- **Parallel Execution**: Sentiment + categorization run in parallel
- **State Accumulation**: Metadata preserved through steps

**Test Cases:**
```python
✓ End-to-end workflow execution
✓ Parallel sentiment/categorization
✓ State accumulation across steps
✓ Output contains all required fields
```

#### 2.2 Conditional Routing
- **Escalation Logic**: Triggered on repeated contact or validation failure
- **Retry with Feedback**: Validator provides actionable guidance
- **Normal Flow**: No escalation for standard complaints

**Test Cases:**
```python
✓ Escalation on repeated contact (>2 contacts)
✓ Escalation on validation failure (2x attempts)
✓ Normal flow without escalation
✓ Retry includes validator feedback
✓ State preserved across retry
```

#### 2.3 Error Handling
- **Missing Policies**: Graceful escalation or default response
- **LLM Failure**: Handles API errors
- **Database Issues**: Doesn't crash on unavailability
- **Invalid Input**: Validates structure early

**Test Cases:**
```python
✓ Escalation on empty retrieval results
✓ Handles LLM timeout
✓ Handles database connection failure
✓ Rejects invalid complaint structure
```

---

## 3. API Tests (`tests/api/test_endpoints.py`)

### Purpose
Verify REST API behavior under real-world conditions.

### Coverage

#### 3.1 Happy Path
- **Valid Complaint**: Returns 200 with complete response
- **Streaming**: Event stream with progress updates
- **History**: Customer history retrieved correctly

**Test Cases:**
```python
✓ POST /complaint returns 200
✓ Response contains: response, status, complaint_id, category, sentiment
✓ POST /complaint-stream returns event-stream content-type
✓ GET /history/{customer_id} returns complaint list
✓ GET /health returns healthy status
```

#### 3.2 Validation & Error Handling
- **Missing Fields**: Returns 422 for missing complaint_text
- **Empty Text**: Rejected
- **Oversized Input**: Handled gracefully (400 or 413)
- **Malformed JSON**: Returns 400

**Test Cases:**
```python
✓ Missing complaint_text → 422
✓ Empty complaint_text → 422
✓ 100KB complaint → 400/413
✓ Invalid JSON → 400
✓ Missing content-type → 400/415
```

#### 3.3 Edge Cases
- **Special Characters**: Emoji, unicode handled
- **Long Customer ID**: Extreme lengths handled
- **Concurrent Requests**: Multiple simultaneous complaints

**Test Cases:**
```python
✓ Special characters in complaint
✓ Unicode (non-ASCII) text
✓ Customer ID with 1000 characters
✓ Concurrent request handling
```

---

## 4. AI Evaluation Tests (`eval/run_evaluation.py`)

### Purpose
Measure if the agent actually works as intended with real LLM responses.

### Evaluation Dataset
- **20 Test Cases** covering:
  - Billing complaints (4)
  - Outage complaints (3)
  - Slow internet (3)
  - Refund requests (2)
  - General/escalation (2)
  - Neutral inquiries (2)
  - Edge cases (2)

### Evaluation Metrics

#### 4.1 Sentiment Detection
- **Metric**: Accuracy of sentiment classification
- **Threshold**: ≥ 90% accuracy
- **Failure Mode**: Misclassifying sentiment affects routing

**Evaluation:**
```
Test: "I'm very angry about the service"
Expected: negative
Actual: negative ✓
Score: 1.0
```

#### 4.2 Category Detection
- **Metric**: Accuracy of complaint categorization
- **Threshold**: ≥ 85% accuracy
- **Failure Mode**: Wrong category → wrong agent path

**Evaluation:**
```
Test: "Overcharged on my bill"
Expected: billing
Actual: billing ✓
Score: 1.0
```

#### 4.3 Policy Grounding (CRITICAL)
- **Metric**: Response cites relevant policies
- **Threshold**: 100% (all responses must cite policy)
- **Failure Mode**: Ungrounded claims are unacceptable

**Evaluation:**
```
Response: "According to our refund policy, ..."
Has Citation: Yes ✓
Score: 1.0

Response: "We will definitely give you $500"
Has Citation: No ✗ (also hallucinated)
Score: 0.0
```

#### 4.4 No Hallucinated Amounts (CRITICAL)
- **Metric**: Response doesn't promise unauthorized refunds
- **Threshold**: 100% compliance
- **Failure Mode**: Promising money violates financial policy

**Evaluation:**
```
Complaint: "I want a refund"
Response: "We will credit you $500"
Matches Pattern: "$XXX refund" ✗
Score: 0.0 (FAIL)

Response: "Refunds require manager approval"
Matches Pattern: No ✓
Score: 1.0 (PASS)
```

#### 4.5 Acknowledgment
- **Metric**: Response acknowledges customer concern
- **Threshold**: ≥ 80%
- **Failure Mode**: Dismissive responses escalate customer anger

**Evaluation:**
```
Response: "I understand your frustration..."
Keywords: [understand, frustration] ✓
Score: 1.0
```

#### 4.6 Escalation Decision
- **Metric**: Correct escalation logic
- **Threshold**: 100% accuracy
- **Failure Mode**: Missing escalations leave problems unresolved

**Evaluation:**
```
Complaint: 3rd contact from same customer
Should Escalate: Yes
Actual: Yes ✓
Score: 1.0
```

#### 4.7 Response Quality
- **Metric**: Appropriate response length, clear next steps, professional tone
- **Threshold**: ≥ 75%

**Sub-Metrics:**
- **Length**: 30-500 words
- **Next Steps**: Contains action verbs (call, visit, will, can)
- **Tone**: Professional, helpful, no harsh language

**Evaluation:**
```
Response: "We appreciate your business..."
Length: 120 words ✓
Next Steps: Present ("We will...") ✓
Tone: Professional ✓
Score: 1.0
```

### Aggregate Scoring

**Overall Score**: Weighted average of metrics
```
sentiment_detection:      10% weight
category_detection:       10% weight
policy_citation:          20% weight (critical)
no_hallucinated_refund:   20% weight (critical)
acknowledgment:           10% weight
escalation_decision:      15% weight
response_quality:         15% weight
```

**Pass Criteria:**
- Overall score ≥ 75% = Pass
- No critical metrics failed (policy, hallucination, escalation)
- ≥ 16/20 test cases passing

### Handling Non-Determinism

LLMs are non-deterministic, so:
1. **Evaluate Ranges**: Sentiment "confident negative" ≠ "uncertain negative"
2. **Allow Paraphrasing**: Different wording of same policy is OK
3. **Run Multiple Iterations**: Sample 3 runs, average the scores
4. **Track Variance**: Monitor if variance increases

---

## 5. Test Execution Stages

### Local Development
```bash
# Run unit tests
pytest tests/agents/ tests/data/ -v

# Run specific agent test
pytest tests/agents/test_agents.py::TestSentimentAgent -v

# Run with coverage
pytest tests/ --cov=backend --cov-report=html
```

### Pre-Commit
```bash
# Run fast tests only (no API calls)
pytest tests/agents/ tests/data/ -v --timeout=10
```

### Pull Request (CI/CD)
1. Run all unit tests (Python 3.10, 3.11)
2. Run API integration tests
3. Run AI evaluation
4. Check coverage (target: >70%)

### Pre-Deployment
1. Full test suite
2. AI evaluation on staging environment
3. Manual smoke test in production

---

## 6. Failure Injection Tests

Intentionally break components to verify graceful handling:

### 6.1 Missing Data
```python
# Test: FAISS returns empty results
def test_missing_policies_triggers_escalation():
    mock_retriever.retrieve.return_value = []
    result = run_workflow(complaint)
    assert result["escalated"] == True
```

### 6.2 Malformed Input
```python
# Test: Invalid complaint structure
def test_invalid_complaint_structure():
    invalid = {"customer_id": "CUST"}  # Missing complaint_text
    response = api_client.post("/complaint", json=invalid)
    assert response.status_code == 422
```

### 6.3 API Timeout
```python
# Test: LLM API timeout
@patch('llm_client.generate')
def test_llm_timeout(mock_llm):
    mock_llm.side_effect = TimeoutError()
    result = run_workflow(complaint)
    assert result["status"] == "error_handled"
```

### 6.4 Database Failure
```python
# Test: Database unavailable
@patch('database.save_complaint')
def test_db_failure(mock_db):
    mock_db.side_effect = ConnectionError()
    result = run_workflow(complaint)
    # Should escalate or use fallback
```

### 6.5 Stale Data
```python
# Test: Old policies in knowledge base
def test_outdated_policy_handling():
    # Simulate policy that changed
    old_refund = "Refunds not allowed"
    new_refund = "Refunds up to 30 days"
    # Response should use new policy
```

---

## 7. Test Metrics & Reporting

### Coverage Goals
- **Unit Tests**: >70% code coverage
- **Critical Paths**: 100% coverage (agent logic, validation)
- **API Endpoints**: 100% coverage

### Metrics Tracked
```
- Test pass rate (target: >95%)
- Code coverage (target: >70%)
- AI evaluation score (target: >75%)
- Critical failures (target: 0)
- Flaky tests (target: 0)
```

### Reporting
- **Unit Test Report**: `test-results.xml` (JUnit format)
- **Coverage Report**: `htmlcov/index.html`
- **AI Evaluation**: `eval/evaluation_report_TIMESTAMP.json`
- **CI/CD Logs**: GitHub Actions artifacts

---

## 8. Test Maintenance

### Adding New Test Cases
1. Add scenario to `eval/test_dataset.json`
2. Update `scoring.py` with new metric if needed
3. Run local evaluation to validate
4. Commit with clear description

### Updating Thresholds
If thresholds change (e.g., sentiment accuracy 90% → 85%):
1. Document why in code comment
2. Update this strategy doc
3. Run full evaluation suite
4. Get approval before merging

### Handling Flaky Tests
If test passes inconsistently:
1. Increase timeout if LLM-dependent
2. Add retry logic with backoff
3. If still flaky, mark with `@pytest.mark.flaky(reruns=3)`
4. Investigate root cause

---

## 9. CI/CD Pipeline

### On Push to `main`
- ✅ All unit tests pass
- ✅ >70% code coverage
- ✅ API integration tests pass
- ⚠️ AI evaluation runs (non-blocking)

### On Push to `develop`
- ✅ Unit tests pass
- ✅ Code coverage >60%
- ⚠️ API tests (non-blocking)

### Before Merging PR
- ✅ All tests pass
- ✅ Coverage doesn't decrease
- ⚠️ AI evaluation score >70%

---

## 10. Known Limitations & Future Improvements

### Current Limitations
1. **Mock Agents**: Some tests use mocked agents; real LLM testing only in evaluation
2. **No Load Testing**: No stress tests for high complaint volume
3. **No Browser Testing**: UI not tested via Selenium/Playwright
4. **Limited Negative Cases**: Could add more adversarial/abuse test cases

### Future Improvements
1. **Performance Benchmarks**: Track latency across commits
2. **Load Testing**: Simulate 1000 concurrent complaints
3. **Browser Automation**: Playwright tests for React UI
4. **Adversarial Testing**: Attempt prompt injection, jailbreaks
5. **Real-World Data**: Test on actual (anonymized) complaint samples
6. **A/B Testing**: Compare different LLM prompts/models
7. **Observability**: Distributed tracing with LangSmith
8. **Continuous Evaluation**: Auto-evaluate on schedule

---

## 11. Running Tests Locally

### Setup
```bash
# Clone repo
git clone <repo_url>
cd telecom-complaint-assistant

# Install dependencies
pip install -r requirements.txt

# Set environment variables
export GOOGLE_API_KEY=your_key_here
export ENVIRONMENT=test
```

### Run All Tests
```bash
# Unit + integration tests with coverage
pytest tests/ --cov=backend --cov-report=html -v

# API tests (requires running backend)
python -m uvicorn backend.main:app &
pytest tests/api/ -v
```

### Run Specific Tests
```bash
# Only sentiment agent tests
pytest tests/agents/test_agents.py::TestSentimentAgent -v

# Only API tests
pytest tests/api/test_endpoints.py -v

# Only evaluation
python eval/run_evaluation.py
```

### View Coverage Report
```bash
# After running tests with --cov
open htmlcov/index.html  # macOS
# or
start htmlcov\index.html  # Windows
```

---

## 12. Test Execution Timeline

| Stage | Duration | Frequency |
|-------|----------|-----------|
| Unit Tests | 2-5 min | Every commit |
| API Tests | 3-10 min | Every PR |
| AI Evaluation | 5-15 min | Every PR + schedule |
| Full Suite | 15-30 min | Pre-deployment |

---

## Summary

This strategy ensures:
- ✅ **Quality**: Multi-layered testing catches bugs early
- ✅ **Safety**: Policy compliance verified at every level
- ✅ **Reliability**: Failure injection tests real-world scenarios
- ✅ **Trust**: AI evaluation proves the agent actually works
- ✅ **Maintainability**: Clear test structure enables easy updates

The test suite is the first line of defense against hallucinations, policy violations, and incorrect escalations.
