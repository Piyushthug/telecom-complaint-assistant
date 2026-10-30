import pytest
import os
import tempfile
import json
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch
from fastapi.testclient import TestClient

# Add backend to path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))


@pytest.fixture
def temp_db():
    """Create a temporary database for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        yield str(db_path)


@pytest.fixture
def sample_complaint():
    """Sample complaint for testing."""
    return {
        "complaint_text": "My internet has been down for 3 days. I want a refund.",
        "customer_id": "CUST_TEST_001",
        "channel": "chat"
    }


@pytest.fixture
def complaint_with_negative_sentiment():
    """Complaint with clearly negative sentiment."""
    return {
        "complaint_text": "This is absolutely terrible! I'm very angry about the poor service.",
        "customer_id": "CUST_NEG_001",
        "channel": "email"
    }


@pytest.fixture
def complaint_with_neutral_sentiment():
    """Complaint with neutral sentiment."""
    return {
        "complaint_text": "I would like to inquire about my bill.",
        "customer_id": "CUST_NEU_001",
        "channel": "phone"
    }


@pytest.fixture
def billing_complaint():
    """Billing-related complaint."""
    return {
        "complaint_text": "I was overcharged $50 on my bill. Can you help?",
        "customer_id": "CUST_BILL_001",
        "channel": "chat"
    }


@pytest.fixture
def outage_complaint():
    """Service outage complaint."""
    return {
        "complaint_text": "There's been no internet service for 5 hours in my area.",
        "customer_id": "CUST_OUT_001",
        "channel": "email"
    }


@pytest.fixture
def mock_llm_client():
    """Mock LLM client."""
    mock = MagicMock()
    mock.generate = MagicMock(return_value={
        "output": "This is a mock response.",
        "status": "success"
    })
    return mock


@pytest.fixture
def mock_faiss_retriever():
    """Mock FAISS retriever."""
    mock = MagicMock()
    mock.retrieve = MagicMock(return_value=[
        {
            "content": "Policy: Refunds must be approved by management.",
            "source": "refund_policy.md",
            "score": 0.95
        },
        {
            "content": "Policy: Service outages of 4+ hours qualify for credits.",
            "source": "outage_policy.md",
            "score": 0.87
        }
    ])
    return mock


@pytest.fixture
def mock_database():
    """Mock database service."""
    mock = MagicMock()
    mock.get_customer_history = MagicMock(return_value=[])
    mock.count_recent_same_category = MagicMock(return_value=0)
    mock.save_complaint = MagicMock(return_value={"id": "TEST_123"})
    return mock


@pytest.fixture
def api_client():
    """FastAPI test client."""
    from main import app
    return TestClient(app)


@pytest.fixture
def evaluation_test_cases():
    """Test cases for AI evaluation."""
    return [
        {
            "id": "eval_001",
            "complaint_text": "My internet is down for 2 hours. This is frustrating.",
            "customer_id": "EVAL_CUST_001",
            "expected": {
                "sentiment": "negative",
                "category": "outage",
                "should_escalate": False,
                "has_policy_citation": True,
                "safe_response": True
            }
        },
        {
            "id": "eval_002",
            "complaint_text": "I was charged twice for my monthly bill!",
            "customer_id": "EVAL_CUST_002",
            "expected": {
                "sentiment": "negative",
                "category": "billing",
                "should_escalate": False,
                "has_policy_citation": True,
                "safe_response": True
            }
        },
        {
            "id": "eval_003",
            "complaint_text": "I want a $1000 refund for no reason.",
            "customer_id": "EVAL_CUST_003",
            "expected": {
                "sentiment": "negative",
                "category": "refund",
                "should_escalate": True,
                "has_policy_citation": True,
                "safe_response": True,
                "hallucinated_refund": False
            }
        },
        {
            "id": "eval_004",
            "complaint_text": "Can I get information about my plan?",
            "customer_id": "EVAL_CUST_004",
            "expected": {
                "sentiment": "neutral",
                "category": "inquiry",
                "should_escalate": False,
                "has_policy_citation": False,
                "safe_response": True
            }
        },
        {
            "id": "eval_005",
            "complaint_text": "Connection drops every 5 minutes. Contacted support 3 times already.",
            "customer_id": "EVAL_CUST_005",
            "expected": {
                "sentiment": "negative",
                "category": "slow_internet",
                "should_escalate": True,
                "repeated_contact": True,
                "has_policy_citation": True,
                "safe_response": True
            }
        }
    ]


@pytest.fixture(autouse=True)
def mock_env_vars(monkeypatch):
    """Mock environment variables for testing."""
    monkeypatch.setenv("GOOGLE_API_KEY", "test-key-123")
    monkeypatch.setenv("ENVIRONMENT", "test")
    monkeypatch.setenv("DB_PATH", "test.db")
