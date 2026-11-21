"""Assemble Solver boundary instances from prepared RSP artifacts."""

from dataclasses import dataclass
from pathlib import Path

import numpy as np
import warp as wp

from Solver.boundaries.runtime import BoundaryInstance, BoundarySystem

from ..config import check_volume_options
from .load import load_boundary_asset
from .schema import BoundaryArtifact


@dataclass(frozen=True)
class BoundaryLoadOptions:
    support_radius: float
    device: str | wp.Device | None = None
    quadrature_points: int = 16


def load_boundaries(static_asset, dynamic_assets, options: BoundaryLoadOptions) -> BoundarySystem:
    """Load prepared artifacts once, preserving the requested instance order.

    No geometry generation, directory discovery, visual-mesh reads or writes
    occur here. Repeated artifact references share the same GPU volumes.
    """
    if isinstance(dynamic_assets, (str, Path, BoundaryArtifact)):
        raise ValueError("dynamic_assets must be a sequence of boundary artifact references")
    check_volume_options(options.support_radius, options.quadrature_points)
    references = tuple(item if isinstance(item, BoundaryArtifact) else BoundaryArtifact(item)
                       for item in (static_asset, *dynamic_assets))
    if len(references) > np.iinfo(np.int32).max:
        raise ValueError("Boundary instance count exceeds int32 indexing")
    device = wp.get_device(options.device)
    if not device.is_cuda:
        raise ValueError("Boundary Volume loading requires a CUDA device")
    assets, instances, asset_ids = [], [], {}
    for index, reference in enumerate(references):
        if reference not in asset_ids:
            loaded = load_boundary_asset(reference, support_radius=options.support_radius,
                                         quadrature_points=options.quadrature_points, device=device)
            asset_ids[reference] = len(assets)
            assets.append(loaded)
        instances.append(BoundaryInstance(asset_ids[reference], index - 1))
    return BoundarySystem(assets, instances, device)
