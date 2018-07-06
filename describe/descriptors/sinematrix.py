from __future__ import absolute_import, division, print_function
from builtins import super
import numpy as np
from describe.descriptors.matrixdescriptor import MatrixDescriptor


class SineMatrix(MatrixDescriptor):
    """Calculates the zero padded Sine matrix for different systems.

    The Sine matrix is defined as:

        Cij = 0.5 Zi**exponent      | i = j
            = (Zi*Zj)/phi(Ri, Rj)   | i != j

        where phi(r1, r2) = | B * sum(k = x,y,z)[ek * sin^2(pi * ek * B^-1
        (r2-r1))] | (B is the matrix of basis cell vectors, ek are the unit
        vectors)

    The matrix is padded with invisible atoms, which means that the matrix is
    padded with zeros until the maximum allowed size defined by n_max_atoms is
    reached.

    For reference, see:
        "Crystal Structure Representations for Machine Learning Models of
        Formation Energies", Felix Faber, Alexander Lindmaa, Anatole von
        Lilienfeld, and Rickard Armiento, International Journal of Quantum
        Chemistry, (2015),
        https://doi.org/10.1002/qua.24917
    """
    def __init__(self, n_atoms_max, permutation="sorted_l2", flatten=True):
        """
        Args:
            n_atoms_max (int): The maximum nuber of atoms that any of the
                samples can have. This controls how much zeros need to be
                padded to the final result.
            permutation (string): Defines the method for handling permutational
                invariance. Can be one of the following:
                    - none: The matrix is returned in the order defined by the Atoms.
                    - sorted_l2: The rows and columns are sorted by the L2 norm.
                    - eigenspectrum: Only the eigenvalues are returned sorted
                      by their absolute value in descending order.
                    - random: ?
            flatten (bool): Whether the output of create() should be flattened
                to a 1D array.
        """
        super().__init__(n_atoms_max, permutation, flatten)

    def get_matrix(self, system):
        """Creates the Sine matrix for the given system.
        """
        # Cell and inverse cell
        B = system.get_cell()
        B_inv = system.get_cell_inverse()

        # Difference vectors in tensor 3D-tensor-form
        diff_tensor = system.get_displacement_tensor()

        # Calculate phi
        arg_to_sin = np.pi * np.dot(diff_tensor, B_inv)
        phi = np.linalg.norm(np.dot(np.sin(arg_to_sin)**2, B), axis=2)

        with np.errstate(divide='ignore'):
            phi = np.reciprocal(phi)

        # Calculate Z_i*Z_j
        q = system.get_initial_charges()
        qiqj = q[None, :]*q[:, None]
        np.fill_diagonal(phi, 0)

        # Multiply by charges
        smat = qiqj*phi

        # Set diagonal
        np.fill_diagonal(smat, 0.5 * q ** 2.4)

        return smat
