# Embodiment spatial-render projection contract candidate v1

**Status: proposed for Embodiment-owner review; not an accepted final contract.**

This candidate operationalizes the design-base disposition recorded on Embodiment #77. It defines a bounded *semantic* contract for separate static articulated geometry and dynamic link poses. It does not define an Observation record, wire/API schema, transport, persistence, access policy, or publication authorization. It changes no runtime behavior. Spatial Visualization V1 remains `proposed / not_evaluated / UNRESOLVED`.

## Purpose and boundary

A consumer may draw only owner-authored display geometry at owner-provided link transforms. It must not infer anatomy, run forward kinematics, interpret solver/checkpoint formats, or use the current root-only `embodiment.body_pose` as a substitute for articulated geometry.

Two projections are separate:

1. **Static render morphology** — relatively stable, bounded description of displayable geometry and its declared articulated topology.
2. **Dynamic rendered-link poses** — one already-computed world pose per renderable link for a particular physical candidate/cut. This is not a physics solver output requested from Frontend.

A composed cross-domain scene is usable only after the World contract supplies verifiable evidence that the dynamic sample belongs to the exact confirmed cut. A matching tick, shared label, or matching morphology fields alone is insufficient. This document defines no World proof/token; see World #162.

## Evidence baseline and capability disposition

Inspected source revisions:

- Embodiment `main@d73315d87bbb3f2eea14e8c33812b37b59a5d72f`.
- World `main@51cea9f8975fbdea603592fa5e9c56b073a2f4d4`.
- Existing Observation response bound inspected at `observation` source; this contract does not raise or otherwise change it.

| Capability | Current evidence | Candidate disposition |
|---|---|---|
| Authored segment primitive, dimensions and visual origin | `src/embodiment/physics3d/mechanics.py:63-68` (`SegmentSpec`); `physics3d/articulated_spec.py:_segment_link_xml` emits a box with the authored origin and `rpy="0 0 0"`. | Reuse only this explicitly authored box subset. Current source does not separately name a render-only frame/revision. |
| Joint parent/child and local origin | `JointTopology` at `mechanics.py:71-76`; `build_articulated_urdf` emits origin translation with zero RPY. | Reuse topology and translation, with local frame meanings explicit below. |
| Joint axis and joint units | `JointSpec.axis`; `observation_contract.py` declares revolute, radians and radians/second. `build_articulated_urdf` emits its axis. | Static axis is dimensionless, normalized, expressed in the joint frame; dynamic contract does not require exporting joint scalar state. |
| Body/root pose and frames | `observation_contract.py` declares metres, right-handed `+Z`, `xyzw`, `physics3d.world`, `body.root`; `BodyPoseSample` is root-only. | Reuse these existing names/conventions for world-space link poses, subject to the explicit orientation meaning and owner review below. |
| Active morphology identity | `ActiveArticulatedMorphology` binds body, episode, morphology revision, spec; full morphology SHA also covers non-render fields. | Preserve `body_id`, `embodiment_episode_id`, `morphology_revision`; add separate render geometry revision/digest. Do not expose/reuse full morphology digest as the render digest. |
| Per-link world transforms | `ArticulatedEmbodimentPhysicalState` stores root and joint scalar state only. In World `adapters/articulated_mujoco.py`, same-step `mj_forward` is followed by reading only root `data.xpos/xquat` plus joint scalars; it returns no per-link transforms. | A real integration dependency remains: World must pass through same-step solver link transforms, Embodiment validates/binds them to its active morphology, and the resulting projection becomes Embodiment-semantic only under an explicit owner-approved producer boundary. No second FK implementation. |
| Verified committed-cut evidence | `PhysicalStepCorrelation` carries proposed step/source identifiers; `BodyPoseObservationProjection` expressly is not a World commit receipt. | World #162 must provide the independent post-commit proof/reference. A source tick alone cannot authorize publication or a coherent scene. |

The repository’s existing solver input/URDF and checkpoint encodings are internal representations, not browser publication contracts. Current source proves inputs that could support the static subset and proves MuJoCo computes same-step body poses; it does **not** prove an existing Embodiment-owned per-link output or current publication authorization.

