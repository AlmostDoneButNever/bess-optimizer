import pandas as pd
import os
import glob

def price_process(dir_path, prim_category, cons_category):

    # Define the folder paths containing the CSV files
    folder_names = ['energy', 'regulation', 'reserve']

    # Create a dictionary to map periods to specific times
    period_to_time = {
        1: "00:00",  2: "00:30", 3: "01:00", 4: "01:30", 5: "02:00",     6: "02:30",
        7: "03:00",    8: "03:30",    9: "04:00",    10: "04:30",
        11: "05:00",    12: "05:30",    13: "06:00",    14: "06:30",
        15: "07:00",    16: "07:30",    17: "08:00",    18: "08:30",
        19: "09:00",    20: "09:30",    21: "10:00",    22: "10:30",
        23: "11:00",    24: "11:30",    25: "12:00",    26: "12:30",
        27: "13:00",    28: "13:30",    29: "14:00",    30: "14:30",
        31: "15:00",    32: "15:30",    33: "16:00",    34: "16:30",
        35: "17:00",    36: "17:30",    37: "18:00",    38: "18:30",
        39: "19:00",    40: "19:30",    41: "20:00",    42: "20:30",
        43: "21:00",    44: "21:30",    45: "22:00",    46: "22:30",
        47: "23:00",    48: "23:30"
    }


    # Create a dictionary to store concatenated dataframes by folder
    data = {}

    # Iterate over each folder path
    for folder_name in folder_names:
        # Get a list of all CSV files in the folder
        folder_path = dir_path + folder_name + "/"
        csv_files = glob.glob(os.path.join(folder_path, "*.csv"))

        # Check if files are found
        if not csv_files:
            print(f"No CSV files found in the directory: {folder_path}")
            continue

        print(f"Found {len(csv_files)} CSV files in {folder_path}")

        # Create a list to store dataframes
        dataframes = []

        # Iterate over the list of CSV files
        for file in csv_files:
            # Read the CSV file into a dataframe
            df = pd.read_csv(file)
            
            # Append the dataframe to the list
            dataframes.append(df)

        # Concatenate all dataframes into a single dataframe for the current folder
        concatenated_df = pd.concat(dataframes, ignore_index=True)
        
        # Store the concatenated dataframe in the dictionary
        data[folder_name] = concatenated_df


    energy_price_df = data['energy'][['DATE', 'PERIOD', 'USEP ($/MWh)']]
    energy_price_df.columns = ['date', 'period', 'arb_energy_price']

    # Ensure we are working with the original dataframe
    energy_price = energy_price_df.copy()
    energy_price.loc[:, "timestep"] = energy_price["period"].map(period_to_time)
    energy_price.loc[:, "Time"] = energy_price["date"] + " " + energy_price["timestep"]
    energy_price = energy_price[['Time', 'arb_energy_price']].set_index(['Time'])

    regulation_price = data['regulation'][['DATE', 'PERIOD', 'PRICE ($/MWh)']]
    regulation_price.columns = ['date', 'period', 'reg_up_price']
    regulation_price['reg_down_price'] = regulation_price['reg_up_price']
    regulation_price.loc[:, "timestep"] = regulation_price["period"].map(period_to_time)
    regulation_price.loc[:, "Time"] = regulation_price["date"] + " " + regulation_price["timestep"]
    regulation_price = regulation_price[['Time', 'reg_up_price', 'reg_down_price']].set_index(['Time'])

    reserve_price = data['reserve'][['RESERVE GROUP', 'DATE', 'PERIOD', 'PRICE ($/MWh)']]
    reserve_price.loc[:, "timestep"] = reserve_price["PERIOD"].map(period_to_time)
    reserve_price.loc[:, "Time"] = reserve_price["DATE"] + " " + reserve_price["timestep"]
    reserve_price = reserve_price[['RESERVE GROUP', 'Time', 'PRICE ($/MWh)']]

    cons_reserve_price = reserve_price[reserve_price["RESERVE GROUP"].str.contains("CON")]
    cons_reserve_price.columns = ['Group', 'Time', 'cres_capacity_price']
    cons_reserve_price = cons_reserve_price.set_index(['Group','Time'])

    prim_reserve_price = reserve_price[reserve_price["RESERVE GROUP"].str.contains("PRI")]
    prim_reserve_price.columns = ['Group', 'Time', 'pres_capacity_price']
    prim_reserve_price = prim_reserve_price.set_index(['Group','Time'])

    merged_df = pd.merge(energy_price, regulation_price, on="Time")
    merged_df = pd.merge(merged_df, prim_reserve_price.loc[prim_category], on="Time")
    merged_df = pd.merge(merged_df, cons_reserve_price.loc[cons_category], on="Time")

    merged_df = merged_df.reset_index()
    merged_df['Time'] = pd.to_datetime(merged_df['Time'])
    merged_df = merged_df.set_index(['Time']).sort_index()

    return merged_df
