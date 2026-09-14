import argparse
import csv
import json
import random
from datetime import datetime, timedelta
from pathlib import Path


CATEGORIES = [
    "INTERNET_OUTAGE",
    "SLOW_INTERNET",
    "BILLING",
    "REFUND",
    "CUSTOMER_SERVICE",
]

SENTIMENTS = [
    "POSITIVE",
    "NEUTRAL",
    "NEGATIVE",
    "VERY_NEGATIVE",
]

CHANNELS = [
    "CHAT",
    "EMAIL",
    "PHONE",
    "WEB",
]


COMPLAINT_TEMPLATES = {
    "INTERNET_OUTAGE": [
        "My internet has been completely down since this morning.",
        "I have no internet connection at home.",
        "My router is connected but there is no internet.",
        "The internet stopped working suddenly.",
        "I cannot access any websites because my internet is down.",
    ],
    "SLOW_INTERNET": [
        "My internet is extremely slow today.",
        "The connection works but the speed is very poor.",
        "My internet speed has become much slower than usual.",
        "Videos keep buffering even though my connection is active.",
        "The internet is working but everything loads very slowly.",
    ],
    "BILLING": [
        "I was charged twice for the same service.",
        "My latest bill is higher than expected.",
        "There is an incorrect charge on my bill.",
        "I do not understand this extra charge on my account.",
        "My bill contains a charge that I did not expect.",
    ],
    "REFUND": [
        "I would like a refund for this charge.",
        "Can I get my money back for the service?",
        "I want to request a refund.",
        "Please help me with a refund for my recent payment.",
        "I believe I should receive a refund for this charge.",
    ],
    "CUSTOMER_SERVICE": [
        "I have already contacted support but my issue is still unresolved.",
        "The support team did not resolve my problem.",
        "I am unhappy with the customer service I received.",
        "I have contacted customer support multiple times.",
        "I need help because my previous support request was not resolved.",
    ],
}


SENTIMENT_PREFIXES = {
    "POSITIVE": [
        "Thanks for your help. ",
        "I appreciate the support. ",
    ],
    "NEUTRAL": [
        "",
        "I need some help. ",
    ],
    "NEGATIVE": [
        "I am frustrated. ",
        "This is very disappointing. ",
        "I am unhappy about this. ",
    ],
    "VERY_NEGATIVE": [
        "I am extremely frustrated and upset. ",
        "This has been a terrible experience. ",
        "I am very unhappy with this situation. ",
    ],
}


STATUSES = [
    "OPEN",
    "IN_PROGRESS",
    "RESOLVED",
    "ESCALATED",
]


def generate_complaint(
    complaint_id: str,
    customer_id: str,
    created_at: datetime,
) -> dict:
    """
    Generate one synthetic customer complaint.
    """

    category = random.choice(CATEGORIES)
    sentiment = random.choice(SENTIMENTS)
    channel = random.choice(CHANNELS)

    prefix = random.choice(SENTIMENT_PREFIXES[sentiment])
    complaint_text = random.choice(COMPLAINT_TEMPLATES[category])

    complaint = prefix + complaint_text

    return {
        "complaint_id": complaint_id,
        "customer_id": customer_id,
        "complaint": complaint,
        "category": category,
        "sentiment": sentiment,
        "channel": channel,
        "created_at": created_at.isoformat(timespec="seconds"),
    }


def generate_complaints(count: int, seed: int) -> list:
    """
    Generate synthetic complaint records.
    """

    random.seed(seed)

    complaints = []

    start_date = datetime.now() - timedelta(days=180)

    for i in range(1, count + 1):
        complaint_id = f"CMP{i:04d}"

        customer_id = f"CUST{random.randint(1, 80):04d}"

        created_at = start_date + timedelta(
            minutes=random.randint(0, 180 * 24 * 60)
        )

        complaint = generate_complaint(
            complaint_id,
            customer_id,
            created_at,
        )

        complaints.append(complaint)

    return complaints


