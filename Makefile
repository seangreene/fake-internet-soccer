# Update the league charts by running the season notebooks.
#
#   make update                 # standings + head-to-head for the current season
#   make update LATEST_GW=10    # force a gameweek instead of auto-detecting it
#   make standings / make scores
#   make update SEASON=15       # an older season's notebooks
#
# Needs a Datawrapper token in .env or DATAWRAPPER_API_TOKEN (see _workspace/dw_helpers.py).
# Executed copies of the notebooks go to _workspace/runs/ (git-ignored), so the
# notebooks you edit in Jupyter are never touched.

SEASON ?= 16
WORKSPACE := _workspace
RUNS := $(WORKSPACE)/runs
NBCONVERT := jupyter nbconvert --to notebook --execute \
	--ExecutePreprocessor.timeout=900 --ExecutePreprocessor.kernel_name=python3 \
	--output-dir $(RUNS)

export LATEST_GW

.PHONY: update standings scores install

update: standings scores

standings:
	$(NBCONVERT) $(WORKSPACE)/standings-$(SEASON).ipynb

scores:
	$(NBCONVERT) $(WORKSPACE)/scores-$(SEASON).ipynb

install:
	pip install -r $(WORKSPACE)/requirements.txt