## Proposed static projection semantics

### Identity and version binding

Each static projection is bound to:

- `contract_revision = embodiment.render_morphology/v1`;
- `body_id` and `embodiment_episode_id`;
- active `morphology_revision`;
- owner-assigned `geometry_revision` (a compatibility/version identity, not inferred from a hash); and
- `render_geometry_sha256` (content identity of the display-only subset, defined in Digest below).

`geometry_revision` and `render_geometry_sha256` are distinct: revision identifies the owner’s declared geometry version; the digest lets a consumer detect content changes. The owner must define revision lifecycle and whether/how it changes. No consumer may treat the full internal `morphology_sha256` as equivalent because it includes mass, mechanics, material and other excluded fields.

### Display geometry and topology

The exact proposed field meanings are:

| Field | Meaning / constraints |
|---|---|
| `coordinate_system` | `right_handed_z_up`; explicitly declares basis, not a new World frame identity. |
| `length_unit` | `m`. |
| `segments[]` | Stable `segment_id` (the Embodiment-owned link ID), `shape = box`, positive finite `dimensions_m[3]`, and `visual_origin_in_link_m[3]`. The box is centered on its local visual origin, as in the current URDF visual shape; local rotation is the identity only because the current producer emits zero RPY. |
| `joints[]` | Stable `joint_id`, `parent_link_id`, `child_link_id`, `joint_type = revolute`, `joint_origin_in_parent_m[3]`, and `axis_in_joint_frame[3]`. Axis is finite, nonzero, normalized; angle direction follows the right-hand rule and is in radians. Joint-origin rotation is identity only because current URDF emits zero RPY. |
| Fixed links | No shape is created for a carrier or link that has no authored `SegmentSpec`. Fixed-link display support is excluded from this first candidate unless its own owner-authored geometry exists. |

Only `box` is accepted in this candidate because that is the current authored segment primitive. Sphere/cylinder/mesh support is not implied. Do not publish segment color/material, mass/inertia, contacts, receptor/effector data, solver settings, actuator limits, checkpoints, URDF text, or any other private/mechanical field.

All joint link references must identify declared Embodiment links. The topology is descriptive, not an instruction to the client to compute link transforms.

## Proposed dynamic projection semantics

A dynamic projection contains:

- the exact static binding tuple (`body_id`, `embodiment_episode_id`, `morphology_revision`, `geometry_revision`, `render_geometry_sha256`); the consumer must resolve the static descriptor for that identity and require exact equality before applying any pose;
- `source_world_id` and a World-authored opaque `confirmed_cut_reference` supplied/validated under #162 (not authored or interpreted by Embodiment);
- `physical_step_id` as step provenance only, never as proof of commit;
- `reference_frame = physics3d.world`, `length_unit = m`, right-handed `+Z` basis;
- one pose for **each and only each renderable `segment_id`** in the static descriptor: `segment_id`, translation `[x,y,z]` metres, and unit quaternion `orientation_xyzw` describing the segment link frame orientation in the reference frame (`R_world_from_link`, maps link-local vectors into world coordinates); and
- an explicit completeness state that is either `complete` or rejected/unavailable. Partial transform sets are not renderable as an articulated body.

The consumer must verify exact static identity/revision/digest matches, exact link-set equality, finite translation, a unit quaternion within a documented tolerance, and World’s exact-cut proof before composing/claiming a coherent scene. The static `render_geometry_sha256` binds the dynamic set to the geometry content only; it is not the digest of the dynamic poses and is not a World cut proof. The selected World cut must bind the particular dynamic transform sample (or a World-authorized content identity for it) to that exact confirmed cut. World #162 owns the cut-reference/proof and any canonicalization or digest needed for that binding; Embodiment does not mint a cut token, assert post-commit status, or define a second cut-evidence layer. Until that World-authored binding is specified and verifiable by the consumer, the dynamic pose set is not eligible for a causally coherent scene. Quaternion antipodes `q` and `-q` denote the same rotation; the dynamic records are not a historical stream and are not sorted by arrival time into a causal history.

