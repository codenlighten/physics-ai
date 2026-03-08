import numpy as np

from physics_ai.visualization import (
    plot_dispersion,
    plot_field,
    plot_particles,
    plot_spectrum,
    plot_temporal_signal,
    plot_trajectory,
    render_summary,
)


def test_basic_plots_smoke(tmp_path) -> None:
    field = np.random.default_rng(1).random((16, 16))
    dispersion = {"k_values": [1.0, 2.0], "omega": 3.0, "coefficients": [0.0, 1.0, 0.0], "law_type": "wave"}
    particles = {"tracks": [{"positions": [(1, 2), (2, 3), (3, 4)]}]}
    trajectory = np.array([[1.0, 1.0], [2.0, 2.0], [3.0, 2.0]])

    fig1 = plot_field(field)
    fig2 = plot_spectrum(field)
    fig3 = plot_temporal_signal([0.1, 0.2, 0.15])
    fig4 = plot_dispersion(dispersion)
    fig5 = plot_particles(particles)
    fig6 = plot_trajectory(trajectory)

    for fig in (fig1, fig2, fig3, fig4, fig5, fig6):
        assert fig is not None
        fig.savefig(tmp_path / f"fig_{id(fig)}.png")


def test_render_summary_saves_files(tmp_path) -> None:
    results = {
        "dataset": [
            {
                "observation": {
                    "field": np.random.default_rng(2).random((12, 12)),
                    "temporal_signal": [0.2, 0.1, 0.3],
                    "particles": {"tracks": [{"positions": [(1, 1), (2, 2)]}]},
                    "trajectory": np.array([[0.0, 0.0], [1.0, 2.0]]),
                }
            }
        ],
        "dispersion": {"k_values": [1.0], "omega": 1.0, "coefficients": [0.0, 1.0, 0.0], "law_type": "wave"},
    }
    saved = render_summary(results, output_dir=tmp_path, show=False)
    assert saved
