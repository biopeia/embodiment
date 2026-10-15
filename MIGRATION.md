# Migration record

## Source baseline

- Source repository: local `symbiont-lab` monorepo
- Source SHA: `80d372a186513035f85a769db886e505cabba52d`
- Architecture audit baseline: `cef998a55aae32ed8b2f7373079c11667b01e915`
- Original package root: `symbiont/src/symbiont/core/embodiment/`

## Initial slice records (historical extraction snapshot)

This table records the first copied candidate slice as it was documented; it does not override the pinned symbol-level dispositions below. Where the tables differ, the pinned inventory is the current migration disposition. A copied blob is provenance evidence, not semantic acceptance.

| Source path | Disposition | Target path | Notes |
| --- | --- | --- | --- |
| `symbiont/src/symbiont/core/embodiment/physiology.py` | SPLIT | `src/embodiment/physiology.py` | Somatic body state slice; copied unchanged. Last source-path commit at baseline: `538fa01dcaf4d80e63983f948aee4028fc5c2bef`. |
| `symbiont/src/symbiont/core/embodiment/metabolism.py` | SPLIT | `src/embodiment/metabolism.py` | Carries current per-kind accounting coupled to body state; ownership of non-somatic accounting remains subject to boundary review. Last source-path commit at baseline: `13720935595fedabec2c376dc933629b0deae5aa`. |
| `symbiont/src/symbiont/core/embodiment/physiology_config.py` | SPLIT | `src/embodiment/physiology_config.py` | Somatic configuration remains an Embodiment candidate. The unused `prospective_*` deliberation parameters are excluded and separately classified as DROP in the pinned symbol inventory; they are not implicitly assigned to Organism. Last source-path commit at baseline: `ca10871706a02def5afe62d059b04046dee4876c`. |
| source unit tests | REWRITE | `tests/` | Focused contract checks authored for the extracted slice; no source files changed. |

No source history is asserted for this reconstructed multi-file slice. Provenance
is the pinned source SHA and paths above. The source monorepo remains intact.

## Open source dispositions and exclusions

The detailed pinned core-package inventory below records each material module
and its source disposition. `DEFER` rows remain open, name the owning domain and
state a revisit condition. Cross-owner Lab solver/runtime files are out of scope
for this repo inventory; Lab owns their separate disposition.

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

- `physiology_config.py` excludes unused `prospective_*` parameters, dispositioned as DROP in the pinned inventory; this does not implement Organism deliberation or transfer those fields to Organism.
- Python distribution/import name is `embodiment`; no `biopeia_*` prefix is used.
- The additional `physics3d.mechanics` module is a physical-apparatus value contract, not a new semantic authority or a claim that Physics3D is owned by Embodiment in full.
- `physics3d.observation_contract` is a coordinate/kinematics declaration only; its metadata tests do not establish runtime conformance.
- This package contains extracted slices only; no whole-package CURRENT/TARGET compliance is implied.
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

**Disposition superseded by the Architecture Owner ratification dated
2026-10-09:** the historical extracted implementation and its target tests are
`DROP`, not TARGET behavior. The records below preserve provenance only. The
Biopeia implementation, export, and tests have been removed; no compatibility
surface is retained. New Embodiment-owned somatic dynamics remain a required
TARGET capability, but are not implemented by this historical cycle or by a
replacement formula in this change.

| Source element | Disposition | Target path | Provenance / boundary |
| --- | --- | --- | --- |
| `symbiont/src/symbiont/core/embodiment/body.py` — `Body.tick_physics()` behavior only | DROP | None | Source repository SHA `80d372a186513035f85a769db886e505cabba52d`; source-path commit `13720935595fedabec2c376dc933629b0deae5aa`; pinned source blob `84d57d7a820070699314f3e21d0349da18751398` (SHA-256 `cbbdfd7e1d1e49f61266c0eaa1af05be1b9b00e1fb6971bdf2dc93599f2624ad`). The former extracted operation applied source-specific basal debit, passive wear, and age advancement in a legacy order with legacy defaults. These are not ratified TARGET dynamics. |
| Focused checks for the extracted body cycle | DROP | None | `tests/test_somatic_cycle.py` checked only the legacy extracted operation and is removed as a TARGET test. Its historical assertions do not define Biopeia behavior. |

`Body.apply_damage()` was not copied because its current behavior delegates to
`LivingBodyState.apply_wear()` and adds no distinct somatic transition. The
source monorepo remains unchanged. This DROP does not negate the ratified need
for new somatic dynamics; it prevents the legacy cycle from being treated as
their implementation. The evidence-backed contract and implementation work is
tracked in [Embodiment issue #20](https://github.com/biopeia/embodiment/issues/20);
until its evidence and owner-transition inputs are established, no replacement
formula is introduced.

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
90–94 and 194–197). This extracted value does not establish target-wide compliance
or runtime conformance. The source monorepo remains unchanged.
## Additional slice: owner command to physical-effector projection

| Source element | Disposition | Target path | Provenance / boundary |
| --- | --- | --- | --- |
| Opaque `MotorCommand` / `ActuatorSurface` and current ordinal adapter behavior | REWRITE / COMPOSE | `src/embodiment/physics3d/actuation_projection.py` | Source provenance at pinned SHA `80d372a186513035f85a769db886e505cabba52d`: `symbiont/src/symbiont/actuation/action.py` and `surface.py` (path commit `13720935595fedabec2c376dc933629b0deae5aa`); `lab/src/lab/integration/physics3d/apparatus.py` (commit `792d2dbd3e507d1d41300456cf826d8efe19fddb`); `lab/src/lab/physics3d/runtime.py` (commit `5e9a250f103373ed1333c05f96bc2554abdf5020`); `embodiment/src/embodiment/physics3d/articulated.py` (commit `cea69ac01681811cce0ed23d87c514b9eb048fdb`). Current ordinal mapping and zero-default are source behavior only, not target authority. |
| Owner-selected morphology and per-effector quantity contracts | NEW STRUCTURAL CONTRACT, refined by MIG-006 Phase A | `MorphologyLike`, `EffectorContractLike` in `src/embodiment/physics3d/actuation_projection.py`; concrete mapping in `src/embodiment/physics3d/actuator_binding.py` | Require stable effector IDs, body ID, embodiment episode ID, morphology revision, command kind, quantity, unit, minimum, neutral, maximum, and explicit saturation policy. Only `reject` is implemented; no clipping or physical unit is invented. The binding is immutable, Embodiment-owned, revision-scoped, and has a strict versioned checkpoint/restore representation and canonical SHA-256 content fingerprint. |
| Focused projection tests | REWRITE / EXTEND | `tests/test_actuation_projection.py` | Checks stable-ID matching under permuted binding order, sparse omission, binding/body/episode/morphology checks, checkpoint round trip and tamper/unknown-field rejection, declared quantity/range/neutral/unit/saturation contracts, and malformed/duplicate mappings. |

The target association is explicit: each command actuator ID resolves through
an Embodiment-owned `EmbodimentActuatorBinding` to a stable effector ID; channel
order has no mapping authority. The binding is tied to body, embodiment episode,
and morphology revision, pins the Organism source-surface fingerprint, and its
versioned checkpoint rejects unknown fields and content whose fingerprint does
not verify. Projection requires this concrete
owner binding rather than accepting a caller-constructed structural surface.
Every emitted channel explicitly repeats `body_id`,
`embodiment_episode_id`, `morphology_revision`, `effector_id`, and
`command_kind`, as well as the value and its quantity/unit/range/neutral/
saturation contract. The candidate carries the binding identity and its stable
content fingerprint. Command, binding, active morphology, pose, and Embodiment
checkpoint must agree on body and episode; the binding and active morphology
must also agree on morphology revision. This contract does not authorize or
correlate a World physical step; that remains a separate World-issued context.

MIG-006 Phase A provenance: source code is a fresh TARGET rewrite, not copied
legacy implementation. Historical reference paths remain
`symbiont/src/symbiont/actuation/{action.py,surface.py}` at pinned source SHA
`80d372a186513035f85a769db886e505cabba52d` (path commit
`13720935595fedabec2c376dc933629b0deae5aa`), plus the solver-facing consumer
`lab/src/lab/integration/physics3d/apparatus.py` at path commit
`792d2dbd3e507d1d41300456cf826d8efe19fddb`. TARGET changes are based on
Embodiment `origin/main` `4bb43338c77379c7e89f785b8c5b10000b44cd1a`.
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