### Producer and authority split (integration dependency)

This proposal deliberately separates **numeric transform production** from **Embodiment semantic ownership**:

- **World physical adapter / MuJoCo** is the evidenced candidate producer of the numeric transforms: it already calls `mj_forward` for the physical candidate and MuJoCo makes body world positions/orientations available in that same `MjData`. In the current candidate path, however, World reads/returns only the root transform plus joint scalars. Passing every needed link transform from that same `MjData` through the World→Embodiment physical candidate is a required, not-yet-implemented integration edge.
- **Embodiment** owns the morphology/link identities, local geometry semantics, binding to its active body/episode/morphology, validation that exactly the authored link set is present, and any Embodiment-semantic projection built from an accepted source candidate. It must not recalculate the transforms. If the domain owners do not approve this producer/validation split, the articulated body remains unavailable to Frontend; do not fall back to frontend FK.
- **World** remains authoritative for physical execution and commit/cut proof. Embodiment cannot mint, verify, or reinterpret the World cut reference. #162 must define how the consumer validates that the projection is from one confirmed cut.
- **Observation** may carry only after its own approved passive, bounded contract. It must not join static/dynamic families or manufacture completeness/cut semantics.
- **Frontend** may render a fully bound projection only; it may not fill missing data or simulate motion.

The static descriptor and dynamic poses can be implemented/published independently once each owner-approved dependency is satisfied. Static geometry alone may be displayed as a clearly partial morphology view; it must never imply a current physical pose or a coherent World/Environment scene.

## Bounds proposed for owner review

Proposed per-body hard bounds (these are candidate ceilings, not current approved limits):

- at most **128 declared links**, **128 display segments**, and **127 revolute joints**;
- static canonical descriptor at most **256 KiB**;
- dynamic complete transform set at most **256 KiB**.

Reject over-limit input before constructing/publishing a projection. These per-family ceilings stay below Observation’s existing **1,000,000-byte HTTP response cap** but do not authorize allocating that whole cap to Embodiment or changing Observation limits. Observation’s aggregate response may also contain other approved families. Owners should lower/adjust these values if evidence or memory budgets require it; the renderer must not silently truncate.

## Canonical digest proposal

`render_geometry_sha256` is lowercase SHA-256 over a domain-separated canonical serialization of exactly the static **render subset**, not the dynamic pose or identity metadata. The preimage object contains `contract_revision`, `schema_version`, `coordinate_system`, `length_unit`, `segments`, and `joints`; arrays are sorted by stable ID, and each object has only its declared fields. `body_id`, episode, morphology/geometry revisions and any World/cut identifiers are checked separately and are not geometry content. Unknown fields are rejected before digesting.

Candidate byte canonicalization for the **static geometry digest only**: UTF-8 RFC 8785 JSON Canonicalization Scheme (JCS), no BOM or trailing newline, finite IEEE-754 numbers only, no NaN/Infinity, no rounding/truncation, zero normalized per JCS, exact Unicode strings with no silent normalization. Prefix bytes are `biopeia:embodiment.render_morphology/v1\n`; hash exactly `prefix || JCS(render-subset-object)`. This avoids depending on Python-only `json.dumps` formatting. The current full `articulated_body_spec_sha256` is explicitly not reused. This layer does not serialize or hash dynamic poses and does not establish their association with a World cut. Any dynamic-payload digest or canonical bytes used by a World cut proof belong to World #162 and remain unspecified here; do not infer one from this static digest.

One simple candidate conformance vector (the sample is illustrative, not a current morphology). It uses exactly the candidate digest field set above; `joints` is empty and the field names match the proposed descriptor:

```text
JCS bytes:
{"contract_revision":"embodiment.render_morphology/v1","coordinate_system":"right_handed_z_up","joints":[],"length_unit":"m","schema_version":1,"segments":[{"dimensions_m":[0.2,0.1,0.1],"segment_id":"body.root","shape":"box","visual_origin_in_link_m":[0,0,0]}]}

Domain prefix bytes:
biopeia:embodiment.render_morphology/v1\n
Candidate SHA-256:
62a6a5dc9be0d29cabfbd1d5c55079988dd7e6f85b6f14816d15ebae8ef0c234
```

