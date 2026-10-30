"""AI evaluation scoring functions."""
import re
from typing import Dict, List, Any
from dataclasses import dataclass


@dataclass
class EvaluationMetric:
    """Single evaluation metric result."""
    name: str
    score: float  # 0-1
    passed: bool
    reason: str
    severity: str  # "critical", "high", "medium", "low"


class ResponseScorer:
    """Score agent responses against evaluation criteria."""

    def __init__(self):
        self.metrics = []

    def score_sentiment_detection(
        self,
        expected_sentiment: str,
        actual_sentiment: str,
        confidence: float = None
    ) -> EvaluationMetric:
        """Score sentiment detection accuracy."""
        passed = expected_sentiment.lower() == actual_sentiment.lower()
        score = 1.0 if passed else 0.0

        if confidence:
            # Adjust score based on confidence
            score *= confidence

        return EvaluationMetric(
            name="sentiment_detection",
            score=score,
            passed=passed,
            reason=f"Expected: {expected_sentiment}, Got: {actual_sentiment}",
            severity="high"
        )

    def score_category_detection(
        self,
        expected_category: str,
        actual_category: str,
        confidence: float = None
    ) -> EvaluationMetric:
        """Score complaint category detection."""
        passed = expected_category.lower() == actual_category.lower()
        score = 1.0 if passed else 0.0

        if confidence:
            score *= confidence

        return EvaluationMetric(
            name="category_detection",
            score=score,
            passed=passed,
            reason=f"Expected: {expected_category}, Got: {actual_category}",
            severity="high"
        )

    def score_policy_citation(self, response: str) -> EvaluationMetric:
        """Check if response cites policy."""
        has_policy_keywords = any(kw in response.lower() for kw in [
            "policy", "according to", "our policy", "company policy",
            "terms and conditions", "agreement"
        ])

        return EvaluationMetric(
            name="policy_citation",
            score=1.0 if has_policy_keywords else 0.0,
            passed=has_policy_keywords,
            reason="Response should cite relevant policy" if not has_policy_keywords else "Policy cited",
            severity="critical"
        )

    def score_no_hallucinated_refund(self, response: str) -> EvaluationMetric:
        """Ensure response doesn't promise unauthorized refunds."""
        # Look for patterns like "$XXX refund", "refund you $", etc.
        refund_patterns = [
            r'\$\d+.*refund',
            r'refund.*\$\d+',
            r'credit.*\$\d+',
            r'give you.*\$\d+',
            r'we will.*\$\d+'
        ]

        has_hallucinated_refund = any(
            re.search(pattern, response, re.IGNORECASE)
            for pattern in refund_patterns
        )

        return EvaluationMetric(
            name="no_hallucinated_refund",
            score=0.0 if has_hallucinated_refund else 1.0,
            passed=not has_hallucinated_refund,
            reason="Response should not promise specific refund amounts" if has_hallucinated_refund else "No unauthorized refund promised",
            severity="critical"
        )

    def score_acknowledgment_of_issue(self, response: str) -> EvaluationMetric:
        """Check if response acknowledges the customer's issue."""
        ack_keywords = [
            "understand", "sorry", "apologize", "frustrating", "acknowledge",
            "thank you for", "we understand", "appreciate", "recognize"
        ]

        acknowledges = any(kw in response.lower() for kw in ack_keywords)

        return EvaluationMetric(
            name="acknowledgment",
            score=1.0 if acknowledges else 0.5,
            passed=acknowledges,
            reason="Response should acknowledge customer's concern" if not acknowledges else "Issue acknowledged",
            severity="high"
        )

    def score_escalation_decision(
        self,
        expected_escalate: bool,
        actual_escalate: bool
    ) -> EvaluationMetric:
        """Score escalation decision correctness."""
        passed = expected_escalate == actual_escalate

        return EvaluationMetric(
            name="escalation_decision",
            score=1.0 if passed else 0.0,
            passed=passed,
            reason=f"Expected escalate={expected_escalate}, Got escalate={actual_escalate}",
            severity="high"
        )

    def score_response_length(self, response: str) -> EvaluationMetric:
        """Check response length is reasonable."""
        length = len(response.split())

        # Reasonable response: 30-500 words
        if length < 20:
            return EvaluationMetric(
                name="response_length",
                score=0.5,
                passed=False,
                reason=f"Response too short ({length} words)",
                severity="medium"
            )
        elif length > 1000:
            return EvaluationMetric(
                name="response_length",
                score=0.7,
                passed=False,
                reason=f"Response too long ({length} words)",
                severity="low"
            )
        else:
            return EvaluationMetric(
                name="response_length",
                score=1.0,
                passed=True,
                reason=f"Response length appropriate ({length} words)",
                severity="low"
            )

    def score_next_steps(self, response: str) -> EvaluationMetric:
        """Check if response provides clear next steps."""
        next_step_keywords = [
            "next", "will", "can", "should", "steps",
            "call", "visit", "contact", "proceed", "follow"
        ]

        has_next_steps = any(kw in response.lower() for kw in next_step_keywords)

        return EvaluationMetric(
            name="next_steps",
            score=1.0 if has_next_steps else 0.5,
            passed=has_next_steps,
            reason="Response should outline next steps" if not has_next_steps else "Next steps provided",
            severity="high"
        )

    def score_tone(self, response: str, expected_tone: str = "professional") -> EvaluationMetric:
        """Evaluate response tone."""
        response_lower = response.lower()

        # Check for negative indicators
        negative_words = ["no", "can't", "won't", "unable", "impossible", "refuse"]
        harsh_words = ["stupid", "idiot", "wrong", "you're wrong"]

        has_harsh = any(word in response_lower for word in harsh_words)

        if has_harsh:
            return EvaluationMetric(
                name="tone",
                score=0.0,
                passed=False,
                reason="Response contains inappropriate language",
                severity="critical"
            )

        # Check for professional indicators
        professional_words = ["we", "help", "assist", "happy", "will", "can help"]
        has_professional = any(word in response_lower for word in professional_words)

        score = 1.0 if has_professional else 0.6

        return EvaluationMetric(
            name="tone",
            score=score,
            passed=score > 0.7,
            reason="Tone is professional and helpful" if score > 0.7 else "Tone could be improved",
            severity="high"
        )


