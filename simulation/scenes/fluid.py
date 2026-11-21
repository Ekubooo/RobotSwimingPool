"""RSP fluid settings shared by scene assembly and asset preparation."""

from types import SimpleNamespace

from Solver.fluid_clock import FluidSettings
from Solver.pbf.pbf_helper import PBFConfig, init_scene_parameters


# PBFConfig exposes every fluid parameter, including radius, density, viscosity,
# vorticity, pressure regularization, initial velocity and block bounds. Supply
# overrides here, e.g. pbf=PBFConfig(substeps=2, viscosity=0.25).
DEFAULT_SETTINGS = FluidSettings(
    pbf=PBFConfig(particle_radius=0.0115, substeps=2, pressure_iterations=3, gravity=(0., -10., 0.),
                  # Z-up runtime lattice: 60 * 73 * 80 = 350,400 particles.
                  # Centered across 85% of the pool's 2 m horizontal width.
                  # The regular lattice deliberately includes the static bunny.
                  block_start=(1.56, .50, .15), block_end=(2.96, 2.363, 1.85)),
    time_scale=1.0,
    max_dt=1.0 / 300.0,
)


def boundary_support_radius(settings):
    particles = SimpleNamespace(config=settings.pbf)
    init_scene_parameters(particles)
    return particles.smoothing_length
