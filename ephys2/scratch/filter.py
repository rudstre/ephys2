'''
Signal filtration
'''

from typing import List
from dataclasses import dataclass

import pdb
import numpy as np
from numpy import ndarray
from scipy import signal

@dataclass
class IIRFilter:
    '''
    Specification for an impulse-response filter with the estimated impulse-response length.

    sos : ndarray
        Second-order sections representation of the IIR filter.
        Initial-conditions for steady-state step-response (see `signal.lfilter_zi`)
    sos_zi : ndarray
        Initial conditions suitable for use with ``sosfilt``, shape
        ``(n_sections, 2)``.
    '''
    sos: ndarray
    sos_zi: ndarray

def approx_irlen(a_coeffs: ndarray, b_coeffs: ndarray) -> int:
    '''
    Approximate the impulse-response length of a filter.
    See https://docs.scipy.org/doc/scipy/reference/generated/scipy.signal.filtfilt.html

    Parameters
    ----------
    a_coeffs : (N,) Tensor
        The denominator coefficient vector of the filter.  If ``a[0]``
        is not 1, then both `a` and `b` are normalized by ``a[0]``.
    b_coeffs : (N,) Tensor
        The numerator coefficient vector of the filter.
    

    Returns
    -------
    irlen : int 
        The length of the impulse response of the filter.  
    '''
    z, p, k = signal.tf2zpk(a_coeffs, b_coeffs)
    eps = 1e-9
    r = np.max(np.abs(p))
    irlen = int(np.ceil(np.log(eps) / np.log(r)))
    return irlen

def filtfilt_even_cu(X: ndarray, filter: IIRFilter, padlen: int) -> Tensor:
    '''
    Mirrors scipy filtfilt() implementation with Torch backend; uses even-symmetric padding.
    Heavily borrows from https://docs.scipy.org/doc/scipy/reference/generated/scipy.signal.filtfilt.html

    Parameters
    ----------
    X : (N, T) ndarray
        The signals to be filtered (N-dimensional, last dimension is time.)
    

    Returns
    -------
    y : (N, T) ndarray
        The filtered output with the same shape as `x`.
    '''
    assert padlen >= 0
    X = cp.asarray(X) # TODO: move to GPU

    # Apply even extension
    X = cp.concatenate((X[:, padlen::-1], X, X[:, padlen:-1]), axis=1)

    # Forward / backward filters
    X = cusignal.filtering.sosfilt(filter.sos, X)
    X = cp.flip(cusignal.filtering.sosfilt(filter.sos, cp.flip(X, axis=1)), axis=1)

    # De-pad
    X = X[:, padlen:-padlen]

    # For benchmarking
    # X.device.synchronize()

    return X

def make_iir(sos: ndarray) -> IIRFilter:
    return IIRFilter(
        cp.asarray(sos), 
        cp.asarray(signal.sosfilt_zi(np.asarray(sos)))
    )

def median_filter(X: ndarray) -> ndarray:
    '''
    Reduce by median along the second-to-last dimension.
    '''
    return X.median(dim=-2)[0]
