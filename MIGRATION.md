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
