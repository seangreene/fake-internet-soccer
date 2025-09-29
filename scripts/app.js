import { renderDatawrapper } from './components/datawrapper';

async function main() {
  // season selector dropdown
  const select = document.getElementById('season-select');

  // Dropdown change event
  select.addEventListener('change', function () {
    renderDatawrapper(bumpChartContainer, this.value);
  });

  // render bump chart ("Race to the bottom")
  let bumpChartContainer = document.getElementById('bump-chart');
  renderDatawrapper(bumpChartContainer, 'b7v86');
}
main().catch(console.error);
