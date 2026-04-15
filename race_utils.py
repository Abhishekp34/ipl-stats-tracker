import streamlit.components.v1 as components
import json

def d3_bar_chart_race(df, metric_col, category):
    # Prepare data for JS: Sort by match and then rank
    # We only need the Top 10 for each match to keep the JS payload light
    data_json = df.to_json(orient='records')
    
    # Custom Javascript with D3.js logic
    # This handles the physical sliding and swapping of bars
    custom_js = f"""
    <div id="d3-race-container" style="background: transparent;"></div>
    <script src="https://d3js.org/d3.v6.min.js"></script>
    <script>
        const data = {data_json};
        const metric = "{metric_col}";
        const width = 1000;
        const height = 600;
        const margin = {{top: 50, right: 80, bottom: 20, left: 120}};
        const barSize = 45;
        const n = 10; // Top 10 players
        const duration = 250; // Smoothness of swap (ms)

        const teamColors = {{
            'Chennai Super Kings': '#FDB913',
            'Mumbai Indians': '#004BA0',
            'Royal Challengers Bengaluru': '#2B2A29',
            'Kolkata Knight Riders': '#3A225D',
            'Delhi Capitals': '#00008B',
            'Punjab Kings': '#DD1F2D',
            'Rajasthan Royals': '#EA1A85',
            'Sunrisers Hyderabad': '#FF822E',
            'Gujarat Titans': '#1B2133',
            'Lucknow Super Giants': '#0057E2',
            'Deccan Chargers': '#33414E'
        }};

        async function render() {{
            const div = d3.select("#d3-race-container");
            div.selectAll("*").remove(); // Clear previous if any
            
            const svg = div.append("svg")
                .attr("viewBox", [0, 0, width, height])
                .style("overflow", "visible")
                .style("display", "block");

            const x = d3.scaleLinear([0, 1], [margin.left, width - margin.right]);
            const y = d3.scaleBand()
                .domain(d3.range(n + 1))
                .rangeRound([margin.top, margin.top + barSize * (n + 1)])
                .padding(0.1);

            const formatNumber = d3.format(",d");
            const matches = Array.from(new Set(data.map(d => d.match_seq))).sort((a,b) => a-b);
            
            // Initial Axis
            const xAxis = svg.append("g")
                .attr("transform", `translate(0,${{margin.top}})`)
                .call(d3.axisTop(x).ticks(width / 160).tickSizeOuter(0).tickSizeInner(-barSize * (n + 1)));

            const ticker = svg.append("text")
                .attr("class", "match-ticker")
                .style("font", "bold 34px sans-serif")
                .style("fill", "rgba(255,255,255,0.2)")
                .attr("text-anchor", "end")
                .attr("x", width - margin.right)
                .attr("y", height - margin.bottom)
                .text(`Match #${{matches[0]}}`);

            for (const seq of matches) {{
                const frameData = data.filter(d => d.match_seq === seq)
                    .sort((a, b) => b[metric] - a[metric])
                    .slice(0, n);
                
                x.domain([0, d3.max(data, d => d[metric])]);

                // Update Axis
                xAxis.transition().duration(duration).ease(d3.easeLinear).call(d3.axisTop(x));

                // BARS
                const bar = svg.selectAll(".bar")
                    .data(frameData, d => d.player);

                bar.enter().append("rect")
                    .attr("class", "bar")
                    .attr("fill", d => teamColors[d.team] || '#808080')
                    .attr("x", x(0))
                    .attr("y", y(n))
                    .attr("height", y.bandwidth())
                    .style("opacity", 0.9)
                    .attr("rx", 4)
                    .merge(bar)
                    .transition().duration(duration).ease(d3.easeLinear)
                    .attr("y", (d, i) => y(i))
                    .attr("width", d => x(d[metric]) - x(0));

                bar.exit().transition().duration(duration).ease(d3.easeLinear)
                    .attr("y", y(n))
                    .attr("width", 0).remove();

                // NAMES
                const labels = svg.selectAll(".label")
                    .data(frameData, d => d.player);
                
                labels.enter().append("text")
                    .attr("class", "label")
                    .attr("x", margin.left - 10)
                    .attr("y", y(n))
                    .attr("dy", "1.15em")
                    .attr("text-anchor", "end")
                    .style("fill", "white")
                    .style("font", "bold 13px sans-serif")
                    .text(d => d.player)
                    .merge(labels)
                    .transition().duration(duration).ease(d3.easeLinear)
                    .attr("y", (d, i) => y(i));

                // VALUES
                const values = svg.selectAll(".value-label")
                    .data(frameData, d => d.player);

                values.enter().append("text")
                    .attr("class", "value-label")
                    .attr("x", x(0))
                    .attr("y", y(n))
                    .attr("dy", "1.15em")
                    .attr("dx", 5)
                    .style("fill", "white")
                    .style("font", "bold 12px monospace")
                    .merge(values)
                    .transition().duration(duration).ease(d3.easeLinear)
                    .attr("x", d => x(d[metric]))
                    .attr("y", (d, i) => y(i))
                    .text(d => formatNumber(d[metric]));

                ticker.text(`Match #${{seq}}`);
                
                await new Promise(r => setTimeout(r, duration));
            }}
        }}
        render();
    </script>
    <style>
        .tick line {{ stroke: rgba(255,255,255,0.1); }}
        .tick text {{ fill: rgba(255,255,255,0.5); font-size: 10px; }}
        path.domain {{ display: none; }}
    </style>
    """
    components.html(custom_js, height=650)