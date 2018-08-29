import numpy as np
from pycdft.common.sample import Sample
from pycdft.common.fragment import Fragment
from pycdft.optimizer import Optimizer
from .base import Constraint


class ChargeTransferConstraint(Constraint):
    """ Constraint on electron number difference between a donor and an acceptor fragment

    Extra attributes:
        donor (Fragment): donor fragment.
        acceptor (Fragment): acceptor fragment.
    """

    _eps = 0.0001  # cutoff of Hirshfeld weight when the density approaches zero

    def __init__(self, sample: Sample, donor: Fragment, acceptor: Fragment, N0,
                 optimizer: Optimizer, V_init=0.0, Ntol=None, Vtol=None, dVtol=1.0E-2):
        super(ChargeTransferConstraint, self).__init__(sample, N0, optimizer, V_init=V_init,
                                                       Ntol=Ntol, Vtol=Vtol, dVtol=dVtol)
        self.donor = donor
        self.acceptor = acceptor
        self.update_structure()

    def update_structure(self):
        self.weight = (self.donor.rhopro_r - self.acceptor.rhopro_r) / self.sample.rhopro_tot_r
        self.weight[self.sample.rhopro_tot_r < self._eps] = 0.0
        self.is_converged = False

    def compute_Fc(self):
        omega = self.sample.omega
        n123 = self.sample.n123
        rhor = np.sum(self.sample.rho_r, axis=0)
        Fc = np.zeros([self.sample.natoms, 3])

        for iatom, atom in enumerate(self.sample.atoms):

            w_grad = (self.donor.compute_w_grad(atom, self.weight)
                      - self.acceptor.compute_w_grad(atom, self.weight))
            Fc[iatom] = (omega * n123) * self.V * np.einsum("ijk,aijk->a", rhor, w_grad)

        return Fc
