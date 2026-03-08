import os

import numpy as np
import pytest

from physics_ai.simulation import WaveSimulation
from physics_ai.backend import to_numpy


pytest.importorskip("cupy")
def test_wave_simulation_gpu_parity() -> None:
    os.environ.pop("PHYSICS_AI_CUDA", None)
    sim_cpu = WaveSimulation(size=16, steps=1)
    grid_cpu, vel_cpu = sim_cpu.initialize()
    cpu_grid, cpu_vel = sim_cpu.step(grid_cpu, vel_cpu)

    os.environ["PHYSICS_AI_CUDA"] = "1"
    sim_gpu = WaveSimulation(size=16, steps=1)
    grid_gpu, vel_gpu = sim_gpu.initialize()
    gpu_grid, gpu_vel = sim_gpu.step(grid_gpu, vel_gpu)

    np.testing.assert_allclose(cpu_grid, to_numpy(gpu_grid), atol=1e-5)
    np.testing.assert_allclose(cpu_vel, to_numpy(gpu_vel), atol=1e-5)

    os.environ.pop("PHYSICS_AI_CUDA", None)
