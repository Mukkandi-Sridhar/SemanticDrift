# Common tasks. The experiment itself needs API keys; see research/RUNBOOK.md.
PY ?= python3
AOB_COMMIT = 0d044061ab3ffd4b213ddf6a0868c360d7e9667c

.PHONY: vendor check test validate figures analysis

vendor:            ## fetch AssetOpsBench at the pinned commit (needed by the validator)
	@test -d vendor/AssetOpsBench || git clone https://github.com/IBM/AssetOpsBench vendor/AssetOpsBench
	git -C vendor/AssetOpsBench checkout -q $(AOB_COMMIT)

validate: vendor   ## check every dataset file against datasets/MANIFEST.json
	$(PY) -I src/semdrift/validate_dataset.py

test:              ## run the test suite
	PYTHONPATH=src $(PY) -m unittest discover -s tests

check: validate test

figures:           ## redraw figures/ from results/ (needs matplotlib)
	$(PY) src/semdrift/figures.py

analysis:          ## recompute results/analysis from the raw run (needs results/raw/main)
	PYTHONPATH=src $(PY) -m semdrift.cli analyze --config configs/main.toml
