# RobotSwimingPool

Run trained [MimicKit](https://github.com/xbpeng/MimicKit) policies in a Newton fluid and rigid-body
scene. Choose a Humanoid or G1 profile, select or assemble a scene, and use the
Newton viewer to pause, step, reset, and switch fluid rendering modes.

<!-- RSP screenshot slot: paste GitHub-hosted runtime image Markdown here. Keep local image files out of Git. -->

## Running and checking

Use this submodule through [RoboLab](https://github.com/Ekubooo/Robot_Lab) at `Robot_Lab/RSP`.
The parent repository supplies MimicKit, policy and motion paths, authored scene
configuration, and the sibling [Solver4Newton](https://github.com/Ekubooo/Solver4Newton)
package. Follow the parent README to install the checkout and obtain the
required data. Run these commands from the parent repository root in WarpSim:

```powershell
python tools/run_rsp.py
python tools/run_rsp.py --profile humanoid --direct
python tools/run_rsp.py --profile g1 --direct
# Optional: prepare a single asset without starting playback.
python tools/prepare_rsp_assets.py --asset props/scene_sphere
```

The first command opens scene selection. Startup prepares missing or outdated
assets for the selected scene. Use the [asset guide](sim_ready/RUNTIME_ASSETS.md)
for source files and generated assets.

The demo profiles require local policy files. The Humanoid profile points to
the agent configuration and checkpoint under
`output/a5000_dodgeball_2048_full_r01/`. The G1 profile points to the environment
and agent configurations and checkpoint under `output/g1_lafan_full_20261107_r01/`.
Supply the expected artifacts or update `args/rsp_pbf_demo_args.txt` or
`args/rsp_pbf_g1_args.txt` in the parent checkout to use compatible local files.
The environment and agent configurations also reference motion data and SMP
prior files. Files under `output/` are outside the published checkout.

For an interactive check, open the scene picker and verify that your profile
is available. Start playback and try pause, single-step, reset, and close.
The optional tests and profiling tools mentioned in the guides require
local copies kept outside the versioned checkout.

## Guides

- [Application and playback](app/README.md)
- [Simulation and policy timing](simulation/README.md)
- [GPU rendering and fluid modes](rendering/README.md)
- [Asset preparation interfaces](sim_ready/README.md)

## Code ownership

| Package | Responsibility |
| --- | --- |
| `app` | Launch, CPU UI commands, playback scheduling and application lifetime |
| `simulation` | Scene description/resolution, Newton model/state and coupled execution |
| `integrations.mimickit` | Environment/agent loading, GSI, policy observations/actions and Engine compatibility |
| `rendering` | CUDA/OpenGL resources, render passes, Newton viewer/GUI adapters and asset previews |
| `sim_ready` | Geometry preparation, asset persistence and read-only loading |

The sibling `Solver` package owns PBF, shared volume-map algorithms, runtime
boundary queries, coupling and fluid scheduling. It does not import RSP.

The application composes these packages. Asset processing uses Solver's shared
boundary algorithms but does not import the application, PBF implementation or
MimicKit. Rendering and simulation do not import MimicKit. RSP loads its own
boundary manifests and passes loaded volumes and bounds to Solver.
Provider-specific representation conversions remain in the integration.
Public imports have one canonical implementation; legacy Engine/environment
entry points only forward to it.

## Configuration and data flow

The application reads the existing playback profiles. Fluid defaults remain in
`simulation.scenes.fluid.DEFAULT_SETTINGS`; the application reads the current value
and passes settings explicitly. It derives the boundary support radius with the
existing PBF configuration code and supplies that value to asset preparation and
scene validation. The asset package never discovers a running solver.

Particle radius and fluid parameters come from the current DEFAULT_SETTINGS;
the scene preset supplies the final Z-up fluid bounds and therefore the particle
count. Each main frame advances both systems by 1/150 s: four rigid
substeps at 1/600 s and two fluid substeps at 1/300 s, with three pressure
iterations per fluid substep. The policy stays at 30 Hz (every five frames).
Volume maps must match the support radius derived from those settings. Before
creating an environment, playback prepares the selected scene's assets using
the same fluid settings as the simulation. Matching inputs, recipes and files
are reused. Missing, damaged or outdated outputs are regenerated; changing the
particle radius automatically updates the volume map. Before scene selection,
startup discovers OBJ props and prepares their validated meshes, collisions and
SDFs. Failures are shown and excluded. Volume maps are completed only after
assembly; previews use prepared OBJ geometry and original humanoid sources.

Volume-map precomputation belongs to the sibling Solver's shared boundaries
module. RSP's preparation pipeline writes SDF plus volume-map NVDB resources,
and its boundary loader validates and reads them. Runtime body transforms,
queries and fluid/rigid forces belong to Solver. Each asset has one current
directory, `data/assets_RSP/runtime/<category>/<name>`, with internal build
metadata and checksums. Prepared OBJ boundaries initially have one SDF grid;
simulation requires the completed SDF and volume map as two grids in one NVDB
file. An adequate existing SDF can be reused when only the volume
map needs updating. No asset version selection or publication step is required.

Original inputs stay outside the generated tree. Runtime directories can be
removed while the application is closed and rebuilt from OBJ files under
`data/assets_RSP/origin/props`, humanoid declarations, referenced originals and
the built-in generation recipes. Preparation
validates a temporary replacement before installing it and holds a directory
lease through environment use. Scene assembly and simulation remain read-only.
Legacy scene references with a version field select the current asset without
rewriting custom scene files.

Automatic placement avoids the internal bunny and uses its existing clearance.
Authored scene validation retains its separate exterior/prop-overlap rules.
These paths share geometry calculations without changing placement policy.
The additional fixed `pbf_stairs` container uses Newton-generated steps and an
optional source OBJ on its platform. Its custom layout preserves the flat spawn
area and raises the initial water block when needed without changing its size.
The saved scene records that placement and its optional `terrain_prop` reference.

`simulation/scenes/assembly.py` owns selection-time layouts; the UI only gathers
choices and displays results. Shared terrain geometry lives in
`sim_ready/container_geometry.py`, while `pipelines/container.py` validates and
persists generated assets. Preview and assembly do not import baking pipelines.
Newton terrain mesh conventions are isolated in `sim_ready/adapters/terrain.py`.
The full-floor stairs, random-grid and gap recipes use the same geometry path.

Asset fingerprints are scoped to the producing recipe and numerical stage.
SDFs, volume maps and convex pieces are independently checked before reuse.
Existing caches without these stage fingerprints are rebuilt on first use;
each asset still has just one current runtime directory.

## Runtime and resource lifetime

The application owns the selection window and lends it to the environment.
Selection finishes its frame and releases preview textures before simulation
construction. The legacy MimicKit launch path still lets the environment own
its viewer. A playback binding only installs/removes application callbacks.

Newton state pairs and contact feedback have a single simulation owner.
MimicKit borrows persistent Torch views and owns its representation conversion
buffers. State storage, CUDA Graph inputs and observation buffers retain their
addresses across steps and resets. UI only changes CPU state; commands are
applied at a complete frame boundary on the playback stream.

The playback loop holds actions between policy decisions. The environment's
existing `step` also renders; the application does not draw a second successful
frame. Paused frames and failed graph updates use the explicit render-only path.
An invalid sampled terrain placement leaves playback paused until a successful
reset; initial placement errors return to scene selection.
Rendering keeps device-side packing and CUDA/OpenGL mapping without CPU particle
readback. CUDA registrations and GL resources are released before their context.

## Source and license

This submodule was extracted from [Robot Lab commit `b439ffa`](https://github.com/Ekubooo/Robot_Lab/tree/b439ffa7d50157476301152bc8e54d815a032f70).
The parent repository preserves the earlier history. The inherited
[Apache License 2.0](LICENSE) and original copyright notice are included.
See [asset provenance](sim_ready/PROVENANCE.md) for asset origins and separate
third-party terms.
