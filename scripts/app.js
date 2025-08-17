async function main() {
  const iframe = document.getElementById('datawrapper-frame');
  const select = document.getElementById('season-select');

  // Dropdown change event
  select.addEventListener('change', function () {
    switchChart(this.value);
  });

  // Function to switch the chart
  window.switchChart = function (chartId) {
    iframe.src = `https://datawrapper.dwcdn.net/${chartId}/1/`;
  };

  // Listen for Datawrapper iframe height messages
  window.addEventListener('message', function (e) {
    if (
      e.origin.includes('datawrapper.dwcdn.net') &&
      e.data['datawrapper-height']
    ) {
      iframe.style.height =
        Object.values(e.data['datawrapper-height'])[0] + 'px';
    }
  });
}
main().catch(console.error);
