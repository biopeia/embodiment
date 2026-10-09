# Migration record

## Source baseline

- Source repository: local `symbiont-lab` monorepo
- Source SHA: `80d372a186513035f85a769db886e505cabba52d`
- Architecture audit baseline: `cef998a55aae32ed8b2f7373079c11667b01e915`
- Original package root: `symbiont/src/symbiont/core/embodiment/`

## Initial slice dispositions

| Source path | Disposition | Target path | Notes |
| --- | --- | --- | --- |
| `symbiont/src/symbiont/core/embodiment/physiology.py` | SPLIT | `src/embodiment/physiology.py` | Somatic body state candidate; copied unchanged. Last source-path commit at baseline: `538fa01dcaf4d80e63983f948aee4028fc5c2bef`. |
| `symbiont/src/symbiont/core/embodiment/metabolism.py` | SPLIT | `src/embodiment/metabolism.py` | Carries current per-kind accounting coupled to body state; ownership of non-somatic accounting remains subject to boundary review. Last source-path commit at baseline: `13720935595fedabec2c376dc933629b0deae5aa`. |
| `symbiont/src/symbiont/core/embodiment/physiology_config.py` | SPLIT | `src/embodiment/physiology_config.py` | Somatic configuration remains in Embodiment. The unused `prospective_*` deliberation parameters were excluded and deferred to Organism ownership. Last source-path commit at baseline: `ca10871706a02def5afe62d059b04046dee4876c`. |
| source unit tests | REWRITE | `tests/` | Focused contract checks authored for the extracted slice; no source files changed. |

No source history is asserted for this reconstructed multi-file slice. Provenance
is the pinned source SHA and paths above. The source monorepo remains intact.

## Deferred / excluded

| Source area | Disposition | Reason |
| --- | --- | --- |
| `body.py` | DEFER | Mixes somatic truth with receptor transduction, actuator execution and material/world interactions; requires explicit boundary split. |
| `episode.py`, `longitudinal.py`, `memory.py`, `transition.py`, `reembodiment.py` | DEFER | Carry Organism-longitudinal learning, body schema/history, or cross-domain continuity concerns. |
| `session.py`, `contract.py` | DEFER | Mixed transduction/contract capability; candidate for separate Modality/Embodiment contract mapping. |
| `lab/src/lab/physics3d/**` | DEFER | Runtime and physical solver composition belongs to later Physics3D/World extraction analysis. |

## Additional slice: Physics3D mechanical value contracts

| Source path | Disposition | Target path | Provenance / boundary |
| --- | --- | --- | --- |
| `embodiment/src/embodiment/physics3d/mechanics.py` | MOVE (copy-first) | `src/embodiment/physics3d/mechanics.py` | Source repository SHA `80d372a186513035f85a769db886e505cabba52d`; source-path commit `ce5a057295f75bd309af7be3aa60e5d5c49d2b4c`. Exact file content match verified. Self-contained immutable mechanics value types/constants; no solver, World coordination, or Organism interpretation. |
| focused mechanics contract tests | REWRITE | `tests/test_physics3d_mechanics.py` | Target-side checks for immutable mechanics specifications and constants. |

## Additional slice: body/episode checkpoint composition

| Source/target element | Disposition | Target path | Provenance / boundary |
| --- | --- | --- | --- |
| Existing `LivingBodyState` and `MetabolicLedger` checkpoint contracts | REWRITE / COMPOSE | `src/embodiment/checkpoint.py` | Composes the extracted owner checkpoints with explicit body and embodiment-episode IDs. It does not claim Organism identity or World commit authority. |
| Focused serialization and consistency tests | REWRITE | `tests/test_checkpoint.py` | Verifies deterministic encoding, identity retention, malformed schema rejection and body/ledger energy agreement. |

This schema is a migration-stage Embodiment owner checkpoint. It is not a
complete portable Organism continuation or a World causal manifest. It has no
atomic cross-authority publication, crash recovery, storage durability, or
scientific efficacy guarantee. The source monorepo remains unchanged.

## Additional slice: Physics3D coordinate declarations

| Source path | Disposition | Target path | Provenance / boundary |
| --- | --- | --- | --- |
| `embodiment/src/embodiment/physics3d/observation_contract.py` | MOVE (copy-first) | `src/embodiment/physics3d/observation_contract.py` | Source repository SHA `80d372a186513035f85a769db886e505cabba52d`; source-path commit `7100357bf146b906abfe020511258e6eefa1c1db`; source file SHA-256 `df287d3eb8089d1c96597aba00e7d88e1a2ae7df470d475b48b2e1b34a23cf0e`. Stdlib-only coordinate, frame, unit, and revision declarations. |
| `embodiment/tests/test_observation_contract.py` | SPLIT / REWRITE | `tests/test_physics3d_observation_contract.py` | Carries only metadata assertions for the migrated declarations. The source test's `BodyPoseSample`, `JointKinematicState`, and physiology sample checks depend on unmigrated observation models and are deferred. |

This slice defines metadata only. It does not implement a physics solver, prove
that a runtime publishes conforming samples, define actuator mapping, or establish
scientific/physical validity. The engine-specific `physics3d.world` reference
frame label is retained as source contract metadata and is not a World identity.

## Known rewrites

- `physiology_config.py` excludes unused `prospective_*` parameters for Organism deliberation; no other physiology semantics were changed.
- Python distribution/import name is `embodiment`; no `biopeia_*` prefix is used.
- The additional `physics3d.mechanics` module is a physical-apparatus value contract, not a new semantic authority or a claim that Physics3D is owned by Embodiment in full.
- `physics3d.observation_contract` is a coordinate/kinematics declaration only; its metadata tests do not establish runtime conformance.
- This package is an extraction candidate only; no CURRENT/TARGET compliance is implied.
- The copied `LivingBodyState` uses the CURRENT enum label `VitalState.DEAD`; this extraction does not reinterpret it as TARGET `ORGANISM_DEATH`. Applicability is bounded to body-state code and requires later contract mapping.

## Validation

Build/install/test results are recorded in the migration PR/check run. No
scientific assets or historical checkpoints were copied.

## Additional slice: engine-neutral articulated body descriptions

| Source path | Disposition | Target path | Provenance / boundary |
| --- | --- | --- | --- |
| `embodiment/src/embodiment/physics3d/articulated.py` — `FixedLinkTopology`, `ArticulatedBodySpec`, pure URDF formatting helpers, and `build_articulated_urdf` only | SPLIT | `src/embodiment/physics3d/articulated_spec.py` | Source repository SHA `80d372a186513035f85a769db886e505cabba52d`; source-path commit `cea69ac01681811cce0ed23d87c514b9eb048fdb`; source blob SHA-256 `8b47c2caecdf9d31908a008ab4b3af31a2bd8b8272852d8f64fc97bf5d0bfb73`. The target module depends only on the existing mechanics value types and Python standard library. |
| focused body-description checks | REWRITE | `tests/test_articulated_spec.py` | Tests deterministic URDF generation, opaque ordinal channel declarations and invalid topology rejection without loading a solver. |

The solver-bound `ArticulatedPhysics` implementation, MuJoCo scene interactions,
contact resolution, actuation, runtime state, and engine checkpoint handling were
not copied. The generated URDF root label changed from the historical
`symbiont_` prefix to `body_`; link/joint geometry and limits are retained by
the extracted builder. Link emission order is now stable. This is a bounded
description/generation slice, not an executable body, an integration-step
authority, a physics substrate, or evidence of organism motor control.

## Additional slice: body-pose observation value

| Source element | Disposition | Target path | Provenance / boundary |
| --- | --- | --- | --- |
| `embodiment/src/embodiment/observation.py` — `BodyPoseSample` only | SPLIT | `src/embodiment/observation.py` | Source repository SHA `80d372a186513035f85a769db886e505cabba52d`; source file `embodiment/src/embodiment/observation.py`, last commit touching the source path at that baseline `be3236ce13c3aff22353726b5b7aa00ff3e7eac7` (format-only Ruff); last semantic change to `BodyPoseSample` `409e1c2b19972722c09b848c8508a961a18d575d` (unit-quaternion validation); pinned source blob `027f312f9cf07279b4a4421b255448454578ecd2` (SHA-256 `a065368a56274ec2fbac9bacfa6145c43610525716443f504f5b66c4a782def1`). `BodyPoseSample` at source lines 229–281 was split from a mixed observation module and reconstructed with its validation helpers; the whole source module was not copied. Other types in the mixed source module were excluded; this slice does not claim to extract the remainder of that module. |
| Focused BodyPoseSample checks | REWRITE | `tests/test_body_pose_sample.py` | Target-side checks for finite coordinate tuples, unit quaternion, sample time and frame-label preservation. |

