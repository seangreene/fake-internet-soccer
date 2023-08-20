<script>
    import { LayerCake, Svg, Html, flatten, groupLonger } from 'layercake';
    import { extent, max } from 'd3-array';
    import { axisBottom, axisLeft } from 'd3-axis';
    import { scaleLinear, scaleBand } from 'd3-scale';
    import { line as lineShape, curveStep } from 'd3-shape';

    export let data;
     
    // Dimensions
    let width;
    let height = 300;
    let margin = { top: 20, right: 10, bottom: 35, left: 25 };

    // eventual toggle between rank and points
    $: selectedAttr = 'rank';

    $: chartData = data.map((d) => ({
        gw: d.gw,
        team: d.team,
        points: d.points,
        rank: d.rank,
    }));

	const xKey = 'gw';
	const yKey = selectedAttr;
	const zKey = 'team';

	const seriesNames = Object.keys(data[0]).filter(d => d !== xKey);
	const seriesColors = ['#ffe4b8', '#ffb3c0', '#ff7ac7', '#ff00cc'];    

    $: data.forEach(d => {
        d[xKey] = typeof d[xKey] === 'string'
        ? xKeyCast(d[xKey])
        : d[xKey];

        seriesNames.forEach(team => {
        d[team] = +d[team];
        });
    });

    $: groupedData = groupLonger(chartData, seriesNames, {
        groupTo: zKey,
        valueTo: yKey
    });

    $: console.log(groupedData)

    // Scales
    $: xRange = chartData.map((d) => d.gw);
    $: xScale = scaleBand()
        .domain(xRange)
        .range([0, width - margin.left - margin.right])
        .padding(0);
    $: bandwidth = xScale.bandwidth() - 2;

    $: yScaleType = selectedAttr.yScaleType || scaleLinear;
    $: yMin = selectedAttr.yMin || 0;
    $: yMax = max(chartData, (d) => Math.max(d.rank))
    $: yScale = yScaleType()
        .domain([yMin, yMax])
        .nice()
        .range([height - margin.top - margin.bottom, 0]);
    $: y0 = yScale(yMin);

    // Shapes
    $: drawLine = lineShape()
    .x((d) => xScale(d.gw) + bandwidth / 2)
        .y((d) => yScale(d.rank))
        .curve(curveStep);

</script>
<div class="chart">
   <h2>Hello chart</h2>
   <div class="chart-inner" bind:clientWidth={width}>
        <svg {width} {height}>
            <g class="line-group">
                {#each groupedData as group}
                    <path
                        class='path-line'
                        d='{group[0]}'
                        stroke="1"
                    ></path>
                {/each}
            </g>
            <!-- <g class="average-line">
                <path
                  stroke="black"
                  stroke-width="3"
                  stroke-linejoin="round"
                  stroke-linecap="round"
                  fill="none"
                  d={drawLine(chartData)}
                />
              </g>             -->
        </svg>
    </div>
</div>