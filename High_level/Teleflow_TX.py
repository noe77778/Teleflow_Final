import os
import sys
import time
import json
import serial
import csv
import pandas as pd
import threading
from datetime import datetime, timedelta
from awscrt import mqtt, http
from awsiot import mqtt_connection_builder
from utils.command_line_utils import CommandLineUtils

# Global Variables
SerialDone = False
id_counter = 0
serial_port = "/dev/ttyUSB0"
baudrate = 115200
csv_file_path = 'power_consumption_log.csv'
counter_file_path = '/home/chaca/aws-iot-device-sdk-python-v2/samples/id_counter.txt'

# Parse command line arguments
cmdData = CommandLineUtils.parse_sample_input_pubsub()

# MQTT Callbacks
def on_connection_interrupted(connection, error, **kwargs):
    print(f"Connection interrupted. error: {error}")
    save_id_counter(id_counter)

def on_connection_resumed(connection, return_code, session_present, **kwargs):
    print(f"Connection resumed. return_code: {return_code} session_present: {session_present}")
    if return_code == mqtt.ConnectReturnCode.ACCEPTED and not session_present:
        print("Session did not persist. Resubscribing to existing topics...")
        resubscribe_future, _ = connection.resubscribe_existing_topics()
        resubscribe_future.add_done_callback(on_resubscribe_complete)

def on_resubscribe_complete(resubscribe_future):
    resubscribe_results = resubscribe_future.result()
    print(f"Resubscribe results: {resubscribe_results}")
    for topic, qos in resubscribe_results['topics']:
        if qos is None:
            sys.exit(f"Server rejected resubscribe to topic: {topic}")

def on_connection_success(connection, callback_data):
    assert isinstance(callback_data, mqtt.OnConnectionSuccessData)
    print(f"Connection Successful with return code: {callback_data.return_code} session present: {callback_data.session_present}")

def on_connection_failure(connection, callback_data):
    assert isinstance(callback_data, mqtt.OnConnectionFailureData)
    print(f"Connection failed with error code: {callback_data.error}")
    save_id_counter(id_counter)

def on_connection_closed(connection, callback_data):
    print("Connection closed")
    save_id_counter(id_counter)

# ID Counter Handling
def save_id_counter(counter):
    with open(counter_file_path, 'w') as f:
        f.write(str(counter))
        print("Counter successfully written to file")

def load_id_counter():
    if os.path.exists(counter_file_path):
        with open(counter_file_path, 'r') as f:
            return int(f.read().strip())
    return 2001

# CSV Handling
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

def clean_data(df):
    def identify_problematic_rows(column):
        problematic_rows = df[~df[column].apply(lambda x: isinstance(x, (int, float)) or str(x).replace('.', '', 1).isdigit())]
        if not problematic_rows.empty:
            print(f"Problematic rows in column {column}:")
    
    identify_problematic_rows('Voltage (V)')
    identify_problematic_rows('Current (A)')
    identify_problematic_rows('Power (W)')
    
    df['Voltage (V)'] = pd.to_numeric(df['Voltage (V)'], errors='coerce')
    df['Current (A)'] = pd.to_numeric(df['Current (A)'], errors='coerce')
    df['Power (W)'] = pd.to_numeric(df['Power (W)'], errors='coerce')
    
    df = df.dropna()
    
    return df

def analyze_data(df):
    num_records = len(df)
    avg_voltage = df['Voltage (V)'].mean()
    avg_current = df['Current (A)'].mean()
    avg_power = round(df['Power (W)'].mean(), 2)
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

def analyze_serial_CSV():
    df = read_csv(csv_file_path)
    
    if df is not None:
        try:
            df['Timestamp'] = pd.to_datetime(df['Timestamp'], errors='coerce')
        except KeyError:
            print("Timestamp column not found.")
            return None
        
        df = clean_data(df)
        analysis_results = analyze_data(df)
        
        return analysis_results
    else:
        print("Failed to read CSV file.")
        return None

# Serial Data Handling
def open_serial_port(port, baudrate, timeout=1):
    try:
        ser = serial.Serial(port, baudrate, timeout=timeout)
        print("Serial port opened successfully.")
        return ser
    except serial.SerialException as e:
        print(f"Error opening or using serial port: {e}")
        return None

def read_serial_data(ser):
    try:
        if ser.in_waiting > 0:
            line = ser.readline().decode('utf-8').rstrip()
            return line
    except serial.SerialException as e:
        print(f"Error reading serial data: {e}")
    return None

def parse_ina219_data(data_lines):
    try:
        voltage_line = data_lines[0]
        current_line = data_lines[1]
        power_line = data_lines[2]

        voltage = float(voltage_line.split(':')[1].strip().split(' ')[0])
        current = float(current_line.split(':')[1].strip().split(' ')[0]) / 1000  # Convert mA to A
        power = float(power_line.split(':')[1].strip().split(' ')[0]) / 1000  # Convert mW to W

        return voltage, current, power
    except (IndexError, ValueError) as e:
        print(f"Error parsing data: {data_lines} - {e}")
        return None, None, None

