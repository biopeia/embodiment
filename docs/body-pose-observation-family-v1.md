# Embodiment BodyPose Semantic Family v1

## Status and scope

This is the Embodiment-owned semantic contract for the passive `BodyPose`
projection. It defines meaning only. It does not define an Observation wire
record, API, transport, persistence format, or delivery guarantee.

The family identity is `embodiment.body_pose`, semantic revision `v1`.
Changing its meaning, subject identity requirements, units, frame semantics,
authority, or epistemic interpretation is incompatible and requires a new
semantic revision. Additive metadata that does not alter interpretation may be
compatible, but must not be used to reinterpret v1 claims.

## Claim

One claim asserts the current adopted **base-body pose** owned by Embodiment.
Position and orientation are one structured value: splitting them into
independent claims would lose their common subject, owner state, and sampling
context. The claim does not assert velocity, calibration, physical accuracy,
or scientific validity.

The primary authority is Embodiment. The producer is the Embodiment owner
projection boundary; the semantic asserter is the Embodiment owner boundary.
The projection is based on `AUTHORITATIVE_STATE`, specifically the
`EmbodimentPhysicalState` accepted by Embodiment. Observation may represent
this claim but does not become its authority.

The acquisition basis is `embodiment_owner_state_projection`. This identifies
how the claim is obtained; it does not assert that the projection has already
been durably stored or published. The projection's own validation is required
to bind it to the adopted owner state.

## Subject, value, and frames

The typed subject is an Embodiment body in one episode and morphology revision.
All three identities are required:

```text
body_id
embodiment_episode_id
morphology_revision
```

The value is:

```text
position_m: 3 finite components, metres
orientation_xyzw: unit quaternion, component order x-y-z-w
```

For the current Physics3D producer, the quaternion maps vectors expressed in
`body_frame` into `reference_frame`, using the right-handed Hamilton
`q * (v, 0) * conjugate(q)` convention. This is the convention implemented by
the owner-side receptor frame transform. A future producer with another
convention must convert at its owner boundary or define an incompatible family
revision; consumers must not guess or silently reinterpret it. Frame identifiers
are explicit owner-provided names and are preserved verbatim; this contract
does not assert that two different frame identifiers are transform-compatible.

The reference frame and body frame must be explicit and preserved exactly.
There is no implicit global frame. A consumer may not replace frame identity
with a default or infer a transform that is absent from the source projection.
The existing Physics3D conformance declaration uses right-handed coordinates
with +z up; that does not make every possible frame name interchangeable.

## Time, revision, and applicability

This family declares no independent Embodiment clock. `world_id` and
`causal_tick` carried by the projection are correlation/context for World
commit validation; they are not renamed or presented as Embodiment domain
time. `physical_step_id` and its source tick likewise identify the physical
execution correlation, not a second semantic clock.

`morphology_revision` scopes structural applicability. The source projection
must remain bound to the adopted body/episode/morphology identities. A stale or
mismatched identity, frame, or physical-step correlation is rejected by the
owner boundary; consumers must not repair it.

## Acquisition and provenance

Acquisition basis is an Embodiment owner-state projection. Where the pose
resulted from a physical step, preserve the physical-step identity and source
correlation plus environment and solver-configuration revisions as provenance
context. Those revisions do not transfer Environment or solver authority to
Embodiment. Initial adopted state without a physical-step correlation remains
distinguishable from a pose adopted after a physical step.

For a physical-step result, the existing projection carries
`physical_step_id`, source World tick, Environment revision, solver
configuration revision, and the matching body/episode/morphology identities.
For an initial state it carries no fabricated physical-step provenance. This
family does not claim an Embodiment-owned time value: the World causal tick is
context only.

The projection returned by `EmbodimentPhysicalState.body_pose_observation_projection()`
also carries `source_state_sha256`, computed over the canonical Embodiment
checkpoint bytes for that exact owner state. Observation may retain it as a
source-state lineage reference. The projection dataclass validates digest
syntax and body identity, but it does not contain enough checkpoint state to
cryptographically verify an arbitrary caller-supplied digest or independently
bind episode/morphology identifiers. Therefore the owner method is the
authoritative producer; constructing the projection directly is not evidence
that its fields came from an adopted state. The digest identifies the bytes
used for the owner-produced projection; it does not prove that those bytes were
durably stored, that World committed them, or how an initial state was
scientifically generated. World must independently correlate the digest with
the owner checkpoint reference for a committed cut before publishing a
committed-cut claim. A missing or malformed digest is invalid. Initial states
have no physical-step lineage and must not be assigned a synthetic step
identity.

## Observation mapping boundary

An Observation-side adapter may map this family into the ratified
`SemanticObservation` model only while preserving the family identity and
revision, Embodiment authority, typed subject identities, atomic pose value,
units, explicit frames, applicability, and provenance. `world.causal_tick`
belongs in cross-authority context/correlation, not Embodiment domain time.
Missing owner facts are an error; the adapter must not synthesize them.

The adapter mapping and its negative cases remain downstream integration
evidence; this Embodiment contract and its local tests do not claim that the
Observation adapter already exists or that publication has occurred.

Embodiment does not depend on Observation. World must separately verify a
committed World cut before publication. Neither the owner projection nor this
contract proves that a cut committed or that an Observation was delivered.

## Limitations

This contract does not establish coordinate calibration, physical accuracy,
biological validity, global simultaneity, replay behavior, or transport
semantics. A successful adapter test establishes semantic preservation only
for the exact tested mapping and revisions.
