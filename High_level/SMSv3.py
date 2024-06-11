#!/usr/bin/python

import RPi.GPIO as GPIO
import serial
import time
import argparse

# Initialize the argument parser
parser = argparse.ArgumentParser(description='Send SMS using SIM7600X module')
parser.add_argument('--phone_number', type=str, required=True, help='Phone number to send the message to')
parser.add_argument('--text_message', type=str, required=True, help='Text message to send')

# Parse the arguments
args = parser.parse_args()

ser = serial.Serial("/dev/ttyUSB2", 115200)
ser.flushInput()

phone_number = args.phone_number
text_message = args.text_message
power_key = 6
rec_buff = ''

def send_at(command, back, timeout):
    rec_buff = ''
    ser.write((command + '\r\n').encode())
    time.sleep(timeout)
    if ser.inWaiting():
        time.sleep(0.01)
        rec_buff = ser.read(ser.inWaiting())
    if back not in rec_buff.decode():
        print(command + ' ERROR')
        print(command + ' back:\t' + rec_buff.decode())
        return 0
    else:
        return 1

def SendShortMessage(phone_number, text_message):
    answer = send_at("AT+CMGS=\"" + phone_number + "\"", ">", 2)
    if 1 == answer:
        ser.write(text_message.encode())
        ser.write(b'\x1A')
        answer = send_at('', 'OK', 5)
        if 1 == answer:
            print('send successfully')
        else:
            print('error')
    else:
        print('error%d' % answer)

def power_on(power_key):
    print('SIM7600X is starting:')
    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)
    GPIO.setup(power_key, GPIO.OUT)
    time.sleep(0.1)
    GPIO.output(power_key, GPIO.HIGH)
    time.sleep(0.1)
    GPIO.output(power_key, GPIO.LOW)
    time.sleep(0.1)
    ser.flushInput()
    print('SIM7600X is ready')

def power_down(power_key):
    print('SIM7600X is logging off:')
    GPIO.output(power_key, GPIO.HIGH)
    time.sleep(3)
    GPIO.output(power_key, GPIO.LOW)
    time.sleep(1)
    print('Good bye')

#power_on(power_key)
#SendShortMessage(phone_number, text_message)
#time.sleep(4)


try:    
    power_on(power_key)
    SendShortMessage(phone_number,text_message)
    power_down(power_key)
    print('Action completed')
except :
	if ser != None:
		ser.close()
	GPIO.cleanup()
