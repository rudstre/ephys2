#include "../../include/spc/SW.h"

/* -------------------------------------------------------------------- */
/*  Distance: returns the euclidean distance between data poins i and j */
/* -------------------------------------------------------------------- */
double Distance(int D, double *X, double *Y) {
  int d;
  double dist = 0.0;
  double diff;
  for (d = 0; d <  D; d++){
    diff = X[d] - Y[d]; 
    dist += diff * diff;
  }
  return( sqrt(dist) );
} 

/* -------------------------------------------------------------------- */
/*  Distance_Linf: returns the L-infinity distance between data poins i */
/*                 and j                                                */
/* -------------------------------------------------------------------- */
double Distance_Linf(int D, double *X, double *Y) {
  int d;
  double dist;
  double diff;
  dist = 0.0;
  for (d = 0; d <  D; d++){
    diff = fabs(X[d] - Y[d]); 
    if (dist < diff) dist = diff;
  }
  return( dist );
} 

void DistanceToInteraction( EdgeDistanceResult edr, UIRaggedArray NK, UIRaggedArray KN )
{
	int i, k;
	float dd;

	/* the interactions are calculated */
	for(i = 0; i < edr.J.n; i++)
		for( k = edr.J.c[i]-1; NK.p[i][k]>i && k>=0; k-- ) {
			dd = (edr.J.p[i][k]*edr.J.p[ NK.p[i][k] ][ KN.p[i][k] ])/(edr.chd*edr.chd);
			edr.J.p[i][k] = edr.J.p[ NK.p[i][k] ][ KN.p[i][k] ] = exp(-dd/2.0) / edr.nn;
		}
}








