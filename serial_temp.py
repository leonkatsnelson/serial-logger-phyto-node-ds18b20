import serial
from datetime import datetime
import csv
import os
import glob
import argparse

DATETIME_FMT = "%Y-%m-%dT%H:%M:%S.%f"

def int_from_bytes(xbytes: bytes) -> int:
    return int.from_bytes(xbytes, 'big')

def main():
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description="Serial Data Logger")
    parser.add_argument("--port", type=str, required=True, help="Serial port to read data from (e.g., /dev/ttyACM1)")
    parser.add_argument("--path", type=str, required=True, help="Directory to store CSV files")
    args = parser.parse_args()

    # Directory to store the data in
    print(args.path)
    directory = os.path.abspath(args.path)
    if not os.path.exists(directory):
        os.makedirs(directory)

    serial_ports = [args.port]  # Use the specified port

    serial_instances = {}  # Storing the serial instances

    for port in serial_ports:
        try:
            ser = serial.Serial(port, 19200, timeout=1)
            ser.flushInput()  # Clear any existing data in the input buffer
            serial_instances[port] = ser  # Add the port as an instance
        except Exception as e:
            print(f"Error opening serial port {port}: {e}")
            return

    header = ["timestamp", "T1_leaf", "T2_leaf", "T1_air", "T2_air"]  # Headers for the CSV file
    start_timestamp = datetime.now().strftime(DATETIME_FMT)
    last_csv_time = datetime.now()

    while True:  # Loop to read the data from the ports
        for port, ser in serial_instances.items():
            ser_bytes = ser.readline()
            try:  # Checking the format of the incoming data
                if (ser_bytes[0] != 80 and ser_bytes[-1] != 35) or len(ser_bytes) == 0 or len(ser_bytes) != 11:  # *P3#
                    continue
            except Exception as e:
                continue

            file_prefix = chr(ser_bytes[0]) + str(ser_bytes[1])
            print("prefix:",file_prefix)

            # Parse temperature data
            T1 = ser_bytes[2] + ser_bytes[3] / 10
            T2 = ser_bytes[4] + ser_bytes[5] / 10
            T3 = ser_bytes[6] + ser_bytes[7] / 10
            T4 = ser_bytes[8] + ser_bytes[9] / 10
            print(T1, T2, T3, T4)

            # Timestamp for the data
            timestamp = datetime.now().strftime(DATETIME_FMT)

            # Create a directory for the file prefix
            specific_directory = directory

            current_time = datetime.now()
            if current_time.hour in {0, 14} and current_time.hour != last_csv_time.hour:  # Create new file every 12 hours
                last_csv_time = datetime.now()
                start_timestamp = datetime.now().strftime(DATETIME_FMT)
                print("New file: ", start_timestamp)

            if not os.path.exists(specific_directory):
                os.makedirs(specific_directory)

            file_path = os.path.join(specific_directory, f"{file_prefix}_{start_timestamp}.csv")
            print("file_path:",file_path)

            # Write to the CSV file
            with open(file_path, "a") as f:  # Writing the CSV file
                writer = csv.writer(f, delimiter=",")

                if os.path.getsize(file_path) == 0:  # For empty files write the header row
                    writer.writerow(header)

                writer.writerow([timestamp, T1, T2, T3, T4])  # Write the data row containing timestamp, data

if __name__ == "__main__":
    main()
