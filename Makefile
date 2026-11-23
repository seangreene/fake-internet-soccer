# Update the league charts by running the season notebooks.
#
#   make update                 # standings + head-to-head for the newest season in _workspace/seasons.json
#   make update LATEST_GW=10    # force a gameweek instead of auto-detecting it
#   make standings / make scores
#   make update SEASON=16       # a specific season
#   make recolor                # re-apply team-colors.json to every season's line chart and republish
#
# New season: add its Fantrax league ID to _workspace/seasons.json. The first run
# copies last season's Datawrapper charts and adds them to _data/charts.json.
#
# Needs a Datawrapper token in .env or DATAWRAPPER_API_TOKEN (see _workspace/dw_helpers.py).
# Executed copies of the notebooks go to _workspace/runs/ (git-ignored), so the
# notebooks you edit in Jupyter are never touched.

# Whichever Python you run notebooks with; `make install` puts the packages there.
# e.g. `make update PYTHON=/path/to/python`
PYTHON ?= python3
WORKSPACE := _workspace
RUNS := $(WORKSPACE)/runs
# The kernel talks to nbconvert over local Unix sockets (ipc) in $(RUNS) instead of
# unencrypted TCP, which also silences the "running over TCP without encryption" warning.
# The socket path must be absolute: the kernel runs from the notebook's folder, not here.
NBCONVERT := $(PYTHON) -m jupyter nbconvert --to notebook --execute \
	--ExecutePreprocessor.timeout=900 --ExecutePreprocessor.kernel_name=python3 \
	--KernelManager.transport=ipc --KernelManager.ip=$(abspath $(RUNS))/kernel \
	--output-dir $(RUNS)

export LATEST_GW SEASON

.PHONY: update standings scores recolor install

update: standings scores

standings:
	@mkdir -p $(RUNS)
	$(NBCONVERT) $(WORKSPACE)/standings.ipynb

scores:
	@mkdir -p $(RUNS)
	$(NBCONVERT) $(WORKSPACE)/scores.ipynb

recolor:
	cd $(WORKSPACE) && $(PYTHON) recolor_charts.py

install:
	$(PYTHON) -m pip install -r $(WORKSPACE)/requirements.txt
