# Cause-specific mortality results

See [PROOF.md](PROOF.md) for claim labels, prior art, and checks.

Reproduce:

```
pip install -r requirements.txt
python3 pilot/fetch.py && python3 pilot/refit.py && make verify
```

Summary output is in `summary.txt`; machine-readable aggregates in `certificate.json`.
