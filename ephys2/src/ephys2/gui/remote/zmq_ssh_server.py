'''
ZMQ over SSH tunnel
'''

import subprocess
import zmq
import numpy as np
import h5py

def run_oneliner(cmd: str) -> str:
	val = subprocess.check_output(cmd, shell=True)
	return val[:-1].decode('utf-8')

port = int(run_oneliner('for myport in {6818..11845}; do ! nc -z localhost ${myport} && break; done; echo $myport'))
compute_host = run_oneliner('echo $(hostname)')
compute_user = run_oneliner('echo $USER')
login_host = 'login.rc.fas.harvard.edu'

ssh_cmd = f'ssh -NL {port}:{compute_host}:{port} {compute_user}@{login_host}'

host = '0.0.0.0'
addr = f'tcp://{host}:{port}'

ctx = zmq.Context()
sock = ctx.socket(zmq.REP)
sock.bind(addr)

print(f'Server bound to {addr}')
print(f'Please run the following command in another terminal on your local machine:')
print(ssh_cmd)

def send_array(arr):
	sock.send_json({
		'dtype': str(arr.dtype),
		'shape': arr.shape,
	}, zmq.SNDMORE)
	return sock.send(arr, copy=False, track=False)

# Load h5py data
N = 10000
h5_path = '/n/holylfs02/LABS/olveczky_lab/Everyone/A049_ISOlabeled_snippets_test.h5'
with h5py.File(h5_path, 'r') as file:
	arr = file['6']['data'][:N]

while True:
	message = sock.recv()
	print(f'Received message: {message}')
	send_array(arr)
