import numpy as np

from physics_ai.operator_library import build_coupled_operator_matrices, build_operator_matrix


def test_operator_library_includes_spatial_terms() -> None:
    signal = [0.0, 1.0, 0.5, -0.5]
    field = np.array([[1.0, 2.0], [3.0, 4.0]])

    matrix, target, names = build_operator_matrix(signal, field=field)

    assert matrix.shape == (len(signal), 6)
    assert target.shape == (len(signal),)
    assert names[-3:] == ["laplacian", "biharmonic", "abs(psi)^2 psi"]

    lap = (
        -4 * field
        + np.roll(field, 1, axis=0)
        + np.roll(field, -1, axis=0)
        + np.roll(field, 1, axis=1)
        + np.roll(field, -1, axis=1)
    )
    bih = (
        -4 * lap
        + np.roll(lap, 1, axis=0)
        + np.roll(lap, -1, axis=0)
        + np.roll(lap, 1, axis=1)
        + np.roll(lap, -1, axis=1)
    )
    lap_mean = float(np.mean(lap))
    bih_mean = float(np.mean(bih))
    nonlinear_mean = float(np.mean(np.abs(field) ** 2 * field))

    np.testing.assert_allclose(matrix[:, 3], lap_mean)
    np.testing.assert_allclose(matrix[:, 4], bih_mean)
    np.testing.assert_allclose(matrix[:, 5], nonlinear_mean)


def test_build_coupled_operator_matrices_shapes() -> None:
    psi_signal = [0.0, 1.0, 0.5, -0.5]
    phi_signal = [0.5, -0.5, 0.25, -0.25]
    psi_field = np.array([[1.0, 2.0], [3.0, 4.0]])
    phi_field = np.array([[0.5, 0.2], [0.1, -0.3]])

    matrix_psi, target_psi, names_psi, matrix_phi, target_phi, names_phi = (
        build_coupled_operator_matrices(
            psi_signal,
            phi_signal,
            psi_field=psi_field,
            phi_field=phi_field,
        )
    )

    assert matrix_psi.shape[0] == len(psi_signal)
    assert matrix_phi.shape[0] == len(phi_signal)
    assert target_psi.shape[0] == len(psi_signal)
    assert target_phi.shape[0] == len(phi_signal)
    assert names_psi == names_phi
