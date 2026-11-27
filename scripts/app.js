import { renderDatawrapper } from './components/datawrapper';

async function main() {

  const chartsMetadata = document.getElementById('chartsMetadata');
  const chartsMetadataParsed = JSON.parse(chartsMetadata.textContent);

  // latest published versions looked up at build time by
  // _workspace/datawrapper-versions.mjs; these win over charts.json
  const versionsEl = document.getElementById('datawrapperVersions');
  const latestVersions = versionsEl ? JSON.parse(versionsEl.textContent) : {};

  const latestSeason = Math.max(
    ...Object.keys(chartsMetadataParsed).map(Number)
  );

  // season selector dropdown
  const select = document.getElementById('season-select');

  function getChartInfo(s, type) {
    let chartId = chartsMetadataParsed[s][type]['chart_id'];
    let version = latestVersions[chartId] || chartsMetadataParsed[s][type]['version'];
    return [chartId, version];
  }

  let [bumpChartId, bumpChartVersion] = getChartInfo(latestSeason, 'standings');
  let [h2hChartId, h2hpChartVersion] = getChartInfo(latestSeason, 'h2h');

  // Dropdown change event
  select.addEventListener('change', function () {
    let selectedSeason = select.value;

    // re-render bump chart
    let updatedBumpChartInfo = getChartInfo(selectedSeason, 'standings');
    renderDatawrapper(
      bumpChartContainer,
      updatedBumpChartInfo[0],
      updatedBumpChartInfo[1]
    );

    // re-render h2h chart
    let updatedH2hChartInfo = getChartInfo(selectedSeason, 'h2h');
    renderDatawrapper(
      h2hChartContainer,
      updatedH2hChartInfo[0],
      updatedH2hChartInfo[1]
    );

    // form is only for the current season
    setFormVisible(Number(selectedSeason) === latestSeason);
  });

  // render bump chart ("Race to the bottom")
  let bumpChartContainer = document.getElementById('bump-chart');
  renderDatawrapper(bumpChartContainer, bumpChartId, bumpChartVersion);

  // render h2h chart
  let h2hChartContainer = document.getElementById('h2h-chart');
  renderDatawrapper(h2hChartContainer, h2hChartId, h2hpChartVersion);

  // Current-season section: form table + thumpings. Each is one Datawrapper chart that
  // the scores notebook overwrites every run (_data/form.json, _data/thumpings.json).
  const formChartContainer = document.getElementById('form-chart');
  const thumpingsChartContainer = document.getElementById('thumpings-chart');

  // hide the whole section: its .chart wrapper and the spacer above it
  const formSection = formChartContainer.closest('.chart');
  const setFormVisible = (visible) => {
    formSection.hidden = !visible;
    formSection.previousElementSibling.hidden = !visible;
  };

  // chart ID + newest version for a single-chart metadata block, or null
  function getSingleChart(metadataId) {
    const el = document.getElementById(metadataId);
    const meta = el ? JSON.parse(el.textContent) : null;
    const version = meta && (latestVersions[meta.chart_id] || meta.version);
    return version ? [meta.chart_id, version] : null;
  }

  const formChart = getSingleChart('formMetadata');
  const thumpingsChart = getSingleChart('thumpingsMetadata');

  if (formChart) renderDatawrapper(formChartContainer, ...formChart);
  if (thumpingsChart) renderDatawrapper(thumpingsChartContainer, ...thumpingsChart);
  if (!formChart && !thumpingsChart) setFormVisible(false);
}
main().catch(console.error);
