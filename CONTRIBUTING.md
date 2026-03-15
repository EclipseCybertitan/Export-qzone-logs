# Contributing

## Development setup

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e .
```

## Run tests

```bash
python -m unittest discover -s tests -p "test_*.py"
```

## Contribution guidelines

- Keep changes focused.
- Add or update tests for behavior changes.
- Never include real cookies, UINs, export outputs, or personal data in commits.
