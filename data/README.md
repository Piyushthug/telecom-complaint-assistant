# Synthetic Data

This directory contains synthetic telecom complaint data for the local demo.

## Files

- `complaints.json` — current customer complaints with synthetic labels.
- `complaint_history.csv` — previous complaint records used to demonstrate repeated-contact logic.

## Regenerate

From the project root:

```bash
python scripts/generate_synthetic_data.py
```

Generate a larger dataset:

```bash
python scripts/generate_synthetic_data.py --complaints 500 --seed 42
```

All data is synthetic and contains no real customer information.
