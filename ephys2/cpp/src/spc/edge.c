#include "../../include/spc/utilities.h"
#include "../../include/spc/SW.h"

/* An auxiliary function for OrderEdges()                     */
/* returns the opposite result to that of uicompare in aux2.c */
int uicomp(const void *i, const void *j)
{ return (int)( *((unsigned int*)i) - *((unsigned int*)j) ); }

/**
   \section{OrderEdges}
   \subsection{Description}
   order the sub arrays of a ragged array in ascending order.
    \subsection{Input parameters}
   \begin{itemize}
    \item[NK] the ragged array to be ordered.
   \end{itemize}
    \subsection{Output parameters}
   \begin{itemize}
    \item[NK] The ordereded array.
         NK.p[i][j] $<$ NK.p[i][l] $\iff$ j $<$ l.
   \end{itemize}
   \subsection{Auxiliary function}
   int uicomp(const void *i, const void *j)
   \subsection{file}
   edge.c
**/    
void OrderEdges( UIRaggedArray *nk ) {
   int i, j;
   for( i=0; i<nk->n; i++ )
      qsort(nk->p[i],nk->c[i],sizeof(unsigned int),uicomp);   
}
	 
/**
    \section{InvertEdges}
    \subsection{Description}
    creates an inverted ragged array.
    \subsection{Input parameters}
   \begin{itemize}
    \item[NK] the ragged array to be inverted.
   \end{itemize}
    \subsection{Return value}
   \begin{itemize}
    \item[M] The inverted array.
        If k=NK.p[i][j] and i=NK.p[k][l] then M.p[i][j]=l.
   \end{itemize}
   \subsection{file}
   edge.c
**/    
UIRaggedArray InvertEdges(UIRaggedArray NK){
   UIRaggedArray M;
   int i,j,k,k0;
   int npts;

   M = InitUIRaggedArray( NK );

   for(i=0; i < NK.n; i++)
      for(k = 0; k < NK.c[i]; k++) {
	 k0 = 0;
	 while(NK.p[ NK.p[i][k] ][ k0 ] != i) k0++;
	 M.p[i][k] = k0;
      }

   return M;
}
