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

## Pinned source inventory: `symbiont/core/embodiment`

This inventory classifies every tracked file directly under
`symbiont/src/symbiont/core/embodiment/` at source commit
`80d372a186513035f85a769db886e505cabba52d`. In the source/blob column,
`path@commit/blob` records the last source-path commit at that pinned revision
and the Git blob object ID at the pinned revision. Target paths are relative to
the indicated Biopeia repository. This supplements, and does not replace, the
concrete slice records above. The inventory is evidence-based disposition, not
permission to copy deferred implementation or an assertion that CURRENT source
behavior is a TARGET contract.

| Source file and material symbols | Disposition | Target repository/path | Source path commit / pinned blob | Reason, evidence/tests, caveats, and revisit trigger |
| --- | --- | --- | --- | --- |
| `__init__.py`: package exports for adaptation, contracts, duration, dynamics, episodes, history, memory, reachability, re-embodiment and sessions | SPLIT | `embodiment/src/embodiment/__init__.py` (selective exports already exist) | `60843cba5e66e782054da96e187ca572f0254098` / `ea0df2cffb5b594b8df40b4b905589cac40b51f4` | The source facade re-exports mixed capabilities; target exports only migrated somatic APIs. Evidence: target package tests/imports. Preserve source API compatibility only where a separately classified slice justifies it. Revisit each export when its underlying symbols receive a disposition; do not bulk-copy the facade. |
| `adaptation.py`: `AdaptationSnapshot`, `EmbodimentAdaptation` | DEFER | `embodiment`; target module TBD | `13720935595fedabec2c376dc933629b0deae5aa` / `85edb6a3713777d32b6a7cbe4f26757042504d22` | Prediction-residual adaptation is coupled to `dynamics.py` and unclear learning/Organism authority. No target tests. Revisit when owner and update/learning contract are explicit; then split somatic adaptation from Organism learning if evidence supports both. |
| `agency.py`: `ChannelStat`, `PerceptualStructure`, `SensorimotorModel`, `ChannelInterventionRecord`, `AgencyModel`, inferred body-region/schema/self-model types | DEFER | Primarily `organism`; exact split/paths TBD | `13720935595fedabec2c376dc933629b0deae5aa` / `8e452d866061d7bef83e1bfe6631be25f489d15b` | Self-model and agency inference are Organism concerns, while channel evidence may reference Embodiment/Modality. Source tests: `symbiont/tests/unit/core/test_embodiment_agency.py`, `test_embodiment_v2.py`. Revisit with typed owner/provenance contracts and split any physical description from cognitive interpretation. |
| `assimilation.py`: `AssimilationAction`, `AssimilationDecision`, `InformationAssimilator` | DEFER | `organism`; target path TBD | `13720935595fedabec2c376dc933629b0deae5aa` / `28c9824474f2ad50b347c928772b361cefbbb9e5` | Information assimilation is cognitive/Organism behavior, not somatic state. No target test or code. Revisit when Organism's learning/assimilation contract is in scope; do not move as Embodiment merely because it is in this source package. |
| `body.py`: `Body` and `create_standard_body` remainder; `ReceptorPort`, `PhysicalEffect`, `EffectorPort`, `ActivationConsequence`; excluding separately recorded `tick_physics`, `MaterialTransfer`, `absorb_material` | SPLIT / DEFER | `embodiment/src/embodiment/body.py` or composed modules; exact paths TBD | `13720935595fedabec2c376dc933629b0deae5aa` / `84d57d7a820070699314f3e21d0349da18751398` | `tick_physics()` and material-acceptance rules are separately extracted above. The aggregate still mixes owner state, sensory transduction, actuation, environmental interaction and construction. Source tests include `symbiont/tests/unit/core/test_clean_embodiment_episode.py`; target tests `test_somatic_cycle.py`, `test_intake.py` cover only their bounded slices. Revisit by method/contract when owner-specific command and observation integration is ready; do not migrate the aggregate wholesale. |
| `body_schema.py`: `DependencyKind`, `BodySchemaEngine` and internal evidence/classification helpers | DEFER | `organism`; target path TBD | `c077496ba8bb73cbd3940dda6516672bcd1f7376` / `909c67c8988e95186aab3053210a847c1761a7ba` | Imports Organism limits, epistemic conventions and cognitive channel limits; derives self-model/body-schema evidence rather than physical morphology. Source tests: `symbiont/tests/unit/core/test_body_schema.py`, `test_body_schema_agentic.py`, `test_body_schema_runtime.py`, `test_cognitive_body_schema.py`, `test_cognitive_body_schema_longitudinal.py`. Revisit under Organism semantic/provenance contracts; any physical morphology schema must be a separately identified owner contract, not this cognitive schema by name. |
| `contract.py`: `PerceptualChannel`, `PerceptualSurface`, `TimingContract`, `EmbodimentContract` | DEFER | Split between `modality` (transduction/surface contract) and `embodiment` (physical owner constraints); target paths TBD | `13720935595fedabec2c376dc933629b0deae5aa` / `85076bceaff300ff4a593f4bdc81ae78de1751b4` | Depends on source `ActuatorSurface` and combines perception, timing and Embodiment capability. It cannot be adopted as a single physical contract without resolving modality and explicit command semantics. Revisit with stable identities, units, omission behavior and frame/revision requirements; target `actuation_projection.py` already supplies a narrower explicit effector contract. |
| `degradation.py`: `RetentionState`, `RetainedItem`, `DegradationQueue` | DEFER | `organism` or scientific/evidence store; exact owner/path TBD | `c077496ba8bb73cbd3940dda6516672bcd1f7376` / `cfc40aebf5afa228108ca00f29b439fe83ff0c06` | Retention queue depends on `OrganismLimits` and physiology defaults but its retained-item meaning/authority is not clear from package placement. No target tests. Revisit when retained state, lifecycle and evidence-retention ownership are specified; do not infer Embodiment ownership from the import. |
| `development.py`: `DevelopmentalPhase`, `DevelopmentalSnapshot`, `DevelopmentalTracker` | DEFER | `organism`; target path TBD | `1a7b70730c2730932086c4dff7fd922fb5c8e293` / `a727788628fbf86b311c66c4403387ac6e56ab00` | Developmental phase tracking is not separated into organism development versus physical maturation in this file. No target tests. Revisit with Organism development authority and an explicit split for any body-owned structural changes. |
| `duration.py`: `PhysicalDuration` | MOVE (copy-first) | `embodiment/src/embodiment/duration.py` | `74bd7a0099341410465fe9e540f93e6ef7266bc2` / `965fd3bb62f08c2c582e5b785233955d796297ee` | Already extracted and byte-identical at the pinned source (SHA-256 and tests are recorded above). `tests/test_duration.py` checks finite nonnegative physical seconds. It is a supplied duration value, not a clock or causal scheduler. |
| `dynamics.py`: `EvidenceProvenance`, `PredictionResidual`, `SensorimotorDynamicsModel` | DEFER | Split candidate: `embodiment` for physical dynamics evidence; `organism` for predictive/learned model; paths TBD | `13720935595fedabec2c376dc933629b0deae5aa` / `579620bc4167bbcdc9e442dfc42149373c94ed91` | Prediction residuals and model updates may consume owner observations and learning state; one file cannot establish which authority owns either. No target tests. Revisit after Observation family/provenance and Organism learning contracts are available; keep derived claims distinct from authoritative physical state. |
| `episode.py`: `EmbodimentState`, `EmbodimentEndReason`, `ContractTransition`, `EmbodimentEpisode` | DEFER | `embodiment`; target module TBD | `6ff37a6d9fa6cc455c3db2b5238bba60a25ead3d` / `e085f4edc4603200cd0a9ad3591a596e3d75b54f` | Episode identity is a relevant Embodiment concept, but implementation couples body schema, adaptation, actuation evidence/bindings, memory and reachability. No target episode/runtime tests. Revisit after episode identity/lifecycle contracts and owner checkpoint integration are defined; do not treat source tick or checkpoint behavior as World durability. |
| `history.py`: `EmbodimentEpisodeSummary` | DEFER | `embodiment` candidate; target path TBD | `13720935595fedabec2c376dc933629b0deae5aa` / `a5d20ad2fcf1cd5156ebaa6ba690d78eddc891d7` | Summary is episode-history data, but fields and serialized mapping must be classified against the episode contract and scientific evidence boundary. No target tests. Revisit with episode migration; retain exact source field lineage and do not conflate summary with Observation replay. |
| `homeostasis.py`: `HomeostaticAction`, `HomeostaticSnapshot`, `HomeostaticController` | DEFER | `embodiment` candidate; target path TBD | `a1c613cb89b117359018cc8bdfa15384d3af7e06` / `4dd604719b1d568490bc0fff29bbcd8b4a1c0e7c` | Couples physical duration, metabolic ledger and physiology; thresholds/actions encode unvalidated controller semantics. No target tests. Revisit only with explicit quantity units, thresholds, authority and failure behavior; code/CI alone cannot validate physiological efficacy. |
| `lifecycle.py`: `LifeState`, `ViabilityController` | SPLIT / DEFER | `embodiment` for somatic viability; `organism` for organism lifecycle; paths TBD | `13720935595fedabec2c376dc933629b0deae5aa` / `1dd3367acaf457be5b6f4837b2440c5a750221d2` | Uses metabolic pressure but names organism-like lifecycle. Source tests: `symbiont/tests/unit/core/test_metabolism.py`; target `tests/test_somatic_state.py` covers bounded body-state behavior, not this controller. Revisit with explicit distinction between body viability and Organism death/lifecycle; never map `VitalState.DEAD` to organism death implicitly. |
| `longitudinal.py`: contract fingerprinting, historical motor candidates, memory injection, epoch summary and end-reason helpers | DEFER | `organism`; target path TBD | `42ff87fe2102d1a26eb218a5c071ddfb90f42e34` / `f4c7529be153f54199e1480a6216bdead1c4ea57` | Reads action-domain, competence and actuator evidence and writes longitudinal cognition/history; this is cross-domain Organism continuity, not owner somatic state. Source tests: `symbiont/tests/unit/core/test_cognitive_body_schema_longitudinal.py`, `test_embodiment_v2.py`. Revisit with Organism continuity and provenance contracts; partition any body-specific archive references. |
| `memory.py`: `BodySpecificMemory`, `EmbodimentPrior`, `EmbodimentArchive`, `archive_episode_checkpoint` | DEFER | Split candidate between `embodiment` (body-specific archive reference) and `organism` (learned prior/memory); paths TBD | `f004081a9c70c10109eaeb95d9fb4067488451fa` / `9fe68589710a3f5f6a7514123b73ccaba602c3b7` | Combines body identity with learned prior and episode checkpoint archiving; ownership/custody and cross-episode semantics are not established by current target checkpoint bytes. No target tests. Revisit with explicit archive authority, stable identity, retention and evidence lineage; checkpoint serialization is not durability. |
| `metabolism.py`: `ResourcePressure`, `MetabolicSnapshot`, `MetabolicLedger` | SPLIT | `embodiment/src/embodiment/metabolism.py` | `13720935595fedabec2c376dc933629b0deae5aa` / `4ba6b77486d32fac7a2a98d4f32ce3707f59f1bb` | Already copied unchanged as described above; owner candidate tests are `tests/test_somatic_state.py` and `tests/test_checkpoint.py`. Current per-kind accounting and non-somatic resource semantics remain boundary debt. Revisit those fields individually when Environment/World material ownership is explicit; do not treat scalar intake as physical equivalence. |
| `ontogeny.py`: `PhysicalLifeStage`, `OntogenySnapshot`, `OntogenyController` | DEFER | Split candidate: `organism` development and `embodiment` body maturation; paths TBD | `13720935595fedabec2c376dc933629b0deae5aa` / `3f7ec7453c277d7fb905fd152628243194c73a12` | Couples metabolic ledger, body state and physiology configuration to life-stage transitions. No target tests. Revisit when development owner and somatic maturation effects are specified separately; preserve source thresholds only as CURRENT evidence, not calibrated laws. |
| `physiology.py`: `VitalState`, checkpoint helpers, `BodyStructureState`, `LivingBodyState`, `PhysiologySnapshot`, `PhysiologyController` | MOVE (copy-first) | `embodiment/src/embodiment/physiology.py` | `538fa01dcaf4d80e63983f948aee4028fc5c2bef` / `be27d6590f28436c3ed02683aa0dd9173b14b355` | Entire file is already extracted byte-identically at the pinned source SHA-256; target `tests/test_somatic_state.py` and `tests/test_checkpoint.py` verify bounded state/checkpoint behavior. `VitalState.DEAD` remains a CURRENT body-state label, not TARGET `ORGANISM_DEATH`; physical effectiveness and durable storage are not established. |
| `physiology_config.py`: `PhysiologyConfig` (excluding unused `prospective_*` deliberation parameters) | SPLIT | `embodiment/src/embodiment/physiology_config.py` | `ca10871706a02def5afe62d059b04046dee4876c` / `7f3c23364f4093d62ff25ac2af2373183c5cb1f7` | Somatic parameters are extracted; the named prospective deliberation parameters were excluded for Organism disposition as recorded above. `tests/test_somatic_state.py` exercises target behavior. Revisit excluded parameters only under Organism-owned prospective reasoning; do not import them back as physiology defaults without evidence. |
| `reachability.py`: `ReachabilityRelation`, `ReachabilityModel` | DEFER | `organism` candidate; target path TBD | `13720935595fedabec2c376dc933629b0deae5aa` / `aa20bf98182c518a8df3fdf5a3bab166122af027` | Reachability is an inferred capability/model over body affordances, with uncertain split between Embodiment constraints and Organism inference. No target tests. Revisit with typed physical-affordance inputs and explicit inferred epistemic status; must not become an authoritative body-state claim. |
| `reembodiment.py`: `select_prior`, `begin_reembodiment`, `replace_body` | DEFER | Split candidate between `organism` continuity and `embodiment` episode/lifecycle; paths TBD | `13720935595fedabec2c376dc933629b0deae5aa` / `e5ede03a28c335c062f222b1d11346d1741025f9` | Coordinates archive/prior selection, contract and episode transitions. No target tests. Revisit after both owner contracts exist; require stable Organism, body and episode identities and explicit continuity/provenance, not a hidden 1:1 identity assumption. |
| `session.py`: `PortBinding`, `EmbodimentSession`, `implant`, `implant_body` | DEFER | Split between `modality` (port/transduction) and `embodiment` (episode/body binding); paths TBD | `13720935595fedabec2c376dc933629b0deae5aa` / `dfe7dfe42b4d3b6a15d839afb6d895fbe1a167b3` | Session and implant operations couple runtime apparatus ports to a body and inferred binding; target stable effector contracts now exist but no full session boundary. No target tests. Revisit after Modality/Embodiment identity and lifecycle contracts are ratified; adapter binding must not be treated as physical authority. |
| `transition.py`: `EmbodimentDescriptor`, lifecycle/checkpoint helpers, memory and sensory-prior carry-over | DEFER | Primarily `organism`; split candidate with `embodiment` lifecycle; paths TBD | `42ff87fe2102d1a26eb218a5c071ddfb90f42e34` / `4c6f47478223e67fe6234c984c832aaec4aeae18` | Imports `symbiont` package internals, host checkpoint identity/continuity, cognitive schema, longitudinal history, reactivity and archive code. No target tests. Revisit only with explicit Organism continuity plus owner checkpoint/adoption contracts; split lifecycle state from host orchestration and preserve provenance. |

No source file in this tranche is classified DROP: inspected evidence does not
demonstrate that any remaining material is obsolete or safely removable. All
DEFER entries are provisional classifications, not final dispositions. Before
declaring migration complete, revisit every DEFER row against its stated trigger
and record a final MOVE, SPLIT, REWRITE or DROP decision with tests and caveats.
Source test paths above identify existing source evidence only; they do not
imply that the source suite was run for this documentation change.