def generate_history(complaints: list, seed: int) -> list:
    """
    Generate historical complaint records.

    Some customers intentionally receive multiple complaints
    so that repeated-contact / escalation scenarios can be tested.
    """

    random.seed(seed)

    history = []

    for complaint in complaints:
        status = random.choice(STATUSES)

        resolution_time_hours = None

        if status == "RESOLVED":
            resolution_time_hours = round(
                random.uniform(1, 72),
                2,
            )

        history.append(
            {
                "complaint_id": complaint["complaint_id"],
                "customer_id": complaint["customer_id"],
                "category": complaint["category"],
                "status": status,
                "created_at": complaint["created_at"],
                "resolution_time_hours": resolution_time_hours,
            }
        )

    return history


def add_demo_repeated_contacts(
    complaints: list,
    history: list,
):
    """
    Add deterministic repeated-contact examples.

    These are useful for testing escalation logic.
    """

    demo_customers = {
        "C0001": "INTERNET_OUTAGE",
        "C0002": "SLOW_INTERNET",
        "C0003": "BILLING",
    }

    base_date = datetime.now() - timedelta(days=10)

    next_id = len(complaints) + 1

    for customer_id, category in demo_customers.items():

        for contact_number in range(1, 4):

            complaint_id = f"CMP{next_id:04d}"

            created_at = base_date + timedelta(
                days=contact_number
            )

            complaint_text = random.choice(
                COMPLAINT_TEMPLATES[category]
            )

            complaint = {
                "complaint_id": complaint_id,
                "customer_id": customer_id,
                "complaint": complaint_text,
                "category": category,
                "sentiment": "NEGATIVE",
                "channel": "CHAT",
                "created_at": created_at.isoformat(
                    timespec="seconds"
                ),
            }

            complaints.append(complaint)

            history.append(
                {
                    "complaint_id": complaint_id,
                    "customer_id": customer_id,
                    "category": category,
                    "status": (
                        "ESCALATED"
                        if contact_number == 3
                        else "OPEN"
                    ),
                    "created_at": created_at.isoformat(
                        timespec="seconds"
                    ),
                    "resolution_time_hours": None,
                }
            )

            next_id += 1


def save_json(data: list, output_path: Path):
    """
    Save records to JSON.
    """

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with output_path.open(
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            data,
            file,
            indent=2,
            ensure_ascii=False,
        )


def save_csv(data: list, output_path: Path):
    """
    Save records to CSV.
    """

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    if not data:
        return

    fieldnames = list(data[0].keys())

    with output_path.open(
        "w",
        newline="",
        encoding="utf-8",
    ) as file:

        writer = csv.DictWriter(
            file,
            fieldnames=fieldnames,
        )

        writer.writeheader()
        writer.writerows(data)


def main():
    parser = argparse.ArgumentParser(
        description=(
            "Generate synthetic telecom complaint "
            "and complaint-history datasets."
        )
    )

    parser.add_argument(
        "--complaints",
        type=int,
        default=200,
        help="Number of synthetic complaints to generate.",
    )

    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for reproducible data.",
    )

    parser.add_argument(
        "--output-dir",
        type=str,
        default="data",
        help="Directory where generated files are saved.",
    )

    args = parser.parse_args()

    output_dir = Path(args.output_dir)

    # Generate complaints
    complaints = generate_complaints(
        count=args.complaints,
        seed=args.seed,
    )

    # Generate history
    history = generate_history(
        complaints=complaints,
        seed=args.seed,
    )

    # Add deterministic repeated-contact customers
    add_demo_repeated_contacts(
        complaints=complaints,
        history=history,
    )

    # Save complaints JSON
    complaints_path = (
        output_dir / "complaints.json"
    )

    save_json(
        complaints,
        complaints_path,
    )

    # Save complaint history CSV
    history_path = (
        output_dir / "complaint_history.csv"
    )

    save_csv(
        history,
        history_path,
    )

    print(
        f"Generated {len(complaints)} complaints."
    )

    print(
        f"Generated {len(history)} history records."
    )

    print(
        f"Complaints saved to: {complaints_path}"
    )

    print(
        f"History saved to: {history_path}"
    )


if __name__ == "__main__":
    main()