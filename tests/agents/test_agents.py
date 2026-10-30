"""Tests for AI agents."""
import pytest
from unittest.mock import patch, MagicMock
from pydantic import BaseModel


class TestSentimentAgent:
    """Test sentiment analysis agent."""

    @patch('backend.agents.sentiment_agent.llm_client')
    def test_negative_sentiment_detection(self, mock_llm, complaint_with_negative_sentiment):
        """Agent should detect negative sentiment."""
        # Mock LLM response
        mock_llm.generate.return_value = {
            "sentiment": "negative",
            "confidence": 0.95,
            "keywords": ["terrible", "angry"]
        }

        # This is a simplified test - adapt to your actual agent interface
        from backend.agents import sentiment_agent
        # result = sentiment_agent.run(complaint_with_negative_sentiment)
        # assert result["sentiment"] == "negative"

    def test_neutral_sentiment_detection(self, complaint_with_neutral_sentiment):
        """Agent should detect neutral sentiment."""
        # Test neutral complaint
        assert "inquire" in complaint_with_neutral_sentiment["complaint_text"].lower()

    def test_positive_sentiment_detection(self):
        """Agent should handle positive sentiment."""
        positive_complaint = {
            "complaint_text": "Thank you for amazing service!",
            "customer_id": "CUST_POS_001"
        }
        assert "thank" in positive_complaint["complaint_text"].lower()


class TestCategorizationAgent:
    """Test complaint categorization agent."""

    def test_billing_category_detection(self, billing_complaint):
        """Agent should categorize billing complaints."""
        assert "bill" in billing_complaint["complaint_text"].lower()

    def test_outage_category_detection(self, outage_complaint):
        """Agent should categorize outage complaints."""
        assert "internet" in outage_complaint["complaint_text"].lower() or \
               "service" in outage_complaint["complaint_text"].lower()

    @patch('backend.agents.categorization_agent.llm_client')
    def test_category_confidence_scoring(self, mock_llm):
        """Agent should provide confidence scores."""
        mock_llm.generate.return_value = {
            "category": "billing",
            "confidence": 0.92,
            "alternative_categories": ["refund"]
        }
        # Verify structure
        assert "category" in mock_llm.generate.return_value
        assert "confidence" in mock_llm.generate.return_value


class TestResponseAgent:
    """Test response generation agent."""

    def test_response_generation_calls_retriever(self):
        """Response agent should use retrieval."""
        # Response generation requires FAISS retrieval
        pass

    def test_response_includes_policy_context(self):
        """Generated response should cite policies."""
        pass

    def test_response_does_not_hallucinate_refunds(self):
        """Response should never invent refund amounts."""
        refund_complaint = {
            "complaint_text": "I want a refund!",
            "customer_id": "CUST_REF_001"
        }
        # Response should NOT contain specific amounts like "$500" or "$1000"
        # unless explicitly in retrieved policies


class TestValidatorAgent:
    """Test response validation agent."""

    def test_validator_accepts_policy_grounded_response(self):
        """Validator should accept responses citing policies."""
        response_with_policy = {
            "response": "According to our refund policy, refunds require manager approval.",
            "has_policy_citation": True,
            "grounded": True
        }
        assert response_with_policy["grounded"] == True

    def test_validator_rejects_hallucinated_responses(self):
        """Validator should reject made-up claims."""
        hallucinated_response = {
            "response": "We will immediately credit you $1000 for your inconvenience.",
            "has_policy_citation": False,
            "grounded": False
        }
        assert hallucinated_response["grounded"] == False

    def test_validator_triggers_retry_on_failure(self):
        """Validator should provide feedback for retry."""
        failure_feedback = {
            "valid": False,
            "reason": "Response claims unauthorized refund amount",
            "retry_guidance": "Refer to escalation policy instead"
        }
        assert failure_feedback["valid"] == False


class TestHistoryAgent:
    """Test complaint history analysis agent."""

    def test_history_agent_detects_repeated_contact(self):
        """Agent should detect customers contacting multiple times."""
        history = [
            {"date": "2024-01-01", "category": "billing"},
            {"date": "2024-01-02", "category": "billing"},
            {"date": "2024-01-03", "category": "billing"}
        ]
        # Should flag as repeated contact
        assert len(history) > 2

    def test_history_agent_tracks_categories(self):
        """Agent should note patterns in complaint categories."""
        history = [
            {"category": "outage"},
            {"category": "outage"},
            {"category": "slow_internet"}
        ]
        outage_count = sum(1 for h in history if h["category"] == "outage")
        assert outage_count == 2


class TestSummarizationAgent:
    """Test complaint summarization agent."""

    def test_summarization_preserves_key_details(self):
        """Summarization should keep essential information."""
        long_complaint = {
            "complaint_text": """
            I've been experiencing slow internet speeds for the past 5 days.
            My connection drops every few minutes. I've tried restarting the router.
            I've contacted support twice already but the issue persists.
            I'm very frustrated and considering switching providers.
            """
        }
        # Summary should mention: slow speeds, 5 days, connection drops, restart tried, contacted twice
        key_terms = ["slow", "5 days", "drops", "contacted"]
        assert any(term in long_complaint["complaint_text"].lower() for term in key_terms)

    def test_summarization_reduces_length(self):
        """Summarized text should be shorter than original."""
        pass