The `reference_frame` value `physics3d.world` is retained as a coordinate-frame
label from the pinned contract. It is not a `WorldId`, world authority, or
presence identity; `BodyPoseSample` has no World identity field. This extraction
does not implement passive runtime projection, establish that any Physics3D
runtime emits conforming samples, authorize publication, or validate physical
correctness. `sample_time_s` is only a supplied sample attribute here; this
value type does not make host wall-clock time causal authority. The original
monorepo remains unchanged.

## Additional slice: body-local somatic cycle

| Source element | Disposition | Target path | Provenance / boundary |
| --- | --- | --- | --- |
| `symbiont/src/symbiont/core/embodiment/body.py` — `Body.tick_physics()` behavior only | SPLIT / REWRITE | `src/embodiment/somatic_cycle.py` | Source repository SHA `80d372a186513035f85a769db886e505cabba52d`; source-path commit `13720935595fedabec2c376dc933629b0deae5aa`; pinned source blob `84d57d7a820070699314f3e21d0349da18751398` (SHA-256 `cbbdfd7e1d1e49f61266c0eaa1af05be1b9b00e1fb6971bdf2dc93599f2624ad`). The extracted rule preserves the source order: for a live body, debit basal energy, apply passive wear, then advance body-local age; a dead body is a no-op. Source defaults are retained (`0.005` and `0.0005`). The source caller is `symbiont/src/symbiont/core/orchestration/individual.py:187`, which invokes it from a mixed Organism/Modality/Embodiment step; that caller and its orchestration are not copied. |
| Focused body-cycle checks | REWRITE | `tests/test_somatic_cycle.py` | Target-side tests cover rate validation, live and dead behavior, transition ordering, and bounded state effects. |

This slice does not extract the aggregate `Body`, environmental damage authority,
receptors, effectors, interoception, actuation, material transfer, World tick,
or a solver. It preserves a source-backed body-local operation only; it does not
claim that the source cycle is an empirically calibrated biological law or that
the original mixed runtime satisfies TARGET contracts. `Body.apply_damage()`
was not copied because its current behavior delegates to the already extracted
`LivingBodyState.apply_wear()` path and adds no distinct somatic transition.
The source monorepo remains unchanged.

## Additional slice: body-side material transfer acceptance

| Source element | Disposition | Target path | Provenance / boundary |
| --- | --- | --- | --- |
| `symbiont/src/symbiont/core/embodiment/body.py` — `MaterialTransfer` and `Body.absorb_material()` only | SPLIT / REWRITE | `src/embodiment/intake.py` | Source repository SHA `80d372a186513035f85a769db886e505cabba52d`; source-path commit `13720935595fedabec2c376dc933629b0deae5aa`; pinned source blob `84d57d7a820070699314f3e21d0349da18751398` (SHA-256 `cbbdfd7e1d1e49f61266c0eaa1af05be1b9b00e1fb6971bdf2dc93599f2624ad`). The standalone target operation preserves the source rule: mismatched target body ID accepts `0`; a match delegates the scalar amount to `LivingBodyState.add_energy()`, which rejects dead-body intake and caps acceptance at available capacity. |
| Focused transfer acceptance checks | REWRITE | `tests/test_intake.py` | Directly checks target identity, capacity-limited acceptance, dead-body rejection, zero amount, and transfer validation. The source integration oracle is `lab/tests/unit/lab/world/test_adapter.py::test_clean_material_exchange_conserves_mass_with_scarce_resources` at source lines 362–443; its path last changed at the pinned source SHA in `06f33acca0b01fc772fbcf7b8f1cede295609630`. The tracked caller is `lab/src/lab/world/population.py:739–769`, whose path last changed at that SHA in `0550aede453d213674bfeb916cd6e3975f26aa91`. |

The operation consumes only the existing Embodiment body-state API and imports
no World, Environment, Lab, or Organism code. `source_id` and `composition`
remain uninterpreted, as in CURRENT. The scalar amount is passed unchanged to
`add_energy()`; no material-to-energy conversion or scientific equivalence is
asserted. Resource withdrawal, transfer authorization, event publication,
refunds, and transaction ordering remain World/Environment responsibilities and
were not extracted. The source monorepo remains unchanged.

## Additional slice: engine-neutral physical input projection

| Source elements | Disposition | Target path | Provenance / boundary |
| --- | --- | --- | --- |
| `embodiment/src/embodiment/physics3d/articulated.py` — `ArticulatedBodySpec` and `build_articulated_urdf`; `embodiment/src/embodiment/observation.py` — `BodyPoseSample` | SPLIT / REWRITE composition | `src/embodiment/physics3d/physical_projection.py` | Source repository SHA `80d372a186513035f85a769db886e505cabba52d`; articulated-description source path commit `cea69ac01681811cce0ed23d87c514b9eb048fdb`; pose source path commit `be3236ce13c3aff22353726b5b7aa00ff3e7eac7`. The target combines the already extracted owner-side morphology description (segment mass/box geometry, joints and declared contact-link names) with the already extracted validated root pose into an immutable solver input snapshot. |
| Focused projection checks | REWRITE | `tests/test_physical_projection.py` | Tests pose/frame and geometry/mass preservation, immutability, no mutation of source owner values, and snapshot behavior if the input spec's mapping is later mutated. |

This is the bounded projection contract from the available concrete fields; it
does **not** project `LivingBodyState` energy, integrity, temperature, fatigue,
damage, viability or age into solver parameters. CURRENT defines no grounded
mapping from those physiological scalars to mass, contact geometry, force or
constraints, and inventing one would violate owner semantics. The pose is an
explicit `BodyPoseSample`, not a pose inferred from physiology. URDF here is a
solver-consumable morphology description, not solver ownership or execution.
The solver must return results separately; this projection performs no
Embodiment state transition, World coordination, causal commit, or acceptance
of solver output. No solver-runtime wiring or physical validity claim is made.
The historical monorepo remains unchanged.

## Additional slice: physical duration value

| Source element | Disposition | Target path | Provenance / boundary |
| --- | --- | --- | --- |
| `symbiont/src/symbiont/core/embodiment/duration.py` — `PhysicalDuration` only | MOVE (copy-first) | `src/embodiment/duration.py` | Source repository SHA `80d372a186513035f85a769db886e505cabba52d`; source-path commit `74bd7a0099341410465fe9e540f93e6ef7266bc2`; pinned source blob `965fd3bb62f08c2c582e5b785233955d796297ee` (SHA-256 `cd4e7ed5fad889a2d20615563bdba2e0d0644295f7e937129b31a2d106676819`). The copied implementation retains the exact constructor and representation behavior. |
| Focused `PhysicalDuration` checks | REWRITE | `tests/test_duration.py` | Tests cover plain integer/float and same-type inputs, nonnegative finite values, rejection of booleans/other numeric subclasses/non-numeric values, and representation. |

The type represents a supplied physical elapsed duration in seconds (`T_p`);
it does not measure or source time. No clock, scheduler, timestep policy,
solver integration, consumer, or causal authority was copied or added. Host
wall-clock time and cognition/cycle scales remain outside this type. The
canonical temporal-scale design at the pinned source SHA keeps `T_p` owned by
Embodiment and prohibits Cognition and Foundation from importing or consuming
it (`docs/design/core/temporal-scales-and-clock-separation-v1.md`, lines
90–94 and 194–197). This candidate does not establish target-wide compliance
or runtime conformance. The source monorepo remains unchanged.
## Additional slice: owner command to physical-effector candidate (candidate)

