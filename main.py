import time
import struct
import serial
import serial.tools.list_ports
import datetime as dt
import os
import numpy as np
import telemetry_csv as tc
import sensor_list_test as sl

# from digi.xbee.devices import XBeeDevice

valid_name = False
while not valid_name:
    user_filename = input("""Please name the output data file. Note: Naming a file that already exists will append to that file. 
        Leaving this blank will automatically name the file based on the current date and time: """)
    if user_filename != "":
        csv_name = "Telemetry_Data/"+user_filename+".csv"
    else:
        csv_name = "Telemetry_Data/"+str(dt.datetime)+".csv"

    if not os.path.exists(csv_name):
        try:
            open(csv_name, 'w', newline="")
            valid_name = True
        except:
            print("\nNot a valid name, please try again.\n")
    else:
        valid_name = True

#"Telemetry_Data/test_data.csv"


def select_serial_port():
    ports = list(serial.tools.list_ports.comports())
    for p in ports:
        # index 1 of p is the name of the port, this works only for windows, MacOS uses 0
        if 'Serial Port' in p[1]:
            return serial.Serial(p[0], 9600)
    print("Cannot find comport for xbee")

try:
    device.close()
except:
    None

print("hi")

''' Establish serial device connection '''
# device = serial.Serial('\\dev\\tty.usbserial-D306E0R6', 9600)
device = select_serial_port()
# print(device)

if device != None:
    ''' Wait for connection to establish '''
    while (device.inWaiting() == 0):
        print('waiting')
        time.sleep(2)
        pass

    print("Data received!")
    time.sleep(1)

    index = 0
    start_time = time.time()
    size = (len(sl.all_xbee_sensors)+1) * 2 # for consistency, -1 from time, +1 for parity byte
    id_bytes = b'\x80\x01'

    sig_list = np.ones(size)  # multiplications for each sensor values turning short back to float, default as 1 for now

    tc.csv_create_header(csv_name, sl.all_xbee_sensors)


    while True:
        current_time = round(time.time() - start_time, 2)
        ''' read input stream, works like a stack '''
        raw_values = device.read_until(id_bytes, size)
        # MAKE SURE THE STRING FILE HAS THE CORRECT SIZE, OTHERWISE ABANDON DATA
        if (raw_values[len(raw_values) - 2:len(raw_values)] != id_bytes) | (len(raw_values) < size):
            # print("Warning, incorrect identifier, second chance")
            raw_values += device.read_until(id_bytes, size)
            if raw_values[len(raw_values) - 2:len(raw_values)] != id_bytes:
                print("Second chance fail at: " + str(current_time))
                print(raw_values)
                time.sleep(0.1)
                device.flushInput()
                continue
        ''' decoode "byte" type and remove newline char '''
        # v = raw_values.decode('utf-8', errors='ignore').strip('\n').strip('\r')
        tuple_values = struct.unpack('>'+'h'*(size//2), raw_values[len(raw_values)-size:len(raw_values)])  # data type: tuple

        sensor_values = np.asarray(tuple_values[:len(tuple_values)-1]) / (10 ** 1) ## sig_list
        print("time: " + str(current_time) + " and size of raw values is " + str(len(raw_values)) + " and size of sensor_values is " +  str(len(sensor_values)))
        print(sensor_values[1])

        csv_list = np.concatenate((np.array([index, current_time]), sensor_values))
        index += 1
        
        tc.csv_store_data(csv_name, sl.all_xbee_sensors, csv_list)
        print(csv_list)

        ''' wait '''
        time.sleep(0.1)  # default 0.1
        ''' flush input stream '''
        device.flushInput()