## Additional slice: owner-side physical result adoption and checkpoint value

| Source element | Disposition | Target path | Provenance / boundary |
| --- | --- | --- | --- |
| Correlated solver body candidate and Embodiment adoption boundary | NEW STRUCTURAL CONTRACT | `src/embodiment/physics3d/physical_transition.py` | Candidate correlation includes World, causal tick, physical-step ID, body, embodiment episode, morphology revision, environment revision, and solver configuration revision. The solver remains a numerical executor; this module validates and adopts through an immutable owner-state transition. |
| Embodiment physical-state checkpoint representation | NEW STRUCTURAL CONTRACT (schema v2) | `EmbodimentPhysicalState.checkpoint_bytes()` / `restore_checkpoint()` | Deterministic JSON bytes encode owner identity, episode, morphology revision, world tick, pose, root linear/angular velocity, their SI units and reference frame, contract revision, and last accepted step correlation. SHA-256 is a stable content identifier only. The v2 decoder does not accept the earlier candidate-only v1 encoding. |
| Free-root rigid-body dynamic state needed by deterministic physical execution | NEW TARGET CONTRACT; no legacy implementation/API migrated | `EmbodimentPhysicalState`, `SolverBodyCandidate`, and `BodyPhysicalInput` in `src/embodiment/physics3d/` | Root linear velocity is explicitly metres/second and root angular velocity radians/second, both expressed in the pose's declared reference frame. Embodiment validates finite 3-vectors and adopts them only with a matching causal correlation. The state is body/episode/morphology-bound. This slice does not invent joint position/velocity state or articulated dynamics semantics; those require separate owner contracts. |
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

This inventory classifies the 24 material implementation modules directly under
`symbiont/src/symbiont/core/embodiment/` at source commit
`80d372a186513035f85a769db886e505cabba52d`. In the source/blob column,
`path@commit/blob` records the last source-path commit at that pinned revision
and the Git blob object ID at the pinned revision. Target paths are relative to
the indicated Biopeia repository. This supplements, and does not replace, the
concrete slice records above. The tracked `__init__.py` export facade is not
counted among the 24 material implementation modules; its disposition is SPLIT
(selectively re-export only symbols once their own slices are accepted). There are
25 tracked Python files total. The inventory is evidence-based disposition, not
permission to copy deferred implementation or an assertion that CURRENT source
behavior is a TARGET contract.

