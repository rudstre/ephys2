#include <pybind11/pybind11.h>
#include <pybind11/numpy.h>
#include <stdlib.h>
#include <math.h>
#include <iostream>

#include "../include/ephys2/spc.h"
#include "../include/ephys2/utils.h"

namespace py = pybind11;

SPCResult super_paramagnetic_clustering(
	py::array_t<double> dists, 	// Matrix of pairwise distances between samples (N_samples, N_samples)
	const float Tmin, 					// Minimum temperature
	const float Tmax, 					// Maximum temperature
	const float Tstep, 					// Temperature step
	const size_t cyc,						// Total number of cycles
	const int K, 								// Maximal number of nearest neighbours (used in the knn algorithm)
	const bool MSTree, 					// Whether to add the edges of the minimal spanning tree (should default to True)
	const std::optional<int> seed		// Random seed
	)
// C++ port of Super-paramagnetic clustering implementation by Eytan Domany (https://github.com/eytandomany/SPC)
// Refactored in the following ways:
// * no side effects (no logfiles or environment variables)
// * exposes a library rather than an executable interface.
// * operates solely on distance matrices rather than feature vectors
// * does not save or export any non-label information
{
	const size_t N = dists.shape(0);
	py_assert(K < N, "Number of nearest neighbors can be at most the number of samples"); 
	py_assert(Tmin <= Tmax, "Tmin must be less than or equal to Tmax");

	if (seed) {
		srand(*seed);
	}

	// Default parameters (expose above if necessary)
	const size_t Q = 20;				// Number of Potts Spins; Si = 0,...,Q-1
	const float SWfract = 0.8; 	// The fraction SW sweeps for which averages are calculated. The first (1-SWfract)*cyc sweeps are discarded. 
	const float th_MIN = 0.5;		// Delta-threshold min
	const float th_MAX = 0.5; 	// Delta-threshold max 
	const float dth = 0.5; 			// The threshold on correlations between neighbors, above which they are assumed to belong to the same cluster.
	const float thN = 0.5; 			// The current threshold (loop parameter)

	// State initialization
	float T;              	/* Current temperature                       */
	unsigned int *Spin; 		/* Spin[i]= 0..Q-1 is the spin of point i    */
	UIRaggedArray NK;				/* Contains the neighbors of each point.     */
													/* NK.n is the number of points and NK.c[i]  */
													/* is the number of neighbours of point i.   */
													/* NK[i][j], j=1..NK.c[i] are the labels of  */
													/* neighboring points for each i=1..NK.n     */
	UIRaggedArray KN;				/* KN[i][k] = m, means that point i is the   */
													/* m-th neighbor of point j = N[i][k]        */
	RaggedArray P;					/* Deletion Probabilities for a satisfied    */
													/* bond, i.e. if S[i] = S[j]. For an         */
													/* unsatisfied bond deletion probability = 1 */
	CRaggedArray Bond;			/* Bond[i][k] takes value 1 (0) if bond      */
													/* between spins i and its k-th neighbor is  */
													/* frozen (deleted).                         */
	unsigned int *ClusterSize; /* ClusterSize[n] contains the number of    */
													/* points belonging to cluster n in the      */
													/* current configuration. The clusters are   */
													/* ordered fron the biggest (n=1) to the     */
													/* smallest                                  */
	unsigned int *Block;		/* Block[i] Is the number of the cluster to  */
													/* which Spin[i] belongs                     */
	unsigned int *UIWorkSpc;/* auxiliary work space                      */
	unsigned int *dgOldBlock;/* dgOldBlock[i] Is the number of the cluster*/
													/* to which Spin[i] belonged in the previous */
													/* temperature after directed growth         */
	unsigned int *thOldBlock;/* OldBlock[i] Is the number of the cluster  */
													/* to which Spin[i] belonged in the previous */
	                        /* temperature after thresholding            */
	UIRaggedArray CorrN;    /* Two Points Correlations comulant          */
	int nc;            			/* present number of clusters                */
	int nb;            			/* present number of frozen bonds            */
	int ncy;      					/* cyles counter											       */
	size_t nT;            	/* Temp. step counter                         */
	int i;									/* auxiliary loop index                       */

	// Neighbors
	NK.n = 0;
	NK = knn(N, K, MSTree, dists);
  OrderEdges( &NK ); /* Edges *must* be ordered when calling SetBond() */
  KN = InvertEdges( NK );
  EdgeDistanceResult edr = EdgeDistance( NK, dists );
	assure( edr.nedges > 0, "no edges" );

	DistanceToInteraction( edr, NK, KN );

	// Memory allocations
  CorrN = InitUIRaggedArray(NK);
  Bond = InitCRaggedArray(NK);
  P = InitRaggedArray(NK);
  ClusterSize = InitUIVector(N);
  Block = InitUIVector(N);
  UIWorkSpc = InitUIVector((2*N>Q)?2*N:Q); // bounds on UIWorkSpc size: >=Q for magnetization >=2N for OrderingClusters  
  Spin = InitUIVector(N);
  InitialSpinConfig(N,Spin,Q); 

  dgOldBlock = InitUIVector(N);  
  thOldBlock = InitUIVector(N);
  memset( dgOldBlock, 0, N*sizeof(unsigned int) );
  memset( thOldBlock, 0, N*sizeof(unsigned int) );

  // Results
  std::vector<unsigned int> clusters;
  std::vector<float> temps;


	/*********************** START T LOOP **********************/
	for(T = Tmin, nT = 0; T <= Tmax; nT++, T=T+Tstep ) { // TODO: infinite loop if Tmin == Tmax

		/* Memory reset: */
		ResetUIRaggedArray(CorrN);
		ResetCRaggedArray(Bond);
		ResetRaggedArray(P);

		DeletionProbabilities(T,edr.J,P);

		/* Transient of Monte Carlo (not included in averages) */
		for( i = 0; i < cyc*(1.-SWfract); i++ ){
			nb = SetBond(P,Spin,Bond,NK,KN); 
			nc = Coarsening(Bond,Block,NK,ClusterSize,UIWorkSpc);
			NewSpinConfig(N,Spin,Block,nc,Q,UIWorkSpc);
		}

		/***************** START MC LOOP ********************/     
		for( ncy = 0; ncy <= cyc*SWfract ; ncy++ ){

			nb = SetBond(P,Spin,Bond,NK,KN); 
			nc = Coarsening(Bond,Block,NK,ClusterSize,UIWorkSpc);
			NewSpinConfig(N,Spin,Block,nc,Q,UIWorkSpc);

			GlobalCorrelation(CorrN,NK,Block);
		} /********************* END MC LOOP *********************/

		/* threshold + directed growth */
		nc = DirectedGrowth(ncy,thN,CorrN,NK,KN,Bond,Block,ClusterSize,dgOldBlock,thOldBlock,UIWorkSpc);
		/* Notice that above thOldBlock is the new thBlocks but */
		/* it is OK to use them */  

		// Write cluster assignments in row-major order
		clusters.insert(clusters.end(), Block, Block+N);
		temps.push_back(T);

		memcpy( thOldBlock, Block, N*sizeof(unsigned int) );
		memcpy( dgOldBlock, Block, N*sizeof(unsigned int) );

	}   /******************** END OF T LOOP ***********************/

	FreeUIRaggedArray(CorrN);
	FreeCRaggedArray(Bond);
	FreeRaggedArray(P);
	free(ClusterSize);
	free(Block);
	free(UIWorkSpc);

	FreeUIRaggedArray(NK);
	FreeUIRaggedArray(KN);
	FreeRaggedArray(edr.J);
	free(Spin);
	free(dgOldBlock);
	free(thOldBlock);

  return {
  	seq2numpy(temps, {nT}),
  	seq2numpy(clusters, {nT, N})
  };
}

// C++ port of edge utility functions

/**
   \section{knn}
   \subsection{Description}
   Creates a mutual K nearest neighbours array.
   Fuses it with a minimal spanning tree if required.
   \subsection{Input parameters}
   \begin{itemize}
   \item[N] Number of points.
   \item[K] Number of nearest neighbors.
   \item[X] is the distance matrix. \\
   \end{itemize}
   \subsection{Return value}
   \begin{itemize}
   \item[nk] nk.p[i] is the list of neighbours of vertex i.
   \end{itemize}
   \subsection{file}
   Ported from edge.c
**/

UIRaggedArray knn(const size_t N, const size_t K, const bool MSTree, py::array_t<double> dists ) 
{
	double  *dist;		/* distances      */
	int    **MNV;	/* Nearest neighbours array */
	unsigned int    *indx;	/* auxiliar */
	UIRaggedArray   nk;        /* returned array */
	unsigned int **edg;        /* edges of mst */
	unsigned int *occ;
	auto X = dists.unchecked<2>(); // Check that the array has 2 dimensions; give bounds-check-free access to underlying data

	unsigned int i,j,k,cand;

	dist = (double*) calloc(N,sizeof(double));
	MNV = InitIMatrix(N,K);
	indx = InitUIVector(N);

	/* Ordering of the neighbours - O(N^2 logN)*/
	for(i = 0; i < N; i++) {
		for(j = 0; j < N; j++) {
			dist[j] = X(i,j);
		}
		dist[i] = INFINITY;

		DSortIndex(N,dist,indx);
		for(j = 0; j < K; j++) {
			MNV[i][j] = indx[j];
		}
	}
	free(indx); free(dist);

	if( MSTree ) {
		edg = InitUIMatrix(N-1,2);
		mstree(N,dists,edg);
	}

	/* Check for mutuality - O(NK^2) */
	for (i=0;i<N;i++) {
		for(j=0;j<K;j++) {
			if (MNV[i][j]<0) {// This is hiding a bug -- this is an index and should never be negative
				continue;
			}
			cand = MNV[i][j];	// Candidate becomes ngbr if its mutual 
			for(k=0;k<K && MNV[cand][k] != i;k++);
			MNV[i][j] -= (MNV[i][j] + 1) * (K==k); // If the candidate is rejected its name is replaced by (-1). 
		}
	}

	/* Construction of the nk matrix O(NK)*/
	nk.n = N;
	nk.c = (unsigned int*)calloc(N,sizeof(unsigned int));
	nk.p = (unsigned int**)calloc(N,sizeof(unsigned int*));
	occ = (unsigned int*)calloc(N,sizeof(unsigned int));
	for(i = 0; i < N; i++) {     
		for (j=0;j<N;j++)
			occ[j]=0; 
		for(j = 0; j < K; j++)
			occ[MNV[i][j]]+=(MNV[i][j]>=0);

		if (MSTree) {
			for(j=0;j<(N-1);j++)
				if (edg[j][0]==i)
					occ[edg[j][1]]++;
				else if (edg[j][1]==i)
					occ[edg[j][0]]++;
		}

		for (j=0;j<N;j++)
			nk.c[i]+=(occ[j]>0);
		nk.p[i] = (unsigned int*)calloc(nk.c[i],sizeof(unsigned int));
		for (k=0,j=0;j<N;j++)
			if (occ[j]) 
				nk.p[i][k++]=j;
	}
	if (MSTree)
		FreeUIMatrix(edg,N-1);
	FreeIMatrix(MNV,N);
	free(occ);

	return nk;
}


