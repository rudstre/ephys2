from mpi4py import MPI
import h5py

rank = MPI.COMM_WORLD.rank 

if rank == 0:
	with h5py.File('parallel_test.hdf5', 'w') as f:
		f.create_dataset('test', (4,), dtype='i')
	print('File structure created')

MPI.COMM_WORLD.Barrier()

f = h5py.File('parallel_test.hdf5', 'a', driver='mpio', comm=MPI.COMM_WORLD)
f['test'][rank:rank+1] = rank
f.close()

print(f'Rank {rank} done')
