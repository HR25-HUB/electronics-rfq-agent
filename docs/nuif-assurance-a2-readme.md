# NUIF-SDD-ASSURANCE-001.A2
This is an isolated, draft-stage Design Assurance addition to the RFQ repository.

## Local
```powershell
uv pip install --system 'pydantic>=2.7,<3' 'pytest>=8,<10' 'ruff>=0.9' 'mypy>=1.10'
python -m pytest -q tests/test_design_assurance.py
python -m assurance.eval_cli evals/nuif_assurance_synthetic.json
ruff check assurance tests/test_design_assurance.py
ruff format --check assurance tests/test_design_assurance.py
mypy assurance --ignore-missing-imports
```

The dataset is synthetic. The reference classifier is not connected to QuoteAgent. The approval job deliberately fails when human and independent review evidence is absent. No auto-generated evidence.json is allowed; reviews must be attested by actual distinct sessions and bound to artifact SHA-256 and commit SHA.
