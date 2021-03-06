import numpy as np
from pycdft.common.sample import Sample
from pycdft.common.fragment import Fragment
from pycdft.constraint.base import Constraint


class ChargeTransferConstraint(Constraint):
    r""" Constraint on electron number difference between a donor and an acceptor fragment

    For donor region D and acceptor region A, Hirshfeld weight is defined as
    :math:`w({\bf r})= \frac{\sum_{I \in D} \rho_I-\sum_{I \in A} \rho_I}{\sum_I \rho_I}`

    Extra attributes:
         donor (Fragment): donor fragment.
         acceptor (Fragment): acceptor fragment.
    """

    type = "charge transfer"

    def __init__(self, sample: Sample, donor: Fragment, acceptor: Fragment, N0: float,
                 V_init=0, V_brak=(-1, 1), N_tol=1.0E-3, eps=1e-6):
        super(ChargeTransferConstraint, self).__init__(
            sample, N0, V_init=V_init, V_brak=V_brak, N_tol=N_tol
        )
        self.eps = eps
        self.donor = donor
        self.acceptor = acceptor
        print(f"Constraint: type = {self.type}, N_tol = {self.N_tol:.5f}, eps = {self.eps:.2E}")

    def update_w(self):
        #w = (self.acceptor.rhopro_r - self.donor.rhopro_r) / self.sample.rhopro_tot_r
        w = (self.donor.rhopro_r - self.acceptor.rhopro_r) / self.sample.rhopro_tot_r
        w[self.sample.rhopro_tot_r < self.eps] = 0.0
        if self.sample.vspin == 1:
            self.w = w[None, ...]
        else:
            self.w = np.append(w, w, axis=0).reshape(2, *w.shape)

    def compute_w_grad_r(self, atom):
        if atom in self.donor.atoms:
            delta = 1
        elif atom in self.acceptor.atoms:
            delta = -1
        else:
            delta = 0

        rho_grad_r = self.sample.compute_rhoatom_grad_r(atom)
        w_grad = np.einsum(
            "sijk,aijk,ijk->asijk", delta - self.w, rho_grad_r, 1 / self.sample.rhopro_tot_r
        )
        for icart, ispin in np.ndindex(3, self.sample.vspin):
            w_grad[icart, ispin][self.sample.rhopro_tot_r < self.eps] = 0.0
        return w_grad

    # added for debuggin forces
    def debug_w_grad_r(self, atom):
        if atom in self.donor.atoms:
            delta = 1
        elif atom in self.acceptor.atoms:
            delta = -1
            #delta = 0 # should reproduce charge constains in He_2^+
                       # but instead half reproduces a-d and w_grad is no longer symmetric
        else:
            delta = 0

        rho_grad_r = self.sample.compute_rhoatom_grad_r(atom)
        w_grad = np.einsum(
            "sijk,aijk,ijk->asijk", delta - self.w, rho_grad_r, 1 / self.sample.rhopro_tot_r
        )
#        w_grad_part = np.einsum(
#            "sijk,ijk-> sijk", delta - self.w, 1 / self.sample.rhopro_tot_r
#        )

        for icart, ispin in np.ndindex(3, self.sample.vspin):
            w_grad[icart, ispin][self.sample.rhopro_tot_r < self.eps] = 0.0
        return w_grad, rho_grad_r