The hash is reproduced over the displayed UTF-8 bytes with sorted keys, compact separators, and finite values only; that script is a simple digest check, not an independent RFC 8785 conformance implementation. Before normative adoption, run this vector through an independently implemented JCS conformance test. The hash above is a draft vector for the shown bytes, not current production evidence.

## Conformance vectors to implement only after contract approval

**Accept**

1. Static descriptor has unique stable IDs, box dimensions all finite and positive, valid parent/child joint references, normalized finite joint axes, exact declared field set, deterministic render digest.
2. Dynamic pose set matches one static identity/digest tuple and every renderable link exactly once; values are finite, units and frames match, quaternion norms are within the approved tolerance, and the World consumer proof validates the exact committed cut.
3. Same geometry values serialize to the same render digest regardless of input mapping order; changing a display dimension/origin/topology changes the digest; changing excluded mass/material/torque values does not.
4. Static-only descriptor may render a geometry preview explicitly labeled as lacking dynamic pose/current cut.

**Reject or mark unavailable**

1. Duplicate/empty IDs, unknown keys, unsupported primitive, non-finite/zero/negative dimensions, invalid or unresolved joint topology, non-finite/zero axis, mismatched units/frame, invalid quaternion.
2. Any dynamic/static mismatch in body, episode, morphology revision, geometry revision, or digest; missing/duplicate/extra transform; non-finite coordinate.
3. Missing, forged, unverified, or mismatched World cut reference; same tick by itself; candidate physical step without evidence of committed target cut.
4. Partial per-link transforms, over-limit counts/encoded bytes, or invalid source provenance. No truncation, last-value reuse, extrapolation, or substitute geometry.
5. Morphology identity does not authorize a body projection after episode/body changes. Existing root BodyPose alone is not accepted as an articulated render sample.

These are acceptance vectors for later owned tests; no tests for a nonexistent projection were run here.

## Owner decisions still required before this is a normative contract

1. Confirm/revise exact abstract field set, names, local frame meanings, identity local rotations encoded today as zero RPY, axis frame and right-hand angle convention.
2. Confirm the separate `geometry_revision` lifecycle, and whether the static render digest uses JCS exactly as proposed.
3. Confirm the hard caps and digest byte bound; these numbers are proposed, not silently adopted from Observation’s cap.
4. Confirm the World-produced same-step transform → Embodiment-validation boundary and acceptance of the relevant MuJoCo link frame as the transform source. World #162 must also specify how its cut proof binds that particular dynamic transform sample to the confirmed cut. These are cross-domain integration dependencies; they are not settled solely by Embodiment’s geometry authority. The World cut proof must not be confused with or replaced by `render_geometry_sha256`.
5. Specify which links are renderable when carrier/fixed links lack an authored segment shape, and whether the root/body frame can be a geometry segment.
6. Coordinate with World #162 on the exact post-commit cut proof and with Observation #37 on passive transport limits. This document provides no substitute token or access rule.

## Reproduction anchors

At the pinned sources above, inspect:

- Embodiment `src/embodiment/physics3d/mechanics.py` (`SegmentSpec`, `JointSpec`, `JointTopology`);
- Embodiment `src/embodiment/physics3d/articulated_spec.py` (`articulated_body_spec_payload`, `articulated_body_spec_sha256`, `build_articulated_urdf`, `_segment_link_xml`);
- Embodiment `src/embodiment/physics3d/articulated_state.py` (`ActiveArticulatedMorphology`, `ArticulatedEmbodimentPhysicalState`, state/root/joint projection);
- Embodiment `src/embodiment/physics3d/observation_contract.py` and `src/embodiment/observation.py` (`BodyPoseSample`, `BodyPoseObservationProjection`);
- World `src/world/adapters/articulated_mujoco.py` (same-step `mj_forward`, root `data.xpos/xquat`, joint scalar output).

No runtime code, exported family, transport, registry status, or current publication behavior was modified.
