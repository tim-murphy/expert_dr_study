import keyboard
import os
from random import random
import socket
import sys
import time

# Host machine IP
HOST = '127.0.0.1'
# Gazepoint Port
PORT = 4242
ADDRESS = (HOST, PORT)

# (approximate) number of data points to replay per second. This does not have
# to match the refresh rate as a timestamp is encapsulated in the data and used
# by Gazepoint Analysis for timing.
REPLAY_RATE = 1000

def replay_from_file(input_file):
    if not os.path.exists(input_file):
        raise ValueError("Input file does not exist: " + input_file)

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((HOST, PORT))
        s.listen()
        conn, addr = s.accept()
        with conn:
            print("Ready! Press space to start sending data")
            while True:
                conn.send(str.encode("<ACK ID=\"USER_DATA\" VALUE=\"Loading...\" />"))
                if keyboard.is_pressed(" "):
                    break
                time.sleep(1/REPLAY_RATE)

            print("Sending data...", end='', flush=True)
            with open(input_file, 'r') as infile:
                for outstr in infile:
                    conn.send(str.encode(outstr + '\r\n'))
                    # uncomment to see each output line
                    # print(outstr)
                    time.sleep(1/REPLAY_RATE)

            print("done")

if __name__ == '__main__':
    if not len(sys.argv) > 1:
        print("Usage: " + __file__ + " <input_data>", file=sys.stderr)
        sys.exit(1)

    input_file=sys.argv[1]

    replay_from_file(input_file)

# EOF
