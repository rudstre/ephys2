'''
Test idempotence
'''

from ephys2.lib.h5 import *

# path = '/Users/anandsrinivasan/dev/fasrc/data/mr_linked_snippets_isosplit.h5'

# file = h5py.File(path, 'r')

# d1 = H5LLVBatchSerializer.load(file['0'], 0, 10000)
# d2 = H5LLVBatchSerializer.load(file['0'], 5000, 15000, overlap=5000)
# dtot = H5LLVBatchSerializer.load(file['0'], 0000, 15000)

# d1.append(d2)

path1 = '/Users/anandsrinivasan/dev/fasrc/data/mr_linked_snippets_isosplit.h5'
path2 = '/Users/anandsrinivasan/dev/fasrc/data/mr_summarized_linked_snippets_isosplit.h5'
file1 = h5py.File(path1, 'r')
file2 = h5py.File(path2, 'r')
d1 = H5LLVMultiBatchSerializer.load(file1)
d2 = H5LLVMultiBatchSerializer.load(file2)