| Source element | Disposition | Target path | Provenance / boundary |
| --- | --- | --- | --- |
| Opaque `MotorCommand` / `ActuatorSurface` and current ordinal adapter behavior | REWRITE / COMPOSE | `src/embodiment/physics3d/actuation_projection.py` | Source provenance at pinned SHA `80d372a186513035f85a769db886e505cabba52d`: `symbiont/src/symbiont/actuation/action.py` and `surface.py` (path commit `13720935595fedabec2c376dc933629b0deae5aa`); `lab/src/lab/integration/physics3d/apparatus.py` (commit `792d2dbd3e507d1d41300456cf826d8efe19fddb`); `lab/src/lab/physics3d/runtime.py` (commit `5e9a250f103373ed1333c05f96bc2554abdf5020`); `embodiment/src/embodiment/physics3d/articulated.py` (commit `cea69ac01681811cce0ed23d87c514b9eb048fdb`). Current ordinal mapping and zero-default are source behavior only, not target authority. |
| Owner-selected morphology and per-effector quantity contracts | NEW STRUCTURAL CONTRACT | `MorphologyLike`, `EffectorContractLike`, `ActuatorChannelLike` in `src/embodiment/physics3d/actuation_projection.py` | Require stable effector IDs, body ID, embodiment episode ID, morphology revision, command kind, quantity, unit, minimum, neutral, maximum, and explicit saturation policy. Only `reject` is implemented; no clipping or physical unit is invented. |
| Focused projection tests | REWRITE | `tests/test_actuation_projection.py` | Checks stable-ID matching under permuted surface order, sparse omission, identity/revision binding, declared quantity/range/neutral/unit/saturation contracts, rejection, and malformed/duplicate mappings. |

The target association is explicit: each command actuator ID resolves through
the supplied active revision's surface to a stable effector ID; surface order
has no mapping authority. The surface's schema is validated against the active
morphology revision. Every emitted channel explicitly repeats `body_id`,
`embodiment_episode_id`, `morphology_revision`, `effector_id`, and
`command_kind`, as well as the value and its quantity/unit/range/neutral/
saturation contract. Command, surface, active morphology, pose, and Embodiment
checkpoint must agree on body, embodiment episode, and morphology revision.
Out-of-range values are rejected; no clipping or saturation is inferred. A
missing command channel remains absent and means no command; it is not
converted to zero, neutral, hold, or another inferred action. Neutrality is
available only as the effector descriptor's explicit `neutral` value and is
not used as an omission default. The returned `PhysicalActuationCandidate` is
sparse and immutable; it is not a solver result or somatic state transition.

Remaining work is explicit: command producers and active-morphology/surface
owners must supply these fields; this repository does not define which
physical quantities/units a concrete simulator adapter uses. This slice
neither runs a solver nor claims physical efficacy. It imports no Organism
implementation at runtime; the source monorepo remains unchanged.

## Additional slice: owner-side physical result adoption and checkpoint value (candidate)

| Source element | Disposition | Target path | Provenance / boundary |
| --- | --- | --- | --- |
| Correlated solver body candidate and Embodiment adoption boundary | NEW STRUCTURAL CONTRACT | `src/embodiment/physics3d/physical_transition.py` | Candidate correlation includes World, causal tick, physical-step ID, body, embodiment episode, morphology revision, environment revision, and solver configuration revision. The solver remains a numerical executor; this module validates and adopts through an immutable owner-state transition. |
| Embodiment physical-state checkpoint representation | NEW STRUCTURAL CONTRACT | `EmbodimentPhysicalState.checkpoint_bytes()` / `restore_checkpoint()` | Deterministic JSON bytes encode owner identity, episode, morphology revision, world tick, pose, frames, metres, xyzw ordering, contract revision, and last accepted step correlation. SHA-256 is a stable content identifier only. |
| Focused acceptance and checkpoint tests | NEW TESTS | `tests/test_physical_transition.py` | Exercises valid adoption, stale/wrong correlation rejection without mutation, deterministic bytes, exact restore, explicit units/frames, and malformed/unsupported checkpoint rejection. |

The checkpoint bytes represent a recoverable owner value, but Embodiment does
not persist them or claim filesystem durability. `durably_referenceable` stays
false for the in-memory state; a digest becomes a usable World checkpoint
reference only after an external checkpoint store durably stores and verifies
the bytes. World must still coordinate all required owner references before
committing its causal cut. This bounded slice does not select/invoke a solver,
integrate Environment, persist checkpoints, coordinate World, or complete the
FIRST BIOPEIA END-TO-END PHYSICAL CAUSAL STEP milestone.