| Source file and material symbols | Disposition | Target repository/path | Source path commit / pinned blob | Reason, evidence/tests, caveats, and revisit trigger |
| --- | --- | --- | --- | --- |
| `adaptation.py`: `AdaptationSnapshot`, `EmbodimentAdaptation` | DEFER | Embodiment for any physical adaptation state; Organism for learned prediction/update semantics | `13720935595fedabec2c376dc933629b0deae5aa` / `85edb6a3713777d32b6a7cbe4f26757042504d22` | Prediction-residual adaptation is coupled to `dynamics.py`; no target tests establish an owner/update contract. Do not copy until physical state and learned model semantics are separated. **Linked dependency:** [Organism #44](https://github.com/biopeia/organism/issues/44), which must close its predictor-vs-zero-output evidence gap before learned adaptation claims can be reconsidered. **Review date:** 2026-11-15; at review, record MOVE/SPLIT/REWRITE/DROP per symbol or a successor Issue if #44 is still open. |
| `agency.py`: `ChannelStat`, `PerceptualStructure`, `SensorimotorModel`, `ChannelInterventionRecord`, `AgencyModel`, inferred body-region/schema/self-model types | DROP | None | `13720935595fedabec2c376dc933629b0deae5aa` / `8e452d866061d7bef83e1bfe6631be25f489d15b` | Aligns with Organism's pinned inventory: this historical agency-inference specimen is retired and is not a Biopeia domain capability. Source tests `symbiont/tests/unit/core/test_embodiment_agency.py` and `test_embodiment_v2.py` are historical evidence only; scores, thresholds, and API are not carried forward. |
| `assimilation.py`: `AssimilationAction`, `AssimilationDecision`, `InformationAssimilator` | SPLIT | Organism-owned epistemic/learning behavior only if a target contract requires it; no Embodiment target | `13720935595fedabec2c376dc933629b0deae5aa` / `28c9824474f2ad50b347c928772b361cefbbb9e5` | Aligns with Organism's pinned inventory. Information valuation is not somatic state. Historical tests are evidence of former behavior, not target equivalence. No Embodiment copy is authorized; unsupported assertions are candidates for DROP when the Organism learning issue resolves the owner contract. |
| `body.py`: `Body`, `create_standard_body`, `ReceptorPort`, `PhysicalEffect`, `EffectorPort`, `ActivationConsequence` (excluding separately recorded `tick_physics`, `MaterialTransfer`, `absorb_material`) | SPLIT / REWRITE, final per-symbol disposition | Existing `LivingBodyState` in `physiology.py` for somatic state; Modality for transduction; `actuation_projection.py` and `physical_transition.py` for command validation/adoption; solver for numerical execution; test fixtures only for `create_standard_body` | `13720935595fedabec2c376dc933629b0deae5aa` / `84d57d7a820070699314f3e21d0349da18751398` | Reconciles with Organism's pinned `body.py` REWRITE disposition. `Body` is SPLIT: its body identity/state maps to the existing Embodiment-owned `LivingBodyState`; no standalone `Body` compatibility API is retained. `ReceptorPort` and `transduce_signals` are SPLIT to source-measurement owner and Modality; sampling is not Observation authority. `EffectorPort` is SPLIT to stable Embodiment descriptor/identity plus solver execution; `execute` is REWRITE as a candidate-producing solver operation. `PhysicalEffect` and `ActivationConsequence` are REWRITE as non-authoritative typed candidate data. `apply_damage`, `apply_activations`, `get_receptor/get_effector`, and break/repair operations are REWRITE as owner-validated transitions/projections. `create_standard_body` is REWRITE as a test fixture only, not a production morphology default. Existing source oracle: `symbiont/tests/unit/core/test_clean_embodiment_episode.py`; target `tests/test_intake.py`, `test_actuation_projection.py`, `test_physical_transition.py` cover bounded slices only; no aggregate runtime equivalence is asserted. |
| `body_schema.py`: `DependencyKind`, `BodySchemaEngine` and internal evidence/classification helpers | SPLIT | Physical part/morphology semantics → Embodiment; cognitive regions/private model semantics → Organism; no monolithic target path | `c077496ba8bb73cbd3940dda6516672bcd1f7376` / `909c67c8988e95186aab3053210a847c1761a7ba` | Aligns with Organism's pinned inventory. The historical engine imports Organism limits/epistemic conventions and derives cognitive evidence, not authoritative physical morphology. Source tests are historical evidence only. Any physical schema must be a separate owner contract; generated identifiers and historical assertions are not copied wholesale. |
| `contract.py`: `PerceptualChannel`, `PerceptualSurface`, `TimingContract`, `EmbodimentContract` | REWRITE | Embodiment-owned physical/perceptual projection, coordinated with Modality and Observation; no monolithic target path | `13720935595fedabec2c376dc933629b0deae5aa` / `85076bceaff300ff4a593f4bdc81ae78de1751b4` | Aligns with Organism's pinned inventory. The source combines surface, timing, perception and actuator semantics; it cannot be moved as one contract. Existing target physical projection and observation-contract checks cover narrower declarations only. Historical index-derived IDs and timing meanings are not target guarantees. |
| `degradation.py`: `RetentionState`, `RetainedItem`, `DegradationQueue` | SPLIT | Embodiment only for explicitly defined somatic/physical waste; Organism for private-memory retention; no generic target queue | `c077496ba8bb73cbd3940dda6516672bcd1f7376` / `cfc40aebf5afa228108ca00f29b439fe83ff0c06` | Aligns with Organism's pinned inventory. The generic source queue does not identify an authority or physical quantity. No whole-module copy; historical tests do not authorize a general state manager. Any physical waste contract needs typed quantity and owner transition; any private retention uses Organism-owned state. |
| `development.py`: `DevelopmentalPhase`, `DevelopmentalSnapshot`, `DevelopmentalTracker` | SPLIT | Organism-owned developmental identity/longitudinal state versus Embodiment-owned body development; no monolithic target module | `1a7b70730c2730932086c4dff7fd922fb5c8e293` / `a727788628fbf86b311c66c4403387ac6e56ab00` | Aligns with Organism's pinned inventory. The source does not separate organism development from physical maturation. Phase labels are not a Biopeia ontology by inheritance; each owner must define and test only its own state transition. |
| `duration.py`: `PhysicalDuration` | MOVE (copy-first) | `embodiment/src/embodiment/duration.py` | `74bd7a0099341410465fe9e540f93e6ef7266bc2` / `965fd3bb62f08c2c582e5b785233955d796297ee` | Already extracted and byte-identical at the pinned source (SHA-256 and tests are recorded above). `tests/test_duration.py` checks finite nonnegative physical seconds. It is a supplied duration value, not a clock or causal scheduler. |
| `dynamics.py`: `EvidenceProvenance`, `PredictionResidual`, `SensorimotorDynamicsModel` | REWRITE | Embodiment motor/physical dynamics capability behind explicit effector/percept identity; predictive/learned interpretation remains Organism-owned | `13720935595fedabec2c376dc933629b0deae5aa` / `579620bc4167bbcdc9e442dfc42149373c94ed91` | Aligns with Organism's pinned inventory. Source residuals/model updates cross owner-observation and learning state; neither implicit list-position correspondence nor source units/frames/authority are carried forward. Target actuation/physical-projection tests validate narrower contracts, not dynamics equivalence. |
| `episode.py`: `EmbodimentState`, `EmbodimentEndReason`, `ContractTransition`, `EmbodimentEpisode` | REWRITE | Embodiment-owned episode identity/state; World coordinates causal lifecycle; no monolithic source runtime | `6ff37a6d9fa6cc455c3db2b5238bba60a25ead3d` / `e085f4edc4603200cd0a9ad3591a596e3d75b54f` | Aligns with Organism's pinned inventory. The source couples body schema, adaptation, actuation evidence/bindings, memory and reachability. No target episode/runtime tests establish equivalence; source tick/checkpoint behavior is not World durability or commit protocol. |
| `history.py`: `EmbodimentEpisodeSummary` | REWRITE | Embodiment-owned passive summary with explicit episode/revision provenance | `13720935595fedabec2c376dc933629b0deae5aa` / `a5d20ad2fcf1cd5156ebaa6ba690d78eddc891d7` | Aligns with Organism's pinned inventory. Any target summary must remain passive data and not become a second authority; source serialization is not compatibility. No target summary equivalence is claimed; do not conflate it with Observation replay. |
| `homeostasis.py`: `HomeostaticAction`, `HomeostaticSnapshot`, `HomeostaticController` | REWRITE | Embodiment somatic state transition; World coordinates causal adoption | `a1c613cb89b117359018cc8bdfa15384d3af7e06` / `4dd604719b1d568490bc0fff29bbcd8b4a1c0e7c` | Aligns with Organism's pinned inventory. Source thresholds/actions are unvalidated controller semantics. Embodiment #20 tracks new evidence-grounded somatic dynamics; it does not authorize copying this historical cycle. Target state tests do not establish homeostatic regulation or physiological efficacy. |
| `lifecycle.py`: `LifeState` | DROP | None | `13720935595fedabec2c376dc933629b0deae5aa` / `1dd3367acaf457be5b6f4837b2440c5a750221d2` | `LifeState` is a retired historical label, not an Organism identity or Embodiment `VitalState`; no Biopeia target semantics are inherited. |
| `lifecycle.py`: `ViabilityController` | REWRITE | Embodiment body viability input/transition, consumed under Organism and World lifecycle boundaries | `13720935595fedabec2c376dc933629b0deae5aa` / `1dd3367acaf457be5b6f4837b2440c5a750221d2` | Aligns with Organism's pinned inventory: body viability belongs to Embodiment; organism identity/life remains separate. Embodiment #26 tracks depletion/death semantics. The historical controller's irreversible terminal transition is not copied and does not authorize implicit organism death. |
| `longitudinal.py`: contract fingerprinting, historical motor candidates, memory injection, epoch summary and end-reason helpers | SPLIT | Embodiment episode summaries; Organism cognition/agency memory; World/owner lifecycle as applicable; no monolithic target path | `42ff87fe2102d1a26eb218a5c071ddfb90f42e34` / `f4c7529be153f54199e1480a6216bdead1c4ea57` | Aligns with Organism's pinned inventory. The module composes multiple authorities. Source tests are historical evidence only; classify each helper at its owning target boundary before claiming longitudinal feature parity. Unsupported helpers are DROP candidates, not compatibility obligations. |
| `memory.py`: `BodySpecificMemory`, `EmbodimentPrior`, `EmbodimentArchive`, `archive_episode_checkpoint` | DEFER | Embodiment for body/episode references; Organism for learned priors/private memory; durable custody requires an explicit owner contract | `f004081a9c70c10109eaeb95d9fb4067488451fa` / `9fe68589710a3f5f6a7514123b73ccaba602c3b7` | Combines body identity with learned prior and episode checkpoint archiving; current target checkpoint bytes do not establish ownership, custody or cross-episode semantics. **Linked dependency:** [Organism #45](https://github.com/biopeia/organism/issues/45) for completeness/exactness of cognitive checkpoint fields; it is necessary but not sufficient for archive durability. **Review date:** 2026-11-15; record MOVE/SPLIT/REWRITE/DROP per symbol after reviewing #45, or create a dedicated successor issue if archive ownership remains unresolved. |
| `metabolism.py`: `ResourcePressure`, `MetabolicSnapshot`, `MetabolicLedger` | SPLIT | Somatic resource/energy state → `embodiment/src/embodiment/metabolism.py`; private computational-budget semantics → Organism; no single-owner historical-module equivalence | `13720935595fedabec2c376dc933629b0deae5aa` / `4ba6b77486d32fac7a2a98d4f32ce3707f59f1bb` | Aligns with Organism's pinned inventory. Current Embodiment's accounting candidate is body-energy-backed and does not by itself establish ownership of computational budget semantics; target `tests/test_somatic_state.py` and `tests/test_checkpoint.py` cover bounded candidate behavior only. This supersedes the earlier whole-module MOVE wording above: the historical source module mixes somatic state and computational costs, and copied bytes are not semantic acceptance. |
| `ontogeny.py`: `PhysicalLifeStage`, `OntogenySnapshot`, `OntogenyController` | REWRITE | Embodiment-owned physical development state; reproduction/offspring coordination requires separate domain owners | `13720935595fedabec2c376dc933629b0deae5aa` / `3f7ec7453c277d7fb905fd152628243194c73a12` | Aligns with Organism's pinned inventory. Source couples metabolism, body state and physiology configuration; historical stage labels and thresholds are not Biopeia ontology or calibrated laws. No reproduction/evolutionary efficacy claim is made. |
| `physiology.py`: `VitalState`, checkpoint helpers, `BodyStructureState`, `LivingBodyState`, `PhysiologySnapshot`, `PhysiologyController` | SPLIT | Embodiment body/somatic state → `embodiment/src/embodiment/physiology.py`; Organism identity/continuity and cross-owner checkpoint coordination remain separate | `538fa01dcaf4d80e63983f948aee4028fc5c2bef` / `be27d6590f28436c3ed02683aa0dd9173b14b355` | Aligns with Organism's pinned inventory. A byte-identical file copy is migration evidence, not full-file semantic acceptance. Target `tests/test_somatic_state.py` and `tests/test_checkpoint.py` verify bounded body-state/checkpoint behavior only. `VitalState.DEAD` is not TARGET `ORGANISM_DEATH`; no cross-owner authority, durability, physical validity, or source-wide equivalence is established. |
| `physiology_config.py`: somatic `PhysiologyConfig` parameters excluding `prospective_*` and `somatic_reference_duration_s` | SPLIT | `embodiment/src/embodiment/physiology_config.py` | `ca10871706a02def5afe62d059b04046dee4876c` / `7f3c23364f4093d62ff25ac2af2373183c5cb1f7` | Somatic configuration is an extracted candidate, not approval of every rate or formula. `tests/test_somatic_state.py` covers bounded state behavior only. |
| `physiology_config.py`: unused `prospective_*` deliberation parameters | DROP | None | `ca10871706a02def5afe62d059b04046dee4876c` / `7f3c23364f4093d62ff25ac2af2373183c5cb1f7` | The fields are unused in the extracted target slice and no accepted Organism contract or consumer is evidenced by the pinned ledgers. They are not transferred to Organism solely because their names suggest deliberation; no compatibility behavior is retained. This agrees with Organism's pinned inventory, which allows DROP for these prospective fields. |
| `physiology_config.py`: `somatic_reference_duration_s` and its legacy Physics3D default | DROP | None | `ca10871706a02def5afe62d059b04046dee4876c` / `7f3c23364f4093d62ff25ac2af2373183c5cb1f7` | Explicitly dropped by Architecture Owner ratification dated 2026-10-09. The field encoded a legacy reference duration for preserving a pre-M2 trajectory; it is not a TARGET causal/physical time scale. |
| `reachability.py`: `ReachabilityRelation`, `ReachabilityModel` | DEFER | Embodiment for physical feasibility constraints; Organism for learned action expectation; no target module is approved | `13720935595fedabec2c376dc933629b0deae5aa` / `aa20bf98182c518a8df3fdf5a3bab166122af027` | The source model mixes physical affordance and inferred capability. No target tests. **Linked dependencies:** [Organism #41](https://github.com/biopeia/organism/issues/41) for agency/actuation state and [Organism #44](https://github.com/biopeia/organism/issues/44) for prediction evidence. These are related dependencies, not claims that either issue fully implements reachability. **Review date:** 2026-11-15; resolve the owner split and record MOVE/SPLIT/REWRITE/DROP per symbol, or open a dedicated successor Issue if neither dependency covers it. |
| `reembodiment.py`: `select_prior`, `begin_reembodiment`, `replace_body` | DEFER | Embodiment for body/episode adoption; Organism for private-state continuity and prior selection; World for causal lifecycle coordination | `13720935595fedabec2c376dc933629b0deae5aa` / `e5ede03a28c335c062f222b1d11346d1741025f9` | Composite source helper is not copied; stable Organism, body and episode identities plus explicit continuity/provenance are required. **Linked dependencies:** [Organism #45](https://github.com/biopeia/organism/issues/45) (checkpoint completeness) and [Organism #41](https://github.com/biopeia/organism/issues/41) (agency/actuation state). Neither alone authorizes re-embodiment. **Review date:** 2026-11-15; record per-symbol disposition once both dependencies clarify owner-state boundaries, or create a dedicated successor Issue if they do not. |
| `session.py`: `PortBinding`, `EmbodimentSession`, `implant`, `implant_body` | REWRITE | Embodiment projection/adoption; Modality transduction; World causal coordination as separate contracts | `13720935595fedabec2c376dc933629b0deae5aa` / `dfe7dfe42b4d3b6a15d839afb6d895fbe1a167b3` | Aligns with Organism's pinned inventory. Session/implant code couples apparatus ports, body and inferred binding. Existing target actuation-projection tests cover a smaller explicit physical-command contract only; no positional authority, implicit channel defaults, or compatibility session facade is carried forward. |
| `transition.py`: `EmbodimentDescriptor`, lifecycle/checkpoint helpers, memory and sensory-prior carry-over | SPLIT | Embodiment transition/adoption; Organism checkpoint transformation/private state; World lifecycle orchestration | `42ff87fe2102d1a26eb218a5c071ddfb90f42e34` / `4c6f47478223e67fe6234c984c832aaec4aeae18` | Aligns with Organism's pinned inventory. Source imports composite runtime/checkpoint, cognitive schema, longitudinal history, reactivity and archive code; it is not copied as one owner. No target equivalence test. Preserve owner identity and provenance across the separate contracts. |

Except for the symbol-level DROP dispositions recorded above, inspected
evidence does not demonstrate that the remaining material modules are obsolete
or safely removable. All DEFER entries are provisional classifications, not
final dispositions. Before declaring migration complete, revisit every DEFER
row against its stated trigger and record a final MOVE, SPLIT, REWRITE or DROP
decision with tests and caveats.
Source test paths above identify existing source evidence only; they do not
imply that the source suite was run for this documentation change.

## Additional slice: articulated physical-state adoption (target-authored)

| Source elements | Disposition | Target path | Provenance / boundary |
| --- | --- | --- | --- |
| No direct legacy state-adoption implementation is migrated. This is a target-authored composition of the already rewritten `ArticulatedBodySpec`/URDF projection (`embodiment/src/embodiment/physics3d/articulated.py`, source-path commit `cea69ac01681811cce0ed23d87c514b9eb048fdb`), `BodyPoseSample` (`embodiment/src/embodiment/observation.py`, source-path commit `be3236ce13c3aff22353726b5b7aa00ff3e7eac7`), and the source Embodiment body-state implementation under `symbiont/src/symbiont/core/embodiment/`; pinned source repository SHA: `80d372a186513035f85a769db886e505cabba52d`. | REWRITE / COMPOSE | `src/embodiment/physics3d/articulated_state.py`, `src/embodiment/physics3d/articulated_spec.py` | Target implementation binds root and joint state to body, episode, morphology revision, and an active owner-provided descriptor. Checkpoint v2 persists and fingerprints the complete declared morphology separately from the generated URDF description; restore is owner-bound and rejects stale or mismatched identity, revision, schema, units or morphology. |
| Focused target contract checks | REWRITE | `tests/test_articulated_state.py`, `tests/test_articulated_spec.py` | Covers identity-based adoption under permuted collection order, invalid/missing/duplicate/out-of-range joint values, stale morphology, full-spec fingerprint/restore, descriptor-bound checkpoint restore, deterministic encoding, and continuation through a second causal step after value restore. |

This is not a copied compatibility layer and does not preserve the legacy
runtime's ordinal conventions. `ActiveArticulatedMorphology.from_spec()` must
be called at the Embodiment owner boundary with the descriptor active for the
body episode and morphology revision. The descriptor is not self-authenticating;
the module does not prove that an arbitrary caller obtained it from that owner.
The articulated checkpoint schema v2 includes the complete declared
`ArticulatedBodySpec`, its full-spec SHA-256, and a separate generated-URDF
SHA-256. The full-spec digest covers fields omitted by URDF formatting (such as
contact links, material, fixed-base status, spawn height and schema revision),
and preserves numeric precision beyond the rendered URDF text. The morphology
revision remains an explicit owner-supplied identity; the content digest does
not authenticate a caller or independently select the active morphology. An
Embodiment owner boundary constructs the active descriptor from its active
specification and binds restore to that descriptor. Schema v1 is rejected;
there is no compatibility fallback. The checkpoint is a deterministic value
encoding only: this slice does not provide durable storage, crash recovery,
solver execution, Environment adoption, or World commit, and does not complete
the end-to-end physical causal step milestone. The two-step test exercises
value-level continuation in one process; it is not evidence of process restart
or durable recovery. Articulated topology order remains constrained by the existing
`ArticulatedBodySpec`/URDF builder contract; candidate state correspondence is
by stable joint ID, not collection position. The source monorepo remains
unchanged.

## Pinned source inventory: apparatus/body models in `embodiment/physics3d`

### Scope and decision status

This inventory covers the 11 tracked Python files at source commit
`80d372a186513035f85a769db886e505cabba52d` that were not already dispositioned
in the mechanics, observation-contract, and articulated-description slices
above: the package export facade plus ten body/apparatus modules. The three
previously inventoried modules are intentionally not duplicated here.

The dispositions below are source-inventory outcomes, not authorization to copy
legacy code. They apply only to the pinned source symbols and tests in scope;
they do not close migration in other repositories or all Embodiment work. The
TARGET boundary is ratified: Embodiment owns body truth, Modality transduction,
solver implementations are numerical capabilities, World causal coordination,
and Observation is passive. Historical source remains unchanged. No
compatibility API or shim is retained. `DROP` means no source implementation
moves; any future need must be designed as a fresh TARGET implementation.

The provenance column gives `last source-path commit / pinned Git blob` at the
source SHA above. Source paths are relative to `symbiont-lab`; target paths are
relative to the named Biopeia repository. Cross-owner Lab consumers are listed
as evidence only and remain owned/dispositioned by Lab's inventory.

| Source file and top-level material symbols | Final disposition and target owner/path | Source provenance | Consumers, tests, evidence and caveats |
| --- | --- | --- | --- |
| `embodiment/src/embodiment/physics3d/__init__.py`: package facade (docstring only; no executable exports at the pin) | **DROP**; empty historical facade has no executable exports. TARGET imports use explicit modules; no compatibility facade is required. | `13720935595fedabec2c376dc933629b0deae5aa` / `a4d580f27367fb6831584d06a08bf87c4ead1cca` | Pinned file has no imported names or definitions; explicit target module imports cover retained contracts. |
| `asymmetric.py`: `_deg`, `ASYMMETRIC_JOINT_SPECS`, `ASYMMETRIC_SEGMENTS`, `ASYMMETRIC_TOPOLOGY`, `ASYMMETRIC_SPEC`, `AsymmetricPhysics` | **DROP** source-specific model and solver implementation. Target morphology is represented by owner-supplied revision-bound descriptors; no source preset is selected as canonical. Any selected body is authored against TARGET contracts, not mechanically ported. | `84e55453f0b3e3889be7c65e8a61e72af337faa7` / `536520e2ea4fd8108d9147069b023c41dc9942f5` | Consumed by source `physics3d/bodies.py`, Lab integration/runtime and `lab/physics3d/effective_model_audit_cli.py`; tested with alternatives in `embodiment/tests/unit/lab/physics3d/test_alternative_bodies.py`. Geometry and parameters are source implementation, not evidence of calibration. Downstream source consumers are cross-owner Lab; their existence does not create a target requirement. No calibration or TARGET selection evidence. |
| `bodies.py`: `BodyDescriptor`, `BodyRegistry`, `ANTHROPOMORPHIC_V6`, `CRAWLER_V1`, `SPOT_INSPIRED_V1`, `ASYMMETRIC_V1`, `HEXAPOD_V1`, `ROBOTIC_ARM_V1`, `vision_body_descriptor` | **DROP** source registry, factory coupling, labels and observer/presentation projection. TARGET owner descriptors/projections are separate contracts and do not preserve these preset identities or factory API. | `73dc9a8cc4cbd79192d42d77481988ca7be1feb7` / `2c12c549dc290a4d6508461ac69032161a7b03c3` | Directly imported by source `lab/src/lab/integration/physics3d/bodies.py`; related composition appears in `lab/src/lab/physics3d/runtime.py`. Source tests include `test_alternative_bodies.py` and `test_robotic_bodies.py`. Descriptor currently mixes opaque channel IDs, solver factories, observer geometry, display labels, and sensory capacity. Target owner descriptors and passive observation contracts are separately authored; no source registry API or presentation labels are retained. |
| `contracts.py`: `MotorPortPair`, `Physics3DAppliance` | **SPLIT / REWRITE**. Effector command semantics are represented by `src/embodiment/physics3d/actuation_projection.py`; sensory/transduction portions are **DROP from Embodiment** and remain Modality-owned; solver-facing execution is **DROP** as source migration. Existing TARGET projection is not a port of this combined appliance protocol. | `66358c6e4f618f376cfdd495ec1f8a45c0b07baf` / `fa9b8d48ea49aa979f9e06ae130e44b1beefcd25` | Consumed by source `lab/src/lab/integration/physics3d/apparatus.py`. `Physics3DAppliance` combines receptor sampling, effector IDs and motor bindings in one runtime protocol. Compare with target `physics3d/actuation_projection.py`, `physical_projection.py`, and `physical_transition.py`; those target contracts already require stable effector identity and explicit physical semantics. Source actuator behavior is not retained verbatim; target actuation projection covers explicit owner semantics, while sensor and solver aspects are outside this owner inventory. |
| `crawler.py`: `_deg`, `CRAWLER_JOINT_SPECS`, `CRAWLER_SEGMENTS`, `CRAWLER_TOPOLOGY`, `CRAWLER_SPEC`, `CrawlerPhysics` | **DROP** source crawler preset and numerical class; no canonical body or evidenced target requirement. Future fixture/morphology must be authored for its experiment under TARGET contracts. | `84e55453f0b3e3889be7c65e8a61e72af337faa7` / `7f305f3263d8e6b375fd97998430fe6787d93aae` | Consumers include source `physics3d/bodies.py`, Lab runtime, and `effective_model_audit_cli.py`; tests in `test_alternative_bodies.py`. A crawler fixture appearing in tests does not make it canonical or production TARGET. No current TARGET use is established; any future selected morphology is a new target-authored contract. |
| `hexapod.py`: `_deg`, `_LEGS`, `HEXAPOD_SPEC`, `HexapodPhysics` | **DROP** source hexapod preset and numerical class; source test coverage is not a TARGET requirement. No compatibility migration. | `8a3d9e25f9ca192f1c8fdd4b25aed8ef22b45f5f` / `846cca1253d1a743bc0ae0aca6f206ee1dcab70a` | Consumed through `physics3d/bodies.py` and source Lab runtime; `test_robotic_bodies.py` asserts hexapod anatomy, while `test_alternative_bodies.py` exercises construction. The test assertions establish source behavior only, not that this morphology is required by Biopeia. No TARGET requirement is established by source tests; stable identity is required by future target contracts. |
| `humanoid.py`: `BODY_KIND`, `BODY_STATE_SCHEMA_VERSION`, solver/passive-tone constants, receptor-count constants; `physical_receptor_contract_ids`, `interoceptive_receptor_contract_ids`, `receptor_contract_ids`, `effector_contract_ids`; `JOINT_SPECS`, `JOINT_LIMITS`, `JOINT_AXES`, `_LEFT`, `_LEFT2`, `_RIGHT`, `_RIGHT2`, `SEGMENTS`, `JOINT_TOPOLOGY`, `CONTACT_LINK_NAMES`, `STRUCTURAL_NEIGHBOUR_NAMES`, `CYLINDRICAL_COLLISION_LINKS`; `_deg`, `_fmt`, `_box_inertia`, `_segment_link_xml`, `_carrier_link_xml`, `_cylinder_inertia`, `mechanical_joint_limits`, `build_anthropomorphic_urdf`, `_end_range_resistance`, `_neutral_rest_position`, `_passive_postural_tone`; `ANTHROPOMORPHIC_SPEC`; `HumanoidPhysics` | **DROP** source humanoid fixture, sensory contracts, solver execution and engine state schema as a bundle. Existing target-authored articulated descriptors/adoption are narrower and do not preserve source model identity or constants. | `792d2dbd3e507d1d41300456cf826d8efe19fddb` / `d0d78278aa3fcfb80f16f534ee6437b6e4a82d7e` | Central consumer via source `bodies.py`, Lab runtime and apparatus; test evidence includes `test_dynamics.py`, `test_alternative_bodies.py`, `test_robotic_bodies.py`, plus downstream Lab tests. The file mixes anatomy, receptor/effector surfaces, solver settings, URDF projection and engine state schema. Source constants/schema labels do not themselves establish TARGET semantics or calibration. Source constants do not establish target calibration; future morphology requires stable part identity, morphology revision, units and frames. |
| `robotic_arm.py`: `_deg`, `ROBOTIC_ARM_JOINT_SPECS`, `ROBOTIC_ARM_SEGMENTS`, `ROBOTIC_ARM_TOPOLOGY`, `ROBOTIC_ARM_SPEC`, `RoboticArmPhysics` | **DROP** source fixed-base arm preset and numerical class; no selected TARGET requirement. TARGET articulated body contract is independently authored. | `8a3d9e25f9ca192f1c8fdd4b25aed8ef22b45f5f` / `d0045302d5cac0cef038b32734f354d752621f79` | Consumed by source `bodies.py`, Lab runtime and effective-model audit; covered by `test_robotic_bodies.py` and `test_alternative_bodies.py`. Fixed-base semantics are part of this fixture, not a universal morphology rule. No selected TARGET requirement is established; any future fixed-base apparatus is authored independently. |
| `scene.py`: `DEFAULT_GRAVITY`, `PhysicsScene` (MuJoCo model/data, compilation, stepping, state, name lookup, and geometry primitives) | **DROP** source MuJoCo scene/runtime implementation from Embodiment. A future solver adapter must be newly implemented against owner projections and candidate/adoption/World commit contracts; scene internals are not migrated. | `0f75c709bba8bfc9505a769662e9bf0e8e7e074a` / `0c1d848dd5022d85f5d3e1794be3868d485a69f3` | Direct source consumers include `lab/src/lab/physics3d/runtime.py`, `lab/src/lab/physics3d/effective_model_audit_cli.py`, and `test_alternative_bodies.py`/`test_dynamics.py`. MuJoCo scene compilation and stepping cannot become Environment or World ownership; solver/config revision and candidate adoption need explicit correlation. MuJoCo may be used as an initial solver candidate, but this source implementation is not migrated; a new adapter must honor candidate/adoption/commit boundaries. |
| `spot.py`: `_deg`, `_LEGS`, `SPOT_INSPIRED_SPEC`, `SpotInspiredPhysics` | **DROP** source Spot-inspired fixture and numerical class; approximation is not required TARGET morphology and has no approved canonical use. | `eed3c32abe9ace87dddc91d52150cf5acc874e4e` / `d0197bdee5ec1c1eff5a7922aff89494f618dfd0` | Consumed by source `bodies.py` and Lab runtime/audit; `test_alternative_bodies.py` exercises it. “Spot-inspired” is an approximation label, not a claim of equivalence to a commercial robot or calibrated hardware. No canonical TARGET use or calibration is established; any experiment requiring this body must define it independently. |
| `vision.py`: `VISION_BODY_KIND`, `VISUAL_ARRAY_SIDE`, `VISUAL_RECEPTOR_COUNT`, `HEAD_MOUNT_LINK`, `HEAD_MOUNT_OFFSET`, `HEAD_MOUNT_GAZE_OFFSET`, `VISION_TOTAL_RECEPTOR_COUNT`, `_VISUAL_PERMUTATION_SEED`, `_visual_permutation`, `visual_receptor_contract_ids`, `vision_receptor_contract_ids`, `VisionHumanoidPhysics` | **DROP** source vision model, receptor permutation, sensory behavior and solver implementation from Embodiment. Future body parts and transducers require owner-specific TARGET contracts; no source API is retained. | `0f75c709bba8bfc9505a769662e9bf0e8e7e074a` / `8a7fe0591e7a5c938b32018a0252535aec59cab3` | Consumed through source `bodies.py`, `lab/src/lab/integration/physics3d/bodies.py` and Lab runtime; per-body budget is described in `ADR-0011` and its source test context. A receptor ID/permutation does not itself define a sensory semantic or authorize visual knowledge in Organism. This source implementation does not establish sensor identity, transduction semantics or authority; future modality/body contracts are separately owned. |

### Source-owned core behavior tests in the inventory scope

The following source unit-test files exercise modules directly under the pinned
Embodiment core package. Disposition names the test artifact's target owner and
evidence, and does not imply the source suite was run or ported. `DEFER` is open:
its owner and exact revisit condition are stated explicitly.

| Source test file | Disposition / target owner and evidence | Source path commit / pinned blob | Reason and open condition |
| --- | --- | --- | --- |
| `symbiont/tests/unit/core/test_physiology.py` | REWRITE → Embodiment; `tests/test_somatic_state.py` | `282c44eea894faedb57763c3545a1401cf032a86` / `5f96a067b081a0fde9911ea5bb43c56fac043611` | Target tests current bounded body physiology values, not all source behavior. |
| `symbiont/tests/unit/core/test_metabolism.py` | SPLIT → Embodiment `tests/test_somatic_state.py`, Organism lifecycle inventory for lifecycle assertions | `282c44eea894faedb57763c3545a1401cf032a86` / `3420ac8f1da9bb63f668a9e6b3d8f0358ae513a5` | Body resource accounting is covered; Organism death/lifecycle assertions do not belong in Embodiment. |
| `symbiont/tests/unit/core/test_body_structure_state.py` | REWRITE → Embodiment `tests/test_somatic_state.py`, `tests/test_checkpoint.py` | `b2fd85c0c18d0be1b2c4a3682a181b604b799455` / `746f850740c0bc727c4434aa71b4694f3078d91b` | Target checks cover selected somatic/checkpoint contracts; no source schema compatibility. |
| `symbiont/tests/unit/core/test_clean_embodiment_episode.py` | Cross-domain historical test evidence; owner-specific assertions split among Embodiment, Modality and World. Not an Embodiment `DEFER` disposition. | `6769f8e3ce157d347126796966d20fa6433e54a0` / `d0826fcf55aca1b4490d95fbeda2840224301603` | Embodiment target tests cover selected intake, actuation projection and physical transition contracts. The aggregate source runtime assertion is not ported; no exact source-equivalence or target-wide closure is claimed. Any remaining causal integration is a dependency on its owning repository, not an Embodiment migration item. |
| `symbiont/tests/unit/core/test_temporal_domains.py` | REWRITE → Embodiment `tests/test_duration.py` | `282c44eea894faedb57763c3545a1401cf032a86` / `ee96f1267f6763855c7a33d2bea69662f1a45aca` | Only physical-duration value behavior belongs here; other temporal domains remain separately owned. |
| `symbiont/tests/unit/core/test_temporal_scales_m1.py` | SPLIT → Embodiment `tests/test_duration.py`; nonphysical/cognitive timing assertions remain Organism-owned | `1baeeefde791d09af609c6b052ed56d9ad091cb8` / `2c6bb9d38ed26411fad808a141827e63d5015608` | Source design explicitly separates time scales; no universal clock port. |
| `symbiont/tests/unit/core/test_homeostasis.py` | DROP source controller assertions; physiological control semantics are not ratified or calibrated | `282c44eea894faedb57763c3545a1401cf032a86` / `a1830a34e2b02eeb71a04725378179f343afba1c` | No target controller or evidence basis; re-open only if an approved, unit-bearing homeostasis contract is adopted. |
| `symbiont/tests/unit/core/test_ontogeny.py` | SPLIT → Organism development; Embodiment physical maturation only after an explicit target contract | `282c44eea894faedb57763c3545a1401cf032a86` / `78fe34877b46adda9228d7ff0556ed52185f0c99` | Existing source thresholds are not TARGET laws; review when Organism development contract and body structural-change contract exist. |
| `symbiont/tests/unit/core/test_assimilation.py` | DROP from Embodiment; Organism owns cognitive assimilation | `282c44eea894faedb57763c3545a1401cf032a86` / `ce85d127bc884a77f1b7ed543dee38674f9bb519` | Source package placement is not authority; no Embodiment assertions retained. |
| `symbiont/tests/unit/core/test_degradation.py` | Cross-domain historical test evidence; Organism-owned dependency, not an Embodiment test disposition. | `282c44eea894faedb57763c3545a1401cf032a86` / `9eb8692639146c9b601559c9981e665ea9e67b4d` | The source `DegradationQueue` depends on Organism retention/lifecycle limits. The Organism migration inventory is the place to disposition its symbols; no target test port or exact equivalence is claimed here, and no unrelated open Organism Issue is treated as covering it. |
| `symbiont/tests/unit/core/test_lifecycle.py` | SPLIT → Organism lifecycle inventory; body `VitalState` remains Embodiment-only | `282c44eea894faedb57763c3545a1401cf032a86` / `3200a14841004fc0696135d23ac6a655010abb4f` | Source controller finalizes organism death; does not map to body state. |
| `symbiont/tests/unit/core/test_embodiment_agency.py` | SPLIT → Organism self-model/agency inventory; physical identities remain owner inputs | `282c44eea894faedb57763c3545a1401cf032a86` / `f844ff910ce0face59bb25d55caf118c0475f6a3` | Not an Embodiment behavior test merely because of source path. |
| `symbiont/tests/unit/core/test_embodiment_v2.py` | SPLIT → Organism agency/body-schema inventory; only physical contract pieces separately covered by target actuation/adoption tests | `d69ec7af0111472b7eab9596b40c5d3b2d426998` / `a4d42e224ebbc819461d44ad9eed3d31aaa45eb4` | Mixed source test file; no direct wholesale port. |
| `symbiont/tests/unit/core/test_body_schema.py` | DROP from Embodiment; Organism owns inferred body schema | `6ff37a6d9fa6cc455c3db2b5238bba60a25ead3d` / `04b79bdcb87fd9592aaf52b954f4731d4361cd48` | Cognitive schema is not physical morphology or body truth. |
| `symbiont/tests/unit/core/test_body_schema_agentic.py` | DROP from Embodiment; Organism owns agentic schema inference | `2ae96d4735fe72d57b7f7611bb9e2c8fcf51175d` / `ca8781af502cbfc4a1d4c7cfb3af38a2d446579e` | No Embodiment target behavior retained. |
| `symbiont/tests/unit/core/test_cognitive_body_schema.py` | DROP from Embodiment; Organism owns cognitive schema | `6ff37a6d9fa6cc455c3db2b5238bba60a25ead3d` / `6464af929e7eb2b10b8f7848df2464bc8abf2aa1` | Source terminology does not confer somatic authority. |
| `symbiont/tests/unit/core/test_cognitive_body_schema_longitudinal.py` | SPLIT → Organism longitudinal inventory | `282c44eea894faedb57763c3545a1401cf032a86` / `2bc6ca2acc6c9c3b8a41bbb0c84a88e850f12567` | Longitudinal learning/memory is outside Embodiment; body identity may be typed input only. |
| `symbiont/tests/unit/core/test_somatic_continuous_m2.py` | REWRITE → Embodiment `tests/test_physical_transition.py`, `tests/test_articulated_state.py` for owner adoption; solver and integrated-run assertions remain unimplemented | `7f5a3e6fc4c8bc60589cb7c28a66bbf16593cd86` / `34ec895dfd74e225cdb0fa29243cf5405e39a24a` | Existing tests cover value-level adoption/restore only, not durable process restart or World commit. |

### Directly relevant source tests and test disposition

The following pinned tests are source evidence, not tests run for this
documentation change. Dispositions distinguish retained target owner contracts
from source-specific fixture assertions. Solver/runtime tests belong to a future
solver capability or workspace integration suite, not isolated Embodiment unit
tests when they import other owners.

| Source test | Relevant evidence | Final test disposition and target evidence |
| --- | --- | --- |
| `embodiment/tests/unit/lab/physics3d/test_alternative_bodies.py` | Tests source preset constitution/dimensions, headless loading, settling, replay, solver checkpoint, and fixed-base/root behavior. Source provenance: path commit `80e6435c92c1d61f14ad25f87fefaec210b4db15`, blob `94468cd8b8d2de756938c76220e7fa5306c02df1`. | **DROP** source assertions with the unselected body presets/runtime. Target contracts have independent coverage in `tests/test_articulated_spec.py`, `tests/test_articulated_state.py`, `tests/test_physical_projection.py`, and `tests/test_physical_transition.py`; future solver tests are not yet present. |
| `embodiment/tests/unit/lab/physics3d/test_robotic_bodies.py` | Checks source hexapod structure and fixed-base arm/flange. Source provenance: path commit `8a3d9e25f9ca192f1c8fdd4b25aed8ef22b45f5f`, blob `5049683b3116c1bd283ea9b77e451da5eff33398`. | **DROP** with source presets; target-authored articulated contracts are tested independently and do not require these body shapes. |
| `embodiment/tests/unit/lab/physics3d/test_dynamics.py` | Applies source deterministic actuation and checks humanoid joint hard limits. Source provenance: path commit `792d2dbd3e507d1d41300456cf826d8efe19fddb`, blob `28b5c5c3c5c12cf411d4b0fa9886e3ceadd60d75`. | **DROP** with source solver/body implementation. Owner candidate acceptance has separate target tests; future solver numerical tests are not yet implemented. |
| `embodiment/tests/test_observation_contract.py` | Asserts source pose/joint/physiology observation semantics. Source provenance: path commit `ef097993716b6d494d6a60ab846e9c34af85964e`, blob `77a1fd381413a3321504a0bca30dddd04b6c83a2`. | **SPLIT / REWRITE**: metadata assertions are in `tests/test_physics3d_observation_contract.py`; pose value checks are in `tests/test_body_pose_sample.py`; remaining joint/physiology observations are not currently represented by this target package. |
| `embodiment/tests/test_self_contained.py` | Source test imports the legacy preset registry and asserts source-only body/receptor composition plus absence of other monorepo domains. Source provenance: path commit `80e6435c92c1d61f14ad25f87fefaec210b4db15`, blob `71a89732395fe9f8fbe05a2b99cb92353fbb39ea`. | **DROP**. Biopeia Embodiment has no target requirement that other repositories be absent from the host environment; Python package independence is declared by `pyproject.toml` (`dependencies = []`), and source preset assertions are dropped with those presets. No source API/import compatibility is preserved. |

Pinned-baseline consumer search also identified
`lab/src/lab/app/physics3d/{monitor/converters.py,monitor/viewer.py,runs.py}`;
`lab/src/lab/physics3d/runtime.py`;
`lab/src/lab/integration/physics3d/{apparatus,bodies}.py`;
`lab/src/lab/physics3d/effective_model_audit_cli.py`;
`lab/src/lab/studies/learning/{embodied_counterfactual.py,embodied_intervention.py,embodied_sensorimotor_shadow.py,visual_acquisition.py}`;
and `lab/src/lab/studies/physics3d/constitution_audit.py`, in addition to the
listed source tests. These consumers establish that the source package served
apparatus/runtime composition, monitoring, audits and experiments; they do not
make those responsibilities Embodiment TARGET semantics. In the inspected
Biopeia Embodiment checkout, no imports or tests currently consume the
unresolved source names listed above. Existing target tests for
`articulated_spec`, physical projection/transition, and articulated state cover
narrower target contracts; they do not demonstrate migration or conformance of
these source body models, registries, sensors, or solver scene.

### Final-disposition rule

The apparatus/body-model rows and direct Physics3D test rows above have final
source-disposition labels. The earlier core-module inventory still contains
`DEFER` entries; each is explicitly open, with a named semantic owner and a
review trigger in its row. Those DEFERs are not final dispositions and prevent
claiming complete Embodiment source-inventory closure. This document closes only
the source apparatus/body-model subset and does not claim all Embodiment
migration, all source tests, or global Biopeia migration complete. Cross-owner
Lab runtime, experiments, monitors, evidence and associated tests are not
re-dispositioned here; Lab owns their inventory. The source monorepo was not
modified. No status in this table grants permission to copy legacy code or adds
backward compatibility.

## Target contract correction: owner-bound articulated physical projection

**Disposition: REWRITE the existing Biopeia target projection.** This is a
target-side correction, not an extraction of legacy behavior. It addresses
Biopeia Embodiment issue [#32](https://github.com/biopeia/embodiment/issues/32)
and finding F-0115, documented in the issue as
`biopeia/docs/explanation/embodiment/physical-projection.md`. The implementation
base is Embodiment `f995dcf7d35d4c71dbfbd65a51c68132dd17ea9f`; the source
monorepo SHA remains the inventory baseline above and was not modified.

The prior API accepted morphology, pose, velocities, and correlation as
independent arguments. The rewritten projection consumes one
`ArticulatedEmbodimentPhysicalState` and an explicit
`PhysicalStepCorrelation`. It binds projection to the source body's World,
causal tick, body identity, embodiment episode, and morphology revision, then
projects root pose and velocities plus joint position/velocity by stable joint
identity. It carries the complete joint identity/range set, explicit `m`/`m/s`,
`rad`/`rad/s` semantics through typed fields, morphology revision and content
digest, contact links, surface material, and fixed-base declaration. Direct
construction of the immutable solver input validates identity, units, finite
values, quaternion normalization, joint identity/range completeness, material
value finiteness, and fixed-base type.

The replaced public function signature is removed; no compatibility overload
or shim is retained. Focused target-authored checks are in
`tests/test_physical_projection.py` and cover state binding, stable articulated
projection, immutable snapshot behavior, and invalid direct input.

This projection only verifies correlation equality against its source owner
state; it does **not** authenticate that World authorized the execution. It does
not implement solver execution, owner adoption, Environment projection,
cross-owner authorization, durable recovery, or World commit. Detailed physical
interpretation of material coefficients remains for a solver-adapter contract.
The change does not close the first end-to-end physical causal-step milestone
or the full migration inventory.


### Target contract correction: physiology-complete somatic checkpoint

**Disposition: REWRITE the existing Biopeia target checkpoint contract.** This
is a target-side integrity fix for Embodiment issue
[#27](https://github.com/biopeia/embodiment/issues/27), not a migration of
legacy checkpoint code or API. The bounded base is Embodiment
`97cb09a82b0bc9bf4ad11f6497cce071b85efedd`. The historical source remains
read-only and no legacy implementation or compatibility behavior is copied.

The envelope advances from schema v1 to v2 and the nested
`MetabolicLedger` format from v2 to v3. The checkpoint now preserves the exact
`PhysiologyConfig` and in-progress per-kind `spent` accumulators. Restore
validates exact field sets, config types and invariants, accounting ranges,
physical energy values, and schema versions; prior schemas and unknown fields
are rejected rather than defaulted or ignored. A supplied restore configuration
must match the stored configuration.

Target-authored tests in `tests/test_checkpoint.py` cover deterministic
round-trip, custom threshold preservation, pressure interpretation, pending
spend and deterministic continuation, old/unknown schema rejection, and
malformed configuration/accounting. This does not define a World tick-phase
checkpoint policy, correlate this envelope to a World causal cut, prove
crash/power-loss durability, or make a scientific-equivalence claim. World and
Lab consumers must move to the v2 owner schema explicitly before using the new
format; no compatibility fallback is provided.

### Target contract correction: World-context-bound candidate adoption

**Disposition: REWRITE the existing Biopeia owner adoption boundary.** This is
a target-side correction for Embodiment issue
[#25](https://github.com/biopeia/embodiment/issues/25), not a migration of
legacy behavior. The bounded implementation base is Embodiment
`6114f3d9bcc0d5c44ecbfb6262f87f5824f92903`. Issue evidence was recorded at
Embodiment `a5129f0`; no source-monorepo code is copied or changed by this
correction.

Root and articulated adoption now consume a structural `WorldPhysicalStepContext`
view with World ID, source and target causal ticks, physical-step ID, body and
embodiment episode identities, morphology revision, Environment revision,
and solver configuration revision. Embodiment derives its local correlation
from that context, requires the target tick to immediately follow the source
tick, and validates the candidate against both the context and active owner
state. The API no longer accepts a separately caller-selected expected
correlation; there is no compatibility overload. Embodiment has no runtime
dependency on the World package.

The context protocol is a structural typing boundary, **not authentication**.
The adapter must pass the context received through the active World
coordinator call path. Adoption returns a staged immutable owner value; it
does not enforce global single-use, publish a causal result, or claim a
durable checkpoint. World selects the owner reference made authoritative by
its committed causal cut. This change does not claim malicious-adapter
resistance, rollback, complete physical runtime, solver execution, or durable
recovery.

Target-authored tests in `tests/test_physical_transition.py` and
`tests/test_articulated_state.py` cover valid context binding, exact identity
and revision matching, invalid tick/revision rejection, stable joint
identity under collection permutation, staged-value semantics, and checkpoint
round-trip. Validation on this patch: `uv run pytest -q` (136 passed),
`uv build --no-sources`, and `git diff --check` passed. World cross-repository integration callers must be updated to pass
the World-issued context and repin Embodiment in a separate World-owned slice;
that follow-up is not included in this Embodiment change.


### Target sensor fixture: stable Embodiment receptor attachment

Embodiment issue [#43](https://github.com/biopeia/embodiment/issues/43),
parent [Modality #13](https://github.com/biopeia/modality/issues/13), adds a
fresh target-authored receptor descriptor and source-cut sample-point
projection. The implementation is based on Embodiment main
`e53f4a07f52cf6afb7f08788dc81923ec98b3c24`; no historical sensor code is an
input (`DROP` as target code; no compatibility adapter).

`EmbodimentReceptor` binds a stable `receptor_id` to `body_id`,
`embodiment_episode_id`, `morphology_revision`, an explicit body frame, and a
finite metre offset. Projection validates the active Embodiment owner state
against the World physical step's source causal cut, rotates the local offset
using the owner pose, and emits a sample point in that pose's declared
reference frame. Receptor collection order has no authority; duplicate IDs
are rejected. The structural World-context view checks correlation but is not
authentication or proof of World authorization.

Target tests cover stable identity under permutation, frame and source-cut
projection, quaternion rotation, stale/mismatched body binding, duplicate IDs,
and non-finite location rejection. This slice assigns no meaning to the
sampled scalar and does not implement Environment field sampling, Modality
transduction, Organism intake, causal commit, sensorimotor learning, or a
complete physical loop.

### Target physical actuator fixture: revision-bound joint torque

Embodiment issue [#47](https://github.com/biopeia/embodiment/issues/47)
authorizes a target-authored joint torque command projection in
`src/embodiment/physics3d/joint_torque.py`. The binding correlates each opaque
actuator ID with a stable morphology joint name (`joint_id`), declared axis,
body ID, embodiment episode and morphology revision. Collection position and
solver-native IDs are not used as authority.

The input is a typed request: every channel explicitly declares
`joint_torque` in `N*m`; untyped numeric channels cannot be relabelled as
torque. The output range is derived from the active morphology's declared
maximum motor torque and its neutral value is zero. A joint name is the stable
joint identity within the bound morphology revision. The declared axis is in
the joint frame, whose identity is scoped to that joint and morphology
revision; parent/child link identities are included to make the topology
context explicit. Positive torque follows the right-hand convention about
that axis. A missing input channel produces no command. Non-finite and
out-of-range input is rejected; there is no clipping. The strict binding
checkpoint is versioned and rejects unknown fields.

This candidate projection does not execute a solver, prove delivered torque,
adopt authoritative body state, or commit World state. It is a new TARGET
contract, not a legacy API alias or compatibility bridge.

### Target identity-bound BodyPose observation projection

Embodiment issue [#52](https://github.com/biopeia/embodiment/issues/52) adds
`BodyPoseObservationProjection`, a fresh owner-derived value from the adopted
`EmbodimentPhysicalState`. It combines the existing `BodyPoseSample` with
`world_id`, adopted `causal_tick`, `body_id`, `embodiment_episode_id`, and
`morphology_revision`. When a physical step exists, it carries the complete
last-step identity/revision correlation and validates the source tick and pose
sample identity. It rejects mismatched body identity and incomplete or stale
step correlation. A pose labeled `physics_step` is invalid unless its owner
state retains the matching physical-step correlation; construction, projection,
and checkpoint restoration all fail closed on that missing provenance. An
initial pose with no physical-step correlation remains valid when it is not
represented as a physics-step sample.

The implementation is based on Embodiment `main`
`b5714f985d0aa970d3a412a7d29e43fa0bcb89d6`. Existing
`BodyPoseSample` and `EmbodimentPhysicalState` are reused as TARGET inputs; the
projection and owner factory are new TARGET code, not a historical copy. The
projection stays independent of Observation and does not claim that World
committed the state. World must independently verify the commit before an
Observation publication path exposes it. This slice adds no wire format,
transport, semantic interpretation, or compatibility behavior, and does not
complete the end-to-end migration acceptance cycle.
