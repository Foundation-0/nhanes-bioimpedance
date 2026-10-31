OPENBLAS_NUM_THREADS=1
OMP_NUM_THREADS=1
MKL_NUM_THREADS=1

.PHONY: verify verify-fast verify-cause-specific-mortality certificates

verify: verify-cause-specific-mortality

verify-fast: verify-cause-specific-mortality

verify-cause-specific-mortality:
	OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 \
	  python3 results/cause-specific-mortality/verify.py

certificates:
	OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 \
	  python3 pilot/cause_mortality.py
	@sha256sum results/cause-specific-mortality/certificate.json > certificates/SHA256SUMS
