from flask import Flask, render_template, request, redirect, url_for
import pandas as pd

# Import the Pyomo function from the scripts folder
from scripts.optimization import optimize_revenue
from scripts.data_import import data_import
from scripts.result_export_v2 import generate_html 

app = Flask(__name__, template_folder='templates', static_folder='flask/static')
app.secret_key = 'supersecretkey'

@app.route('/')
def index():
    return render_template('input.html')

@app.route('/result', methods=['POST'])
def result():
    if 'file' not in request.files:
        return redirect(request.url)
    file = request.files['file']
    if file.filename == '':
        return redirect(request.url)
    if file:
        battery_power_capacity = request.form.get('battery_power_capacity')
        energy_capacity = request.form.get('energy_capacity')

        # Print the values to the terminal
        print(f"Battery Power Capacity (MW): {battery_power_capacity}")
        print(f"Energy Capacity (MWh): {energy_capacity}")

        # Directly read the Excel file into a DataFrame without saving the file
        data, basis, bess, service, revenue_change = data_import(file)

        bess['cap_energy'] = float(energy_capacity)
        bess['cap_power'] = float(battery_power_capacity)

        price_df = data['prices']

        model_time_period = int(basis['model_time_period'])    # periods
        total_time_period = len(data['prices'])
        num_slices = int(total_time_period // model_time_period)     # number of time slices to model
        initial_soc = bess['initial_soc'] * bess['cap_energy']
        packaged_data = [data, basis, bess, service] 

        # Lists to store results
        total_revenue = 0
        skipped_p = []

        all_schedule_dict = {}
        all_schedule_dict['arb_charge'] = []
        all_schedule_dict['arb_discharge'] = []
        all_schedule_dict['reg_down'] = []
        all_schedule_dict['reg_up'] = []
        all_schedule_dict['pres'] = []
        all_schedule_dict['cres'] = []
        all_schedule_dict['dr'] = []
        all_schedule_dict['il'] = []
        all_schedule_dict['grid_purchase'] = []
        all_schedule_dict['grid_to_storage'] = []
        all_schedule_dict['grid_to_load'] = []
        all_schedule_dict['storage_to_load'] = []
        all_schedule_dict['soc'] = []

        all_revenue_dict = {}
        all_revenue_dict['Arbitrage'] =  []
        all_revenue_dict['Frequency Regulation'] = []
        all_revenue_dict['Primary Reserve'] = []
        all_revenue_dict['Contingency Reserve'] = []
        all_revenue_dict['Demand Response'] = []
        all_revenue_dict['Interruptible Load'] = []
        all_revenue_dict['Demand-side Energy Savings'] = []

        first_p = 0
        last_p = num_slices #- 1

        num_slices = 10

        # Run the optimization for each time period
        for p in range(num_slices):
            if p == last_p:
                final_soc_target = 1
            else:
                final_soc_target = 0

            periodic_price = price_df[p*model_time_period:(p+1)*model_time_period]
            periodic_price = periodic_price.set_index('period')

            if service['load'] == 1:
                periodic_load = data['load'][p*model_time_period:(p+1)*model_time_period]
                periodic_load = periodic_load.set_index('period')
            else:
                periodic_load = []

            try:
                model, revenue, schedule_dict, revenue_dict = optimize_revenue(initial_soc, packaged_data, periodic_price, periodic_load, final_soc_target)
                
                # Store the results
                total_revenue += model.obj()
                
                all_revenue_dict['Arbitrage'].extend(revenue_dict['arb'])
                all_revenue_dict['Frequency Regulation'].extend(revenue_dict['reg'])
                all_revenue_dict['Primary Reserve'].extend(revenue_dict['pres'])
                all_revenue_dict['Contingency Reserve'].extend(revenue_dict['cres'])
                all_revenue_dict['Demand-side Energy Savings'].extend(revenue_dict['ec'])
                all_revenue_dict['Demand Response'].extend(revenue_dict['dr'])
                all_revenue_dict['Interruptible Load'].extend(revenue_dict['il'])
                
                all_schedule_dict['arb_charge'].extend(schedule_dict['arb_charge'])
                all_schedule_dict['arb_discharge'].extend(schedule_dict['arb_discharge'])
                all_schedule_dict['reg_up'].extend(schedule_dict['reg_up'])
                all_schedule_dict['reg_down'].extend(schedule_dict['reg_down'])
                all_schedule_dict['pres'].extend(schedule_dict['pres'])
                all_schedule_dict['cres'].extend(schedule_dict['cres'])
                all_schedule_dict['dr'].extend(schedule_dict['dr'])
                all_schedule_dict['il'].extend(schedule_dict['il'])
                all_schedule_dict['grid_purchase'].extend(schedule_dict['grid_purchase'])
                all_schedule_dict['grid_to_storage'].extend(schedule_dict['grid_to_storage'])
                all_schedule_dict['grid_to_load'].extend(schedule_dict['grid_to_load'])
                all_schedule_dict['storage_to_load'].extend(schedule_dict['storage_to_load'])
                all_schedule_dict['soc'].extend(schedule_dict['soc'][:-1])

                # Update the initial SOC for the next day
                final_soc = schedule_dict['soc'][-1]
                initial_soc = final_soc

            except:
                skipped_p.append(p)

        # Create a DataFrame for the results
        all_revenue_dict['time'] = price_df.index[:len(all_schedule_dict['arb_charge'])]
        revenue_data = pd.DataFrame(all_revenue_dict)

        all_schedule_dict['time'] = price_df.index[:len(all_schedule_dict['arb_charge'])]
        result_df = pd.DataFrame(all_schedule_dict)
        result_df['net_power'] = result_df['arb_discharge'] - result_df['arb_charge'] - result_df['grid_purchase']
        result_df['soc_percent'] = result_df['soc'] /bess['cap_energy']

        if service['load'] == 1:
            result_df = result_df.set_index(['time'])
            result_df['load'] = data['load'].value[:len(all_schedule_dict['arb_charge'])]/basis['dt']
            result_df = result_df.reset_index()

        price_df.index.names = ['time']
        bess['revenue'] = total_revenue

        filename = 'results/output'
        html_file_path = filename + ".html"
        generate_html(filename, bess, service, price_df, result_df, revenue_data, basis['wacc'], service['load'])

        # Read the generated HTML file content
        with open(html_file_path, "r") as f:
            generated_html_content = f.read()

        return render_template('output.html', generated_html=generated_html_content, solution=total_revenue)

if __name__ == '__main__':
    app.run(debug=True)
