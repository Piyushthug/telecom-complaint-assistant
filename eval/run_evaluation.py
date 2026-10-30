"""Run AI evaluation against test dataset."""
import json
import sys
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List
import requests
from scoring import ResponseScorer, EvaluationReport, calculate_aggregate_metrics

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))


def load_test_dataset(dataset_path: str = None) -> Dict[str, Any]:
    """Load evaluation test dataset."""
    if dataset_path is None:
        dataset_path = Path(__file__).parent / "test_dataset.json"

    with open(dataset_path) as f:
        return json.load(f)


def call_api(complaint: Dict[str, Any], base_url: str = "http://localhost:8000") -> Dict[str, Any]:
    """Call complaint API endpoint."""
    try:
        response = requests.post(
            f"{base_url}/complaint",
            json=complaint,
            timeout=30
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        return {
            "error": str(e),
            "response": "Error processing complaint",
            "sentiment": "unknown",
            "category": "unknown"
        }


def evaluate_single_case(
    test_case: Dict[str, Any],
    api_response: Dict[str, Any]
) -> EvaluationReport:
    """Evaluate a single test case."""
    scorer = ResponseScorer()
    report = EvaluationReport(test_case["id"], test_case)

    # Extract expected values
    expected = test_case.get("expected", {})

    # Score sentiment detection
    if "sentiment" in api_response and "sentiment" in expected:
        metric = scorer.score_sentiment_detection(
            expected["sentiment"],
            api_response.get("sentiment", "unknown"),
            api_response.get("sentiment_confidence", 0.8)
        )
        report.add_metric(metric)

    # Score category detection
    if "category" in api_response and "category" in expected:
        metric = scorer.score_category_detection(
            expected["category"],
            api_response.get("category", "unknown"),
            api_response.get("category_confidence", 0.8)
        )
        report.add_metric(metric)

    # Get response text
    response_text = api_response.get("response", "")

    # Score policy citation
    if expected.get("response_requirements", {}).get("has_policy_citation", False):
        metric = scorer.score_policy_citation(response_text)
        report.add_metric(metric)

    # Score no hallucinated refund
    if expected.get("response_requirements", {}).get("no_specific_amount_promised", False):
        metric = scorer.score_no_hallucinated_refund(response_text)
        report.add_metric(metric)

    # Score acknowledgment
    if expected.get("response_requirements", {}).get("acknowledges_issue", False):
        metric = scorer.score_acknowledgment_of_issue(response_text)
        report.add_metric(metric)

    # Score escalation decision
    if "should_escalate" in expected and "escalated" in api_response:
        metric = scorer.score_escalation_decision(
            expected["should_escalate"],
            api_response.get("escalated", False)
        )
        report.add_metric(metric)

    # Score response quality metrics
    if response_text:
        report.add_metric(scorer.score_response_length(response_text))
        report.add_metric(scorer.score_next_steps(response_text))
        report.add_metric(scorer.score_tone(response_text))

    return report


def run_evaluation(
    dataset_path: str = None,
    api_url: str = "http://localhost:8000",
    output_file: str = None,
    verbose: bool = True
) -> Dict[str, Any]:
    """Run full evaluation suite."""

    # Load dataset
    print("Loading test dataset...")
    dataset = load_test_dataset(dataset_path)
    test_cases = dataset.get("test_cases", [])

    if not test_cases:
        print("ERROR: No test cases found in dataset")
        return {"error": "No test cases"}

    print(f"Loaded {len(test_cases)} test cases")

    # Check API is running
    try:
        requests.get(f"{api_url}/health", timeout=5)
        print(f"✓ API is running at {api_url}")
    except Exception as e:
        print(f"✗ Cannot reach API at {api_url}: {e}")
        print("Make sure the backend is running with: python -m uvicorn backend.main:app --reload")
        return {"error": f"API not available: {e}"}

    # Run evaluations
    reports: List[EvaluationReport] = []
    failed_cases = []

    for i, test_case in enumerate(test_cases, 1):
        print(f"\n[{i}/{len(test_cases)}] Evaluating: {test_case['id']}")

        # Call API
        complaint = {
            "complaint_text": test_case["complaint_text"],
            "customer_id": test_case["customer_id"],
            "channel": test_case.get("channel", "chat")
        }

        if verbose:
            print(f"  Complaint: {complaint['complaint_text'][:80]}...")

        api_response = call_api(complaint, api_url)

        if "error" in api_response:
            print(f"  ✗ API Error: {api_response['error']}")
            failed_cases.append(test_case["id"])
            continue

        # Evaluate
        report = evaluate_single_case(test_case, api_response)
        reports.append(report)

        # Print results
        score = report.get_overall_score()
        status = "✓" if score >= 0.8 else "⚠" if score >= 0.6 else "✗"
        print(f"  {status} Score: {score:.2f}")

        if report.get_failed_metrics():
            for metric in report.get_failed_metrics():
                print(f"    - {metric.name}: {metric.reason}")

    # Generate report
    print("\n" + "=" * 80)
    print("EVALUATION SUMMARY")
    print("=" * 80)

    if reports:
        aggregate = calculate_aggregate_metrics(reports)

        print(f"Test Cases Evaluated: {aggregate['num_test_cases']}")
        print(f"Average Score: {aggregate['average_score']:.2%}")
        print(f"Min Score: {aggregate['min_score']:.2%}")
        print(f"Max Score: {aggregate['max_score']:.2%}")
        print(f"Critical Failures: {aggregate['critical_failures']}")

        print("\nPer-Metric Averages:")
        for metric_name, avg_score in sorted(aggregate['metric_averages'].items()):
            print(f"  {metric_name}: {avg_score:.2%}")

    if failed_cases:
        print(f"\nFailed Cases: {', '.join(failed_cases)}")

    # Save detailed report
    if output_file is None:
        output_file = Path(__file__).parent / f"evaluation_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

    detailed_report = {
        "metadata": {
            "timestamp": datetime.now().isoformat(),
            "api_url": api_url,
            "num_test_cases": len(test_cases),
            "num_evaluated": len(reports),
            "num_failed": len(failed_cases)
        },
        "aggregate_metrics": calculate_aggregate_metrics(reports) if reports else {},
        "individual_reports": [r.to_dict() for r in reports],
        "failed_cases": failed_cases
    }

    with open(output_file, "w") as f:
        json.dump(detailed_report, f, indent=2)

    print(f"\nDetailed report saved to: {output_file}")

    return detailed_report


if __name__ == "__main__":
    # Allow customization via command-line args
    api_url = os.getenv("API_URL", "http://localhost:8000")
    dataset_path = os.getenv("DATASET_PATH", None)
    output_file = os.getenv("REPORT_OUTPUT", None)

    results = run_evaluation(
        dataset_path=dataset_path,
        api_url=api_url,
        output_file=output_file,
        verbose=True
    )

    # Exit with non-zero code if evaluation failed
    if "error" in results:
        sys.exit(1)

    # Exit with non-zero code if critical failures
    if results.get("aggregate_metrics", {}).get("critical_failures", 0) > 0:
        sys.exit(1)

    sys.exit(0)
