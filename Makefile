OPENBLAS_NUM_THREADS=1
OMP_NUM_THREADS=1
MKL_NUM_THREADS=1

.PHONY: verify verify-fast verify-pilot-2026-10-31 verify-outcomes-2026-10-31 verify-cause-specific-mortality certificates participant-guard

verify: verify-pilot-2026-10-31 verify-outcomes-2026-10-31 verify-cause-specific-mortality participant-guard

verify-fast: verify

verify-pilot-2026-10-31:
	OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 \
	  python3 results/pilot-2026-10-31/verify.py

verify-outcomes-2026-10-31:
	OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 \
	  python3 results/outcomes-2026-10-31/verify.py

verify-cause-specific-mortality:
	OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 \
	  python3 results/cause-specific-mortality/verify.py

participant-guard:
	python3 scripts/check_no_participant_data.py

certificates:
	OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 \
	  python3 results/pilot-2026-10-31/verify.py
	OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 \
	  python3 results/outcomes-2026-10-31/verify.py
	OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 \
	  python3 pilot/cause_mortality.py
	@sha256sum results/pilot-2026-10-31/certificate.json results/outcomes-2026-10-31/certificate.json results/cause-specific-mortality/certificate.json > certificates/SHA256SUMS
