// datawrapper render function
export let renderDatawrapper = function (el, chartId, version) {
  let chartDataUrl = `https://datawrapper.dwcdn.net/${chartId}/${version}/embed.json`;
  const target = document.createElement('div');
  el.innerHTML = '';
  el.appendChild(target);
  fetch(chartDataUrl)
    .then((res) => res.json())
    .then((embedData) => {
      // then pass it to datawrapper.render call, along with { target, flags }
      datawrapper.render(embedData, {
        // the node that will be turned into the web component
        target,
        // optionally include flags (e.g dark, fitchart) here
        // see https://developer.datawrapper.de/docs/render-flags
        flags: {},
      });
    });
};