def log_to_csv(file_path, data):
    with open(file_path, 'a', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(data)

def read_INA219_serial():
    global SerialDone
    ser = open_serial_port(serial_port, baudrate)

    if ser is None:
        return

    try:
        with open(csv_file_path, 'a', newline='') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(['Timestamp', 'Voltage (V)', 'Current (A)', 'Power (W)'])

        buffer = []
        start_time = datetime.now()
        end_time = start_time + timedelta(minutes=1)  # Reading for 1 minute

        while datetime.now() < end_time:
            data = read_serial_data(ser)
            if data:
                print(data)
                buffer.append(data)
                if len(buffer) == 3:
                    voltage, current, power = parse_ina219_data(buffer)
                    if voltage is not None and current is not None and power is not None:
                        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        log_to_csv(csv_file_path, [timestamp, voltage, current, power])
                    else:
                        print("Data parsing failed, skipping log entry.")
                    buffer = []  # Clear buffer for the next set of data lines
            time.sleep(0.1)  # Add a small delay to prevent high CPU usage

    except KeyboardInterrupt:
        print("Interrupted by user.")
        save_id_counter(id_counter)
    
    finally:
        if ser and ser.is_open:
            ser.close()
            print("Serial port closed.")
            SerialDone = True

def publish_messages(mqtt_connection, topic):
    global id_counter
    id_counter = load_id_counter()

    try:
        while True:
            global SerialDone
            if SerialDone:
                pandas_results = analyze_serial_CSV()  # Analyzes obtained data
                if pandas_results:
                    messageA = {
                        "id": str(id_counter),
                        "date": datetime.now().strftime("%b %d %H:%M"),  # Month, day, hours, and minutes
                        "disconnectionDate": "",
                        "myState": "",
                        "powerConsumption": pandas_results['avg_power'],  # Average power consumption
                        "reconnectionDate": ""
                    }
                    print(f"Publishing message to topic '{topic}': {messageA}")
                    message_jsonA = json.dumps(messageA)
                    mqtt_connection.publish(
                        topic=topic,
                        payload=message_jsonA,
                        qos=mqtt.QoS.AT_LEAST_ONCE)
                    
                    ## 

                    messageB = {
                        "id": str(id_counter+1000),
                        "date": datetime.now().strftime("%b %d %H:%M"),  # Month, day, hours, and minutes
                        "disconnectionDate": "",
                        "myState": "",
                        "powerConsumption": pandas_results['avg_current'],  # Average power consumption
                        "reconnectionDate": ""
                    }
                    print(f"Publishing message to topic '{topic}': {messageB}")
                    message_jsonB = json.dumps(messageB)
                    mqtt_connection.publish(
                        topic=topic,
                        payload=message_jsonB,
                        qos=mqtt.QoS.AT_LEAST_ONCE)
                    id_counter += 1
                    SerialDone = False  # Reset SerialDone after publishing
                else:
                    print("No data to publish")
            time.sleep(0.1)
    except KeyboardInterrupt:
        print("Publishing interrupted by user")
        save_id_counter(id_counter)

# Main Execution
if __name__ == '__main__':
    proxy_options = None
    if cmdData.input_proxy_host is not None and cmdData.input_proxy_port != 0:
        proxy_options = http.HttpProxyOptions(
            host_name=cmdData.input_proxy_host,
            port=cmdData.input_proxy_port)

    mqtt_connection = mqtt_connection_builder.mtls_from_path(
        endpoint=cmdData.input_endpoint,
        port=cmdData.input_port,
        cert_filepath=cmdData.input_cert,
        pri_key_filepath=cmdData.input_key,
        ca_filepath=cmdData.input_ca,
        on_connection_interrupted=on_connection_interrupted,
        on_connection_resumed=on_connection_resumed,
        client_id=cmdData.input_clientId,
        clean_session=False,
        keep_alive_secs=30,
        http_proxy_options=proxy_options,
        on_connection_success=on_connection_success,
        on_connection_failure=on_connection_failure,
        on_connection_closed=on_connection_closed)

    print(f"Connecting to {cmdData.input_endpoint} with client ID '{cmdData.input_clientId}'...")
    connect_future = mqtt_connection.connect()
    connect_future.result()
    print("Connected!")

    publish_topic = cmdData.input_topic
    publish_thread = threading.Thread(target=publish_messages, args=(mqtt_connection, publish_topic))
    publish_thread.start()

    try:
        while True:
            read_INA219_serial()
            SerialDone = True
    except KeyboardInterrupt:
        print("Serial reading interrupted by user")
        save_id_counter(id_counter)
