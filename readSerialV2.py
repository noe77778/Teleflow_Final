import serial
import time
import csv
from datetime import datetime, timedelta
##4
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

def main():
    serial_port = "/dev/ttyUSB0"
    baudrate = 115200
    csv_file_path = 'power_consumption_log.csv'

    ser = open_serial_port(serial_port, baudrate)

    if ser is None:
        return

    try:
        with open(csv_file_path, 'a', newline='') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(['Timestamp', 'Voltage (V)', 'Current (A)', 'Power (W)'])

        buffer = []
        start_time = datetime.now()
        end_time = start_time + timedelta(hours=1)

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
    
    finally:
        if ser and ser.is_open:
            ser.close()
            print("Serial port closed.")

if __name__ == "__main__":
    main()
