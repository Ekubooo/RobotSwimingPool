"""Settings shared by asset preparation and the playback entry point."""
POLICY_HZ = 30


def get_fluid_settings():
    from RSP.simulation.scenes.fluid import DEFAULT_SETTINGS

    return DEFAULT_SETTINGS


def boundary_support_radius(settings=None):
    from RSP.simulation.scenes.fluid import boundary_support_radius as derive_support_radius

    return derive_support_radius(get_fluid_settings() if settings is None else settings)
