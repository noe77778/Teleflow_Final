import pandas as pd
import json

# Function to read the CSV file
def read_csv(file_path):
    try:
        df = pd.read_csv(file_path)
        print("CSV file read successfully.")
        return df
    except FileNotFoundError:
        print("File not found.")
        return None
    except pd.errors.EmptyDataError:
        print("No data.")
        return None
    except pd.errors.ParserError:
        print("Parsing error.")
        return None

# Function to clean and validate the data
def clean_data(df):
    def identify_problematic_rows(column):
        problematic_rows = df[~df[column].apply(lambda x: isinstance(x, (int, float)) or str(x).replace('.', '', 1).isdigit())]
        if not problematic_rows.empty:
            print(f"Problematic rows in column {column}:")
            print(problematic_rows)
    
    identify_problematic_rows('Voltage (V)')
    identify_problematic_rows('Current (A)')
    identify_problematic_rows('Power (W)')
    
    df['Voltage (V)'] = pd.to_numeric(df['Voltage (V)'], errors='coerce')
    df['Current (A)'] = pd.to_numeric(df['Current (A)'], errors='coerce')
    df['Power (W)'] = pd.to_numeric(df['Power (W)'], errors='coerce')
    
    df = df.dropna()
    
    return df

# Function to analyze the data and store results in variables
def analyze_data(df):
    num_records = len(df)
    avg_voltage = df['Voltage (V)'].mean()
    avg_current = df['Current (A)'].mean()
    avg_power = df['Power (W)'].mean()
    max_voltage = df['Voltage (V)'].max()
    max_current = df['Current (A)'].max()
    max_power = df['Power (W)'].max()
    min_voltage = df['Voltage (V)'].min()
    min_current = df['Current (A)'].min()
    min_power = df['Power (W)'].min()
    
    return {
        "num_records": num_records,
        "avg_voltage": avg_voltage,
        "avg_current": avg_current,
        "avg_power": avg_power,
        "max_voltage": max_voltage,
        "max_current": max_current,
        "max_power": max_power,
        "min_voltage": min_voltage,
        "min_current": min_current,
        "min_power": min_power
    }

# Main function to handle the CSV file
def main():
    csv_file_path = 'power_consumption_log.csv'
    df = read_csv(csv_file_path)
    
    if df is not None:
        try:
            df['Timestamp'] = pd.to_datetime(df['Timestamp'])
        except KeyError:
            print("Timestamp column not found.")
            return None
        
        df = clean_data(df)
        analysis_results = analyze_data(df)
        
        json_results = json.dumps(analysis_results, indent=4)
        print(json_results)
        
        return json_results
    else:
        print("Failed to read CSV file.")
        return None

if __name__ == "__main__":
    main()
