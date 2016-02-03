from math import sqrt,pi
import numpy as np
from flavio.physics.bdecays.common import lambda_K, beta_l, meson_quark, meson_ff
from flavio.physics.bdecays.wilsoncoefficients import wctot_dict
from flavio.physics.bdecays import matrixelements
from flavio.physics import ckm
from flavio.physics.bdecays.formfactors import FormFactorParametrization as FF
from flavio.config import config
from flavio.physics.running import running
from .amplitudes import *
from scipy.integrate import quad

"""Functions for exclusive $B\to V\ell^+\ell^-$ decays."""

def dGdq2(J):
    return 3/4. * (2 * J['1s'] + J['1c']) - 1/4. * (2 * J['2s'] + J['2c'])

def dGdq2_ave(J, J_bar):
    return ( dGdq2(J) + dGdq2(J_bar) )/2.

# denominator of S_i and A_i observables
def SA_den(J, J_bar):
    return 2*dGdq2_ave(J, J_bar)

def S_theory(J, J_bar, i):
    r"""CP-averaged angular observable $S_i$ in the theory convention."""
    return S_theory_num(J, J_bar, i)/SA_den(J, J_bar)

# numerator
def S_theory_num(J, J_bar, i):
    return (J[i] + J_bar[i])

def A_theory(J, J_bar, i):
    r"""Angular CP asymmetry $A_i$ in the theory convention."""
    return A_theory_num(J, J_bar, i)/SA_den(J, J_bar)

# numerator
def A_theory_num(J, J_bar, i):
    return (J[i] - J_bar[i])

def S_experiment(J, J_bar, i):
    r"""CP-averaged angular observable $S_i$ in the LHCb convention.

    See eq. (C.8) of arXiv:1506.03970v2.
    """
    return S_experiment_num(J, J_bar, i)/SA_den(J, J_bar)

# numerator
def S_experiment_num(J, J_bar, i):
    if i in [4, '6s', '6c', 7, 9]:
        return -S_theory_num(J, J_bar, i)
    return S_theory_num(J, J_bar, i)

def A_experiment(J, J_bar, i):
    r"""Angular CP asymmetry $A_i$ in the LHCb convention.

    See eq. (C.8) of arXiv:1506.03970v2.
    """
    return A_experiment_num(J, J_bar, i)/SA_den(J, J_bar)

# numerator
def A_experiment_num(J, J_bar, i):
    if i in [4, '6s', '6c', 7, 9]:
        return -A_theory_num(J, J_bar, i)
    return A_theory_num(J, J_bar, i)

def Pp_experiment(J, J_bar, i):
    r"""Observable $P'_i$ in the LHCb convention.

    See eq. (C.9) of arXiv:1506.03970v2.
    """
    Pp_to_S = {4: 4, 5: 5, 6: 7, 8: 8}
    if i not in Pp_to_S.keys():
        return ValueError("Observable P'_" + i + " not defined")
    denom = sqrt(FL(J, J_bar)*(1 - FL(J, J_bar)))
    return S_experiment(J, J_bar, Pp_to_S[i]) / denom

def AFB_experiment(J, J_bar):
    r"""Forward-backward asymmetry in the LHCb convention.

    See eq. (C.9) of arXiv:1506.03970v2.
    """
    return AFB_experiment_num(J, J_bar)/SA_den(J, J_bar)

def AFB_experiment_num(J, J_bar):
    return 3/4.*S_experiment_num(J, J_bar, '6s')

def AFB_theory(J, J_bar):
    """Forward-backward asymmetry in the original theory convention.
    """
    return AFB_theory_num(J, J_bar)/SA_den(J, J_bar)

def AFB_theory_num(J, J_bar):
    return 3/4.*S_theory_num(J, J_bar, '6s')

def FL(J, J_bar):
    r"""Longitudinal polarization fraction $F_L$"""
    return FL_num(J, J_bar)/SA_den(J, J_bar)

def FL_num(J, J_bar):
    return -S_theory_num(J, J_bar, '2c')

def FLhat(J, J_bar):
    r"""Modified longitudinal polarization fraction for vanishing lepton masses,
    $\hat F_L$.

    See eq. (32) of arXiv:1510.04239.
    """
    return FLhat_num(J, J_bar)/SA_den(J, J_bar)

def FLhat_num(J, J_bar):
    return -S_theory_num(J, J_bar, '1c')


def bvll_obs(function, q2, wc_obj, par, B, V, lep):
    scale = config['renormalization scale']['bvll']
    label = meson_quark[(B,V)] + lep + lep # e.g. bsmumu, bdtautau
    wc = wctot_dict(wc_obj, label, scale, par)
    ml = par[('mass',lep)]
    mB = par[('mass',B)]
    mV = par[('mass',V)]
    mb = running.get_mb(par, scale)
    N = prefactor(q2, par, B, V, lep)
    ff = get_ff(q2, par, B, V)
    h = helicity_amps(q2, wc, par, B, V, lep)
    h_bar = helicity_amps_bar(q2, wc, par, B, V, lep)
    J = angular.angularcoeffs_general_v(h, q2, mB, mV, mb, 0, ml, ml)
    J_bar = angular.angularcoeffs_general_v(h_bar, q2, mB, mV, mb, 0, ml, ml)
    return function(J, J_bar)

def bvll_dbrdq2(q2, wc_obj, par, B, V, lep):
    tauB = par[('lifetime',B)]
    return tauB * bvll_obs(dGdq2_ave, q2, wc_obj, par, B, V, lep)

def bvll_obs_int(function, q2_min, q2_max, wc_obj, par, B, V, lep):
    def obs(q2):
        return bvll_obs(function, q2, wc_obj, par, B, V, lep)
    return quad(obs, q2_min, q2_max, epsrel=0.01, epsabs=0)[0]
