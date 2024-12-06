'''
ZMQ over SSH tunnel
'''

import zmq
import argparse
from timeit import default_timer 
import numpy as np

parser = argparse.ArgumentParser(description='Ephys2 command-line interface')
parser.add_argument('port', type=str, help='port')
args = parser.parse_args()
port = int(args.port)

host = 'localhost'
addr = f'tcp://{host}:{port}'

ctx = zmq.Context()
sock = ctx.socket(0|zmq.REQ)
sock.connect(addr)

print(f'Client connected to {addr}')

def recv_array():
	md = sock.recv_json(flags=0)
	msg = sock.recv(flags=0, copy=False, track=False)
	arr = np.frombuffer(memoryview(msg), dtype=md['dtype'])
	return arr.reshape(md['shape'])

print('Sending request...')
t0 = default_timer()
sock.send_string("Hello from client")
arr = recv_array()
dt = default_timer() - t0
print(f'Received array of shape {arr.shape} and type {arr.dtype} in {dt} seconds')