/* -------------------------------------------------------------------- */
/**
   \section{mstree}
   \subsection{Prim's Algorithm}
   \begin{enumerate}
   \item Set $i=0$, $S_0= \{u_0=s\}$, $L(u_0)=0$, and $L(v)=\inf$ for $v \neq u_0$. 
   If $|V| = 1$ then stop, otherwise go to step 2. 
   \item For each $v$ in $V \setminus S_i$, 
   replace $L(v)$ by $\min\{L(v), d_{v,u_i}\}$. 
   If $L(v)$ is replaced, put a label $(L(v), u_i)$ on $v$. 
   \item Find a vertex $v$ which minimizes $\{L(v) | v \in V \setminus S_i\}$, 
   say $u_{i+1}$. 
   \item Let $S_{i+1} = S_i \cup \{u_{i+1}\}$. 
   \item Replace $i$ by $i+1$. If $i=|V|-1$ then stop, otherwise go to step 2. 
   \end{enumerate}
   The time required by Prim's algorithm is $O(|V|^2)$. \\
   It can be reduced to $O(|E|\log|V|)$ if heap is used (but i didn't bother).
   \subsection{Input parameters}
   \begin{itemize}
   \item[N] number of points
   \item[d] distance matrix
   \end{itemize}
   \subsection{Output parameters}
   \begin{itemize}
   \item[**edg] the edges of the minimal spanning tree. Edge i is between
           vertices edg[i][0] and edg[i][1].
   \end{itemize}
   \subsection{file}
   Ported from edge.c
**/
/* -------------------------------------------------------------------- */
void mstree(const size_t N, py::array_t<double> dists, unsigned int** edg) 
{
	int i,j,mi,u;
	float ml;
	int* V = (int*)calloc(N,sizeof(int));
	float* L = (float*)calloc(N,sizeof(float));
	int* label = (int*)calloc(N,sizeof(int));
	double d;
	auto X = dists.unchecked<2>(); // Check that the array has 2 dimensions; give bounds-check-free access to underlying data

	for (i=0;i<(N-1);i++) {
		V[i] = i;
		L[i] = INFINITY;
	}

	u = N-1;
	for (i=0;i<(N-1);i++) {
		ml = INFINITY;
		for(j=0;j<(N-i-1);j++) {
			d = X(u,V[j]);

			if (d<=L[j]) {
				L[j] = d;
				label[j]=u;
			}
			if (L[j]<=ml) {
				ml = L[j];
				mi = j;
			}
		}
		edg[i][0] = label[mi]; 
		edg[i][1] = V[mi];
		u = V[mi];
		V[mi] = V[N-i-2];
		L[mi] = L[N-i-2];
		label[mi] = label[N-i-2];
	}
}

EdgeDistanceResult EdgeDistance( UIRaggedArray NK, py::array_t<double> dists )
{
	int i,k;
	EdgeDistanceResult edr;
	auto X = dists.unchecked<2>(); // Check that the array has 2 dimensions; give bounds-check-free access to underlying data

	edr.chd = 0.0; 
	edr.nedges = 0;
	edr.J = InitRaggedArray( NK );

	for(i=0; i < edr.J.n; i++){
		for(k = 0; k<edr.J.c[i]; k++ ) {
			edr.J.p[i][k] = X(i,NK.p[i][k]);
			if( edr.J.p[i][k] < INFINITY ) edr.chd+=edr.J.p[i][k], edr.nedges++;
		}
	}
	edr.nedges /= 2;

	edr.nn =  2.0 * (float)edr.nedges / (float)edr.J.n;
	edr.chd = edr.chd / (2.0 * (float)edr.nedges);

	return edr;
}
