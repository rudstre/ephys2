
class H5CSRReserializer_DS(H5BatchReserializer):
	'''
	Direct-sum-mode reserializer for CSR matrices.
	'''

	def __init__(self, h5dirs: List[H5Dir], src_idx: int):
		self.data_reserializer = H5ArrayReserializer([h5dir['data'] for h5dir in h5dirs], src_idx)
		self.indices_reserializer = H5ArrayReserializer([h5dir['indices'] for h5dir in h5dirs], src_idx)
		self.indptr_reserializer = H5ArrayReserializer([h5dir['indptr'] for h5dir in h5dirs], src_idx)
		self.shape = np.array([0, 0], dtype=np.int64)
		self.all_end_shapes = []
		for a_dir in h5dirs:
			end_shapes = a_dir['shapes'][:].cumsum(axis=0) # Computes final shapes corresponding to direct sum
			self.shape += end_shapes[-1]
			self.all_end_shapes.append(end_shapes)
		self.src_idx = src_idx
		self.P = len(h5dirs)

	def create(self, out_dir: H5Dir, name: str):
		subdir = out_dir.create_group(name)
		subdir.attrs['shape'] = tuple(self.shape)
		self.data_reserializer.create(subdir, 'data')
		self.indices_reserializer.create(subdir, 'indices')
		self.indptr_reserializer.create(subdir, 'indptr')

	def start(self) -> MultiIndex:
		self.ctr = 0
		self.ctr_max = self.all_end_shapes.shape[0]
		(i1,) = self.data_reserializer.start()
		(i2,) = self.indices_reserializer.start()
		(i3,) = self.indptr_reserializer.start() - self.src_idx # Remove intermediate leading zeros
		c = 0 # num columns
		for i in range(self.src_idx):
			c += self.all_end_shapes[i][0][1]
		return (i1, i2, i3, c)

	def advance(self, out_dir: H5Dir, name: str, iat: MultiIndex, data: CSRMatrix) -> MultiIndex:
		(i1, i2, i3, c) = iat
		# Direct sum mode: offset indices and indptr by existing data
		(i2,) = self.indices_reserializer.advance(outdir[name], 'indices', (i2,), data.indices + c)
		if self.ctr == 0 and self.src_idx == 0:
			# First batch, first worker: keep leading 0
			assert i1 == 0
			(i3,) = self.indptr_reserializer.advance(outdir[name], 'indptr', (i3,), data.indptr[1:])
		else:
			# Otherwise, uppress leading conventional 0 of indptr
			(i3,) = self.indptr_reserializer.advance(outdir[name], 'indptr', (i3 - 1,), data.indptr[1:] + i1) 
		(i1,) = self.data_reserializer.advance(outdir[name], 'data', (i1,), data.data)
		Nzeros = self.ctr * self.P + self.src_idx
		c = 0 # num columns
		# TODO: there is an error here, but this class is not used (for now).
		raise NotImplementedError
		for i in range(self.src_idx):
			c += self.all_end_shapes[i][self.ctr][1]
		if self.ctr < self.ctr_max - 1:
			for i in range(self.src_idx, self.P):
				c += self.all_end_shapes[i][self.ctr - 1][1]
		self.ctr += 1
		return (i1, i2, i3 - Nzeros, c)