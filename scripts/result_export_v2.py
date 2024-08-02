def generate_html(filename, bess, price_data, result_data, revenue_data, discount_rate):
    # Convert revenue_data to a dictionary for JavaScript
    revenue_data_dict = revenue_data.to_dict()

    # Calculate the annual revenue by summing all items in the revenue_data series
    annual_revenue = revenue_data.sum()

    # Generate the HTML content with embedded JavaScript
    html_content = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Financial Calculations with Plotly</title>
        <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
        <style>
            body {{
                font-family: Arial, sans-serif;
                margin: 0;
                padding: 0;
                background-color: #f4f4f4;
                color: #333;
            }}
            .menu {{
                overflow: hidden;
                background-color: #333;
                padding: 0 10px;
            }}
            .menu a {{
                float: left;
                display: block;
                color: white;
                text-align: center;
                padding: 14px 16px;
                text-decoration: none;
            }}
            .menu a:hover {{
                background-color: #ddd;
                color: black;
            }}
            .content {{
                display: none;
                padding: 20px;
                background-color: white;
                margin: 20px;
                border-radius: 8px;
                box-shadow: 0 0 10px rgba(0, 0, 0, 0.1);
            }}
            .content.active {{
                display: block;
            }}
            .chart-container {{
                width: 100%;
                height: 500px;
                margin-top: 20px;
            }}
            .input-group {{
                margin: 10px 0;
                display: flex;
                align-items: center;
            }}
            .input-group label {{
                margin-right: 10px;
                flex: 1;
                font-size: 14px;
            }}
            .input-group input {{
                flex: 2;
                padding: 8px;
                border: 1px solid #ccc;
                border-radius: 4px;
                font-size: 14px;
            }}
            .input-group span {{
                flex: 2;
                padding: 8px;
                border: 1px solid #ccc;
                border-radius: 4px;
                background-color: #f9f9f9;
                text-align: left;
                font-size: 14px;
            }}
            .input-group button {{
                padding: 10px 20px;
                background-color: #007bff;
                color: white;
                border: none;
                border-radius: 4px;
                cursor: pointer;
                font-size: 14px;
            }}
            .input-group button:hover {{
                background-color: #0056b3;
            }}
            .metrics {{
                margin-top: 20px;
                display: flex;
                flex-wrap: wrap;
            }}
            .metrics div {{
                flex: 1 1 200px;
                padding: 10px;
                margin: 5px;
                background-color: #f9f9f9;
                border: 1px solid #ccc;
                border-radius: 4px;
                text-align: center;
                font-size: 14px;
            }}
        </style>
    </head>
    <body>
        <div class="menu">
            <a href="#bessOptimizationResult" onclick="showSection('bessOptimizationResult')">Optimization Result for BESS Operation</a>
            <a href="#economicAnalysis" onclick="showSection('economicAnalysis')">Economic Analysis</a>
        </div>

        <div id="bessOptimizationResult" class="content active">
            <h1>Optimization Result for BESS Operation</h1>
            <p>Optimization results for Battery Energy Storage System (BESS) operation will be displayed here, including price data, charging and discharging schedules, and state of charge over time.</p>
            <div class="chart-container" id="prices_chart"></div>
            <div class="chart-container" id="revenue_breakdown_chart"></div>
            <div class="chart-container" id="charge_discharge_chart"></div>
            <div class="chart-container" id="soc_chart"></div>
        </div>

        <div id="economicAnalysis" class="content">
            <h1>Economic Analysis</h1>

            <h2>Capacity Settings</h2>
            <div class="input-group">
                <label>Power capacity (MW):</label>
                <span id="cap_power">{bess['cap_power']}</span>
            </div>
            <div class="input-group">
                <label>Energy capacity (MWh):</label>
                <span id="cap_energy">{bess['cap_energy']}</span>
            </div>

            <h2>Costing</h2>
            <div class="input-group">
                <label for="fixed_capex">Fixed capital cost ($):</label>
                <input type="number" id="fixed_capex" name="fixed_capex" value="{bess['fixed_capex']}" step="1000" min="0" oninput="updateInitialCost()">
            </div>
            <div class="input-group">
                <label for="energy_capex">Energy-related capital cost ($/kWh):</label>
                <input type="number" id="energy_capex" name="energy_capex" value="{bess['energy_capex']}" step="1000" min="0" oninput="updateInitialCost()">
            </div>
            <div class="input-group">
                <label for="power_capex">Power-related capital cost ($/kW):</label>
                <input type="number" id="power_capex" name="power_capex" value="{bess['power_capex']}" step="1000" min="0" oninput="updateInitialCost()">
            </div>
            <div class="input-group">
                <label for="fixedOpex">Fixed O&M cost ($):</label>
                <input type="number" id="fixedOpex" name="fixedOpex" value="{bess['fixed_opex']}" step="100" min="0" oninput="updateAnnualCost()">
            </div>
            <div class="input-group">
                <label for="energyOpex">Energy-related O&M cost ($/kWh):</label>
                <input type="number" id="energyOpex" name="energyOpex" value="{bess['energy_opex']}" step="10" min="0" oninput="updateAnnualCost()">
            </div>
            <div class="input-group">
                <label for="powerOpex">Power-related O&M cost ($/kW):</label>
                <input type="number" id="powerOpex" name="powerOpex" value="{bess['power_opex']}" step="10" min="0" oninput="updateAnnualCost()">
            </div>

            <h2>Financial Analysis</h2>
            <div class="input-group">
                <label>Initial cost ($):</label>
                <span id="initialCost">0.00</span>
            </div>
            <div class="input-group">
                <label>Annual cost ($):</label>
                <span id="annualCost">0.00</span>
            </div>
            <div class="input-group">
                <label>Annual revenue ($):</label>
                <span id="annualRevenue">{annual_revenue:,.2f}</span>
            </div>
            <div class="input-group">
                <label for="discountRate">Discount rate (%):</label>
                <input type="number" id="discountRate" name="discountRate" value="{discount_rate * 100}" step="0.01" min="0" max="100" oninput="updateChart()">
            </div>
            <div class="input-group">
                <label for="revenueChange">Annual revenue change (%):</label>
                <input type="number" id="revenueChange" name="revenueChange" value="0" step="1" min="-100" max="100" oninput="updateChart()">
            </div>
            <div class="input-group">
                <label for="costChange">Annual cost change (%):</label>
                <input type="number" id="costChange" name="costChange" value="0" step="1" min="-100" max="100" oninput="updateChart()">
            </div>
            <div class="input-group">
                <button onclick="resetDefaults()">Reset to Default Values</button>
            </div>

            <div class="metrics">
                <div>NPV: $<span id="npvValue"></span></div>
                <div>BCR: <span id="bcrValue"></span></div>
                <div>ROI: <span id="roiValue"></span>%</div>
                <div>IRR: <span id="irrValue"></span>%</div>
                <div>Payback Period: <span id="paybackPeriod"></span> years</div>
            </div>

            <div class="chart-container" id="netCashFlowChart"></div>
            <div class="chart-container" id="cumulativeCashFlowChart"></div>
        </div>

        <script>
            const defaultValues = {{
                fixed_capex: {bess['fixed_capex']},
                energy_capex: {bess['energy_capex']},
                power_capex: {bess['power_capex']},
                cap_energy: {bess['cap_energy']},
                cap_power: {bess['cap_power']},
                discountRate: {discount_rate},
                annualRevenue: {annual_revenue},
                fixedOpex: {bess['fixed_opex']},
                energyOpex: {bess['energy_opex']},
                powerOpex: {bess['power_opex']},
                revenueChange: 0,
                costChange: 0,
                projectDuration: {bess['calendar_life']}
            }};

            var priceData = {price_data};
            var resultData = {result_data};
            var revenueBreakdownData = {revenue_data_dict};

            priceData.forEach(function(d) {{
                d.time = new Date(d.time);
            }});

            resultData.forEach(function(d) {{
                d.time = new Date(d.time);
            }});

            function formatCurrency(value) {{
                return value.toLocaleString(undefined, {{ minimumFractionDigits: 2, maximumFractionDigits: 2 }});
            }}

            function updateInitialCost() {{
                let fixed_capex = parseFloat(document.getElementById('fixed_capex').value);
                let energy_capex = parseFloat(document.getElementById('energy_capex').value) * 1000;
                let power_capex = parseFloat(document.getElementById('power_capex').value) * 1000;
                let cap_energy = parseFloat(document.getElementById('cap_energy').innerText);
                let cap_power = parseFloat(document.getElementById('cap_power').innerText);
                let initialCost = fixed_capex + (energy_capex * cap_energy) + (power_capex * cap_power);
                document.getElementById('initialCost').innerText = formatCurrency(initialCost);
                updateAnnualCost();
            }}

            function updateAnnualCost() {{
                let fixedOpex = parseFloat(document.getElementById('fixedOpex').value);
                let energyOpex = parseFloat(document.getElementById('energyOpex').value);
                let powerOpex = parseFloat(document.getElementById('powerOpex').value);
                let cap_energy = parseFloat(document.getElementById('cap_energy').innerText);
                let cap_power = parseFloat(document.getElementById('cap_power').innerText);
                let annualCost = fixedOpex + (energyOpex * cap_energy) + (powerOpex * cap_power);
                document.getElementById('annualCost').innerText = formatCurrency(annualCost);
                updateChart();
            }}

            function calculatePaybackPeriod(cumulativeCashFlow) {{
                for (let i = 0; i < cumulativeCashFlow.length; i++) {{
                    if (cumulativeCashFlow[i] >= 0) {{
                        return i;
                    }}
                }}
                return 'N/A';
            }}

            function calculateIRR(values) {{
                const guess = 0.1;
                const tol = 1e-6;
                const maxIter = 100;
                let rate = guess;
                for (let i = 0; i < maxIter; i++) {{
                    let npv = values.reduce((acc, val, j) => acc + val / Math.pow(1 + rate, j), 0);
                    let npvPrime = values.reduce((acc, val, j) => acc - (j * val) / Math.pow(1 + rate, j + 1), 0);
                    let newRate = rate - npv / npvPrime;
                    if (Math.abs(newRate - rate) < tol) return newRate;
                    rate = newRate;
                }}
                return rate;
            }}

            function calculateFinancialMetrics(discountRate, initialCost, annualCost, annualRevenue, revenueChange, costChange) {{
                let periods = Array.from({{ length: defaultValues.projectDuration + 1 }}, (_, i) => i);
                let cashInflows = [0].concat(Array(defaultValues.projectDuration).fill(annualRevenue).map((rev, i) => rev * Math.pow(1 + revenueChange / 100, i)));
                let cashOutflows = [initialCost].concat(Array(defaultValues.projectDuration).fill(annualCost).map((cost, i) => cost * Math.pow(1 + costChange / 100, i)));

                let netCashFlow = cashInflows.map((inflow, i) => inflow - cashOutflows[i]);
                let discountedNetCashFlow = netCashFlow.map((flow, i) => flow / Math.pow(1 + discountRate, periods[i]));
                let cumulativeNetCashFlow = netCashFlow.reduce((acc, val, i) => [...acc, (acc[i - 1] || 0) + val], []);
                let cumulativeDiscountedCashFlow = discountedNetCashFlow.reduce((acc, val, i) => [...acc, (acc[i - 1] || 0) + val], []);

                let totalPvInflows = cashInflows.reduce((acc, val, i) => acc + val / Math.pow(1 + discountRate, i), 0);
                let totalPvOutflows = cashOutflows.reduce((acc, val, i) => acc + val / Math.pow(1 + discountRate, i), 0);

                let npv = cumulativeDiscountedCashFlow[cumulativeDiscountedCashFlow.length - 1];
                let bcr = totalPvInflows / totalPvOutflows;
                let roi = ((totalPvInflows - totalPvOutflows) / totalPvOutflows) * 100;
                let irr = calculateIRR(netCashFlow) * 100;
                let paybackPeriod = calculatePaybackPeriod(cumulativeNetCashFlow);

                document.getElementById('npvValue').innerText = formatCurrency(npv);
                document.getElementById('bcrValue').innerText = bcr.toFixed(2);
                document.getElementById('roiValue').innerText = roi.toFixed(2);
                document.getElementById('irrValue').innerText = irr.toFixed(2);
                document.getElementById('paybackPeriod').innerText = paybackPeriod;

                return {{
                    periods,
                    cashInflows,
                    cashOutflows,
                    netCashFlow,
                    cumulativeNetCashFlow,
                    cumulativeDiscountedCashFlow
                }};
            }}

            function updateChart() {{
                let discountRate = parseFloat(document.getElementById('discountRate').value) / 100;
                let initialCost = parseFloat(document.getElementById('initialCost').innerText.replace(/,/g, ''));
                let annualCost = parseFloat(document.getElementById('annualCost').innerText.replace(/,/g, ''));
                let annualRevenue = parseFloat(document.getElementById('annualRevenue').innerText.replace(/,/g, ''));
                let revenueChange = parseFloat(document.getElementById('revenueChange').value);
                let costChange = parseFloat(document.getElementById('costChange').value);

                let metrics = calculateFinancialMetrics(discountRate, initialCost, annualCost, annualRevenue, revenueChange, costChange);

                let cashInflowsTrace = {{
                    x: metrics.periods,
                    y: metrics.cashInflows,
                    name: 'Annual Revenue',
                    type: 'bar'
                }};

                let cashOutflowsTrace = {{
                    x: metrics.periods,
                    y: metrics.cashOutflows,
                    name: 'Annual Cost',
                    type: 'bar'
                }};

                let netCashFlowTrace = {{
                    x: metrics.periods,
                    y: metrics.netCashFlow,
                    name: 'Net Cash Flow',
                    type: 'scatter',
                    mode: 'lines+markers'
                }};

                let cumulativeNetCashFlowTrace = {{
                    x: metrics.periods,
                    y: metrics.cumulativeNetCashFlow,
                    name: 'Undiscounted Cumulative Cash Flow',
                    type: 'scatter',
                    mode: 'lines+markers'
                }};

                let cumulativeDiscountedCashFlowTrace = {{
                    x: metrics.periods,
                    y: metrics.cumulativeDiscountedCashFlow,
                    name: 'Discounted Cumulative Cash Flow',
                    type: 'scatter',
                    mode: 'lines+markers'
                }};

                let netCashFlowData = [cashInflowsTrace, cashOutflowsTrace, netCashFlowTrace];
                let cumulativeCashFlowData = [cumulativeNetCashFlowTrace, cumulativeDiscountedCashFlowTrace];

                let netCashFlowLayout = {{
                    title: 'Net Cash Flow with Annual Costs and Revenues',
                    xaxis: {{ title: 'Period' }},
                    yaxis: {{ title: 'Amount ($)' }},
                    barmode: 'group',
                    legend: {{ orientation: "h", y: 1.2 }}
                }};

                let cumulativeCashFlowLayout = {{
                    title: 'Cumulative Cash Flows',
                    xaxis: {{ title: 'Period' }},
                    yaxis: {{ title: 'Amount ($)' }},
                    legend: {{ orientation: "h", y: 1.2 }}
                }};

                Plotly.newPlot('netCashFlowChart', netCashFlowData, netCashFlowLayout, {{responsive: true}});
                Plotly.newPlot('cumulativeCashFlowChart', cumulativeCashFlowData, cumulativeCashFlowLayout, {{responsive: true}});
            }}

            function showSection(sectionId) {{
                var sections = document.querySelectorAll('.content');
                sections.forEach(function(section) {{
                    section.classList.remove('active');
                }});
                document.getElementById(sectionId).classList.add('active');
                window.dispatchEvent(new Event('resize')); // Trigger resize to adjust Plotly charts
            }}

            function renderCharts() {{
                // Prices Chart
                Plotly.newPlot('prices_chart', [
                    {{
                        x: priceData.map(item => item.time),
                        y: priceData.map(item => item.arb_energy_price),
                        type: 'scatter',
                        mode: 'lines',
                        name: 'Energy Price'
                    }},
                    {{
                        x: priceData.map(item => item.time),
                        y: priceData.map(item => item.reg_up_price),
                        type: 'scatter',
                        mode: 'lines',
                        name: 'Regulation Up Price'
                    }},
                    {{
                        x: priceData.map(item => item.time),
                        y: priceData.map(item => item.reg_down_price),
                        type: 'scatter',
                        mode: 'lines',
                        name: 'Regulation Down Price'
                    }},
                    {{
                        x: priceData.map(item => item.time),
                        y: priceData.map(item => item.pres_capacity_price),
                        type: 'scatter',
                        mode: 'lines',
                        name: 'Primary Reserve Price'
                    }},
                    {{
                        x: priceData.map(item => item.time),
                        y: priceData.map(item => item.cres_capacity_price),
                        type: 'scatter',
                        mode: 'lines',
                        name: 'Contingency Reserve Price'
                    }}
                ], {{
                    title: 'Energy Prices Over Time',
                    xaxis: {{title: 'Time'}},
                    yaxis: {{title: 'Price ($/MWh)'}},
                    legend: {{ orientation: "h", y: 1.2 }}
                }}, 
                {{responsive: true}});

                // Charge Discharge Chart
                Plotly.newPlot('charge_discharge_chart', [
                    {{
                        x: resultData.map(item => item.time),
                        y: resultData.map(item => item.net_discharge),
                        type: 'scatter',
                        mode: 'lines',
                        name: 'Net Power'
                    }},
                    {{
                        x: resultData.map(item => item.time),
                        y: resultData.map(item => item.reg_up),
                        type: 'scatter',
                        mode: 'lines',
                        name: 'Regulation Up Capacity'
                    }},
                    {{
                        x: resultData.map(item => item.time),
                        y: resultData.map(item => item.reg_down),
                        type: 'scatter',
                        mode: 'lines',
                        name: 'Regulation Down Capacity'
                    }},
                    {{
                        x: resultData.map(item => item.time),
                        y: resultData.map(item => item.pres),
                        type: 'scatter',
                        mode: 'lines',
                        name: 'Primary Reserve Capacity'
                    }},
                    {{
                        x: resultData.map(item => item.time),
                        y: resultData.map(item => item.cres),
                        type: 'scatter',
                        mode: 'lines',
                        name: 'Contingency Reserve Capacity'
                    }}
                ], {{
                    title: 'Operation Schedule',
                    xaxis: {{title: 'Time'}},
                    yaxis: {{title: 'Power (MW)'}},
                    legend: {{ orientation: "h", y: 1.2 }}
                }}, 
                {{responsive: true}});

                // SOC Chart
                Plotly.newPlot('soc_chart', [
                    {{
                        x: resultData.map(item => item.time),
                        y: resultData.map(item => item.soc_percent * 100),
                        type: 'scatter',
                        mode: 'lines',
                        name: 'State of Charge'
                    }}
                ], {{
                    title: 'State of Charge Over Time',
                    xaxis: {{title: 'Time'}},
                    yaxis: {{title: 'SOC (%)'}},
                    legend: {{ orientation: "h", y: 1.2 }}
                }}, 
                {{responsive: true}});

                // Revenue Breakdown Chart
                Plotly.newPlot('revenue_breakdown_chart', [
                    {{
                        x: Object.values(revenueBreakdownData),
                        y: Object.keys(revenueBreakdownData),
                        type: 'bar',
                        orientation: 'h'
                    }}
                ], {{
                    title: 'Breakdown of Annual Revenues',
                    xaxis: {{title: 'Revenue ($)'}},
                    yaxis: {{title: 'Revenue Sources'}},
                    legend: {{ orientation: "h", y: 1.2 }}
                }}, 
                {{responsive: true}});
            }}

            function resetDefaults() {{
                document.getElementById('fixed_capex').value = defaultValues.fixed_capex;
                document.getElementById('energy_capex').value = defaultValues.energy_capex;
                document.getElementById('power_capex').value = defaultValues.power_capex;
                document.getElementById('fixedOpex').value = defaultValues.fixedOpex;
                document.getElementById('energyOpex').value = defaultValues.energyOpex;
                document.getElementById('powerOpex').value = defaultValues.powerOpex;
                document.getElementById('discountRate').value = defaultValues.discountRate * 100;
                document.getElementById('revenueChange').value = defaultValues.revenueChange;
                document.getElementById('costChange').value = defaultValues.costChange;
                document.getElementById('cap_energy').innerText = defaultValues.cap_energy;
                document.getElementById('cap_power').innerText = defaultValues.cap_power;
                document.getElementById('annualRevenue').innerText = formatCurrency(defaultValues.annualRevenue);
                updateInitialCost();
            }}

            resetDefaults(); // Initialize with default values
            renderCharts(); // Render charts initially
        </script>
    </body>
    </html>
    """

    # Write the HTML content to a file
    with open('result/' + filename + ".html", 'w') as file:
        file.write(html_content)

    print("HTML file generated:" + filename + ".html")
