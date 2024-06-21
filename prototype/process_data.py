import pandas as pd
import os

def process_data():
    try:
        # Example data processing
        data = {'Column1': [1, 2, 3, 4], 'Column2': [5, 6, 7, 8]}
        df = pd.DataFrame(data)

        # Save to a new Excel file
        output_file = 'output.xlsx'
        df.to_excel(output_file, index=False)
        print(f"Data processed and saved to {output_file}")

        # Check if file is created
        if os.path.exists(output_file):
            print(f"File {output_file} created successfully.")
        else:
            print(f"Failed to create {output_file}.")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    process_data()
