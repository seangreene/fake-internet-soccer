import { json } from 'd3-fetch';
import { renderSvelteComponent } from './utils/render.js';
import BumpChart from './components/BumpChart.svelte';

async function main() {
  // the first parameter should be the path to the file
  // the second parameter *must* be “import.meta.url”
  // const url = new URL('../_data/standings-xii.json', import.meta.url);
  // // Call it in
  // const data = await json(url);
  // const chartContainer = document.getElementById('bump');
  // renderSvelteComponent(BumpChart, chartContainer, { data: data });
}
main().catch(console.error);