class EvaluationReport:
    """Generate evaluation report from metrics."""

    def __init__(self, test_case_id: str, complaint: Dict[str, Any]):
        self.test_case_id = test_case_id
        self.complaint = complaint
        self.metrics: List[EvaluationMetric] = []
        self.start_time = None
        self.end_time = None

    def add_metric(self, metric: EvaluationMetric):
        """Add evaluation metric."""
        self.metrics.append(metric)

    def get_overall_score(self) -> float:
        """Calculate overall score as weighted average."""
        if not self.metrics:
            return 0.0

        # Weight critical metrics higher
        weights = {
            "critical": 3.0,
            "high": 2.0,
            "medium": 1.0,
            "low": 0.5
        }

        total_weight = 0
        weighted_sum = 0

        for metric in self.metrics:
            weight = weights.get(metric.severity, 1.0)
            weighted_sum += metric.score * weight
            total_weight += weight

        return weighted_sum / total_weight if total_weight > 0 else 0.0

    def get_passed_metrics(self) -> List[EvaluationMetric]:
        """Get metrics that passed."""
        return [m for m in self.metrics if m.passed]

    def get_failed_metrics(self) -> List[EvaluationMetric]:
        """Get metrics that failed."""
        return [m for m in self.metrics if not m.passed]

    def to_dict(self) -> Dict[str, Any]:
        """Convert report to dictionary."""
        return {
            "test_case_id": self.test_case_id,
            "complaint_text": self.complaint.get("complaint_text", ""),
            "overall_score": self.get_overall_score(),
            "num_metrics": len(self.metrics),
            "passed": len(self.get_passed_metrics()),
            "failed": len(self.get_failed_metrics()),
            "metrics": [
                {
                    "name": m.name,
                    "score": m.score,
                    "passed": m.passed,
                    "reason": m.reason,
                    "severity": m.severity
                }
                for m in self.metrics
            ]
        }


def calculate_aggregate_metrics(reports: List[EvaluationReport]) -> Dict[str, Any]:
    """Calculate aggregate metrics across all test cases."""
    if not reports:
        return {}

    overall_scores = [r.get_overall_score() for r in reports]

    # Group by metric name
    metric_scores = {}
    for report in reports:
        for metric in report.metrics:
            if metric.name not in metric_scores:
                metric_scores[metric.name] = []
            metric_scores[metric.name].append(metric.score)

    # Calculate per-metric averages
    metric_averages = {
        name: sum(scores) / len(scores)
        for name, scores in metric_scores.items()
    }

    return {
        "num_test_cases": len(reports),
        "average_score": sum(overall_scores) / len(overall_scores),
        "min_score": min(overall_scores),
        "max_score": max(overall_scores),
        "metric_averages": metric_averages,
        "critical_failures": sum(
            1 for r in reports
            for m in r.get_failed_metrics()
            if m.severity == "critical"
        )
    }
