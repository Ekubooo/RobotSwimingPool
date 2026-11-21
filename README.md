# RoboSwimmingPool architecture

This RobotSwimingPool submodule was extracted from integration-repository commit
`b439ffa`. Earlier history remains in that repository. The inherited LICENSE and
third-party asset provenance are retained. Use this checkout inside Robot_Lab;
the host supplies MimicKit, policies, data and the sibling Solver package.

RSP runs existing MimicKit policies in a single Newton fluid/rigid scene. The
package is maintained in this repository and uses the existing pinned WarpSim
environment. Training, multiple simulation worlds and standalone wheel asset
discovery are outside this application's scope.

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

## Running and checking

From the repository root, using the existing WarpSim environment:

```powershell
python -m pip install -e . --no-deps --no-build-isolation
python tools/run_rsp.py
python tools/run_rsp.py --profile humanoid --direct
python tools/run_rsp.py --profile g1 --direct
# Optional: prepare one asset without starting playback.
python tools/prepare_rsp_assets.py --asset props/scene_sphere
```

The integration distribution includes RSP, Solver and PCA code, not MimicKit or asset data. Asset dependency
pins remain in `sim_ready/requirements.txt`. Playback uses the existing MimicKit
environment and Torch dependencies; rendering uses Newton's installed OpenGL
and ImGui dependencies. This refactor does not change any dependency version.

Run only checks relevant to a change. Static checks must scan the current
Robot_Lab packages and reject an empty scan; old checks targeting the former
root-level RSP package must be updated before use. For numerical relocation,
compare the moved functions against the parent repository's baseline sources,
allowing only explicit extraction and import changes. Tests and standalone checking/profiling scripts are local-only and ignored
by Git; a fresh checkout does not include them. Existing local copies may be
restored from a workspace backup, or regenerated for the change under review.
Commands in module guides that reference these scripts require those local copies.

The local contracts cover automatic preparation and replacement, playback cadence/reset, Viewer
ownership, fluid-clock/Graph bookkeeping, and stable state storage. One-off probes,
traces and timing reports belong under ignored `output/`. Shared evaluation
libraries stay versioned: prior scoring lives in `tools/getup/prior_scoring.py`,
while the G1 evaluator also uses its control-probe and joint-diagnostic modules.
Recording interfaces are retained; recording tests and artifacts are excluded.
