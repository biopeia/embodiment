# Somatic Dynamics Evidence Plan v1

**Status:** Proposed evidence programme; not a frozen experimental protocol  
**Owner:** Biopeia Embodiment  
**Issue:** [embodiment#20](https://github.com/biopeia/embodiment/issues/20)  
**Design basis:** Architecture Owner directions recorded in issue #20 on 2026-10-10  
**Repository base reviewed:** `biopeia/embodiment` `597cc4a09f4a5c94095b17ad0f2ba510df6d02c3`  
**Lab custody reference reviewed:** `biopeia/lab` `698988366cd6a985c970f5a0fb71a11a23f8d665`  

## 1. Purpose and boundary

This document proposes a staged programme for obtaining evidence needed before Biopeia implements quantitative Embodiment-owned somatic dynamics. It is a design deliverable for scientific review, not authorization to run a campaign, admit historical evidence, or implement physiological equations.

The programme separates these quantities and claims:

```text
mechanical_work_joules = physical evidence, with Embodiment as semantic owner
somatic_resource       = Body-owned modeled state in a declared quantity
mechanical_work_joules != somatic_resource expenditure
```

No automatic conversion from mechanical work to resource expenditure is proposed. The programme does not define a basal debit, energy yield, damage threshold, recovery rate, senescence rate, or viability threshold. It does not reinstate the dropped `SomaticCycle` or `somatic_reference_duration_s`, and does not treat historical defaults, formulas, labels, or results as TARGET laws.

The work is divided into sequential evidence stages:

```text
A. Validate mechanical-work measurement independently of physiology.
B. Characterize resource acquisition, storage, and controlled depletion.
C. Investigate damage production under controlled physical stress.
D. Investigate repair/removal separately from new damage.
E. Investigate viability only after A–D have bounded inputs and endpoints.
```

Senescence is a later hypothesis, not an assumed first-order counter. It is outside the first execution programme until evidence supports a distinct, measurable longitudinal question.

## 2. Evidence classes and current gaps

### 2.1 Current Biopeia implementation is not scientific validation

At the reviewed Embodiment base, somatic state and accounting implementation exists in files including:

- `src/embodiment/physiology.py`;
- `src/embodiment/metabolism.py`;
- `src/embodiment/physiology_config.py`.

These are implementation facts, not evidence that their quantities, rates, category names, thresholds, or transitions correspond to a validated physical or biological process. Their presence does not authorize use as an empirical oracle. In particular, generic accounting balances and model-valued floats must not be relabelled as joules, material quantity, or measured damage without an explicit contract and measurement basis.

`MIGRATION.md` records the historical body-local cycle and its focused tests as `DROP`, while retaining the requirement for new somatic dynamics. This plan respects that disposition and proposes no compatibility path.

### 2.2 Historical Lab records are navigational evidence only

The Lab main revision reviewed for this plan is `698988366cd6a985c970f5a0fb71a11a23f8d665`. In its migration inventory, the following source records remain `DEFER` rather than admitted evidence:

- `lab/experiments/embodiment/somatic-correlation-trap/{README.md,experiment.toml,results.json}`;
- `lab/research/studies/embodiment/e5-somatic-correlation-trap-negative.md`;
- `lab/experiments/learning/metabolic-retention-price-calibration-v1/{README.md,experiment.toml}`;
- `lab/experiments/world/genesis-viability-characterization/{README.md,experiment.toml,results.json}`.

The Lab study-evidence map records candidate paths for the somatic-correlation and viability studies as heuristic, not content-validated links. The focused evidence audit attached to [embodiment#20](https://github.com/biopeia/embodiment/issues/20#issuecomment-6087025450) concluded only that the reviewed candidates did not establish quantitative work-to-resource conversion, calibrated damage/recovery, senescence, or viability thresholds; it explicitly did not prove that no relevant artifact exists elsewhere.

Accordingly:

- this plan does not classify or dispose of any Lab artifact;
- it does not assert the validity, reproducibility, or scientific value of historical records;
- it does not claim equivalence to any historical method;
- any evidence later used must be assessed under Lab custody with exact provenance and an independent scientific review.

## 3. Cross-stage design controls

### 3.1 Authority and causal context

| Information/state | Semantic owner | Programme responsibility |
|---|---|---|
| External material, loading scene, or environmental condition | Environment | Declare identity, revision, frame, units, and the controlled input/condition. |
| Body identity, morphology, somatic state, receptor/effector binding where relevant | Embodiment | Validate applicability and adopt only Embodiment-owned state. |
| Shared causal ordering and committed cut | World | Correlate participants and commit; do not define physiological meaning or adopt owner state. |
| Numerical integration | Physical solver capability | Produce candidate physical results; it is not an authority. |
| Protocol, apparatus record, evidence custody, analysis and provenance | Lab | Own the scientific protocol/evidence record; custody does not itself validate a claim. |

Every future run must correlate the applicable `world_id`, committed causal tick/cut, physical-step identity, body identity, embodiment episode, morphology revision, Environment revision, solver/configuration revision, and the relevant Embodiment transition/checkpoint reference. A result from a stale body or morphology revision is not evidence for the current body.

### 3.2 Keep time bases distinct

| Time basis | Meaning in this programme | Allowed use |
|---|---|---|
| World causal tick/cut | Shared committed causal ordering | Correlate an owner transition with the World process; not a physical duration. |
| Organism longitudinal progression (`organism_step`) | Organism-owned progression | Correlate cognition/agency where a study needs it; not body age or solver duration. |
| Embodiment/somatic progression | Body-owned ordered state transition progression, when an explicit contract provides it | Index somatic state transitions; never infer elapsed SI seconds from a count. |
| Physical solver time | Explicit integration interval/substep duration | Use in mechanical integration only when its unit and relation to the physical step are declared. |
| Host wall clock | Collection/performance metadata | Never use as implicit biological or causal time. |

The protocol must record the mapping actually used between solver intervals and World causal cuts. It must not assume one tick equals one second or one Organism step.

### 3.3 Units, ranges, and measurement rules

- Every physical value crossing a protocol boundary has an explicit unit, frame, range, and measurement source.
- SI units are used for the Stage A mechanical quantities: torque in `N·m`, angular velocity in `rad/s`, duration in `s`, and work in `J`. Angular radians are dimensionless in SI dimensional analysis.
- Resource quantities use an explicitly declared material unit where known, or a specifically declared dimensionless/model unit. A model unit is not energy and is not silently convertible to joules.
- Stress and damage protocols declare one loading mode and its measurement basis. Force, moment, pressure, strain, displacement, and damage are not interchangeable measures.
- No value is silently clipped or imputed. Missing, unavailable, stale, or invalid measurement is reported as such, not as zero or neutral.
- Instrument calibration, uncertainty, resolution, reference frame, and raw observations are preserved with the result.

### 3.4 Experimental regime and review

The proposed programme begins with apparatus/mechanics validation and exploratory characterization. Each confirmatory or held-out claim requires its own protocol frozen before outcome inspection, including exact population/body scope, arms, independent and dependent variables, controls, seed strategy, horizon, exclusions, validity rules, analysis, and decision criteria. This plan intentionally supplies no arbitrary sample size, seed set, duration, or numerical threshold.

Before any claim is accepted:

1. an independent Advisor reviews the actual protocol, analysis, results, and primary evidence;
2. the Lab owner accepts or rejects the scientific interpretation and its admissibility;
3. Architecture Owner review is added if the claim changes a constitutional boundary;
4. negative, null, inconclusive, `NOT_TESTABLE`, invalid, and deviating runs are preserved distinctly.

CI or a deterministic software test can validate apparatus mechanics only; it cannot prove a physiological effect.

## 4. Staged evidence programme

### Stage A — Mechanical-work measurement, independent of physiology

**Question.** Does the physical measurement path produce a correctly unit-bound and reproducible mechanical-work quantity for the tested body/joint and solver configuration?

| Requirement | Proposed design |
|---|---|
| Independent variable(s) | A declared torque input/trajectory and a declared angular-velocity trajectory or controlled physical loading condition. One protocol must define which quantities are commanded and which are independently measured. |
| Measured variable(s) | Raw torque, angular velocity, physical interval, and the resulting signed work estimate (W = \int \tau(t)\,\omega(t)\,dt\) over the declared scope. If a different work aggregate is later needed, define it explicitly rather than silently substituting absolute/positive work. |
| Domain owner(s) | Embodiment owns the semantic body-work quantity and validates/adopts it. The solver is a numerical executor that emits candidate measurements. World correlates the physical step and committed cut. Lab owns apparatus calibration and evidence records. |
| Time basis | Solver substep duration in seconds, correlated to one physical-step context and World causal cut. Do not substitute World ticks, Organism steps, or host clock for `dt`. |
| Units/frame | Torque `N·m`; angular velocity `rad/s`; interval `s`; work `J`. Bind torque and angular velocity to the same stable joint/axis, body, episode, morphology revision, and declared frame/convention. |
| Method | First verify the numerical integration against an independently defined analytical/reference trace; then, if a physical apparatus is used, compare the solver/owner result against calibrated measurement with uncertainty. Include variable trajectories and explicit timestep refinement in the declared domain. Keep numerical conformance separate from physical calibration. |
| Controls/baselines | Zero-torque control; sign-reversal control where the apparatus permits; matched initial body/configuration; independent reference instrument/analytic oracle; solver timestep refinement. Each is a mechanics control, not a physiological arm. |
| Required evidence | Raw torque/velocity/time series; integration and sign convention; reference and calibration records; solver/config revisions; body/morphology identities; uncertainty/error budget; test protocol and all deviations. |
| Accept/reject criterion | Accept only a bounded measurement method whose output agrees with the preregistered independent reference within a predeclared instrument/numerical uncertainty across the stated domain. Reject the method for that domain if systematic discrepancies exceed the declared error budget. If calibration/reference is unavailable or the domain is not covered, mark `NOT_TESTABLE`/inconclusive. This stage makes no claim about metabolic expenditure. |

### Stage B — Resource acquisition, storage, and controlled depletion

**Question.** Can an externally controlled quantity be acquired, represented in Body-owned state, retained, and explicitly withdrawn/accounted for with provenance, without treating it as energy expenditure?

| Requirement | Proposed design |
|---|---|
| Independent variable(s) | Declared amount made available by Environment; accessibility/transfer condition; where needed, an explicit controlled withdrawal. Vary one factor at a time or use a preregistered factorial design. Do not call spontaneous state change “metabolism” until its mechanism is separately specified. |
| Measured variable(s) | Environment source amount before/after; amount presented/transferred; amount accepted by Embodiment; Body-owned stored quantity before/after; unaccepted/remaining quantity; explicitly withdrawn amount. Any unexplained residual is reported, not assigned to a hidden cost. |
| Domain owner(s) | Environment owns external source state and availability. Embodiment owns accepted Body storage and its transition. World correlates/commits the causal transfer. Lab controls and records apparatus/protocol. |
| Time basis | Transfer is attached to a World causal cut and Environment revision. Storage/withdrawal changes occur only through explicit Embodiment-owned transitions. If retention over progression is tested, declare the Embodiment progression and protocol horizon separately from physical seconds. |
| Units/frame | Declare material identity/composition and an amount unit from the source contract; use a traceable physical unit when the quantity supports one. Otherwise declare a named dimensionless/model amount unit. Never call the amount joules or infer energy from it. |
| Method | Establish measurement repeatability; compare controlled offered input with owner-accepted storage; separately test no-input retention and explicit withdrawal. If transformations or losses are hypothesized, make each an explicit measured term in a later protocol rather than using an unexplained balance residual. |
| Controls/baselines | No-input/sham transfer; matched initial Body state and capacity; source amount measured before and after; same morphology/configuration; matched observation interval. Include a transfer apparatus control independent of Body dynamics. |
| Required evidence | Source and Body identity/revisions; material/amount schema and units; raw source and Body-state records; transfer/adoption references; calibration/uncertainty; baseline/control results; all rejected/unavailable transfers. |
| Accept/reject criterion | Accept only a bounded acquisition/storage/withdrawal accounting relation if the manipulated amount is independently measured, the owner transition is reproducible, and any balance residual is within declared measurement uncertainty or explained by a separately measured process. Reject the proposed relation if reproducible unexplained discrepancies remain. This does not establish nutritional value, energy yield, or a conversion to mechanical work. |

### Stage C — Damage production under controlled physical stress

**Question.** Under a defined body and tested loading regime, does a controlled physical stress cause a reproducible change in an independently interpretable damage/structural endpoint, separately from resource reserve?

| Requirement | Proposed design |
|---|---|
| Independent variable(s) | One defined loading mode and a declared stress/dose measurement (for example force, moment, pressure, strain, or another justified physical quantity). The choice belongs to the scientific question and apparatus; this plan selects none as universal. |
| Measured variable(s) | Raw applied/experienced load; an independently measured structural or damage endpoint; corresponding Embodiment candidate/adopted state; resource reserve as a controlled covariate rather than the damage outcome. An existing `damage: float` is not a calibrated outcome by itself. |
| Domain owner(s) | Environment owns externally imposed environmental conditions; Embodiment owns body structure and adopted damage state; solver supplies candidate mechanics only; World commits the correlated transition; Lab owns protocol and measurements. |
| Time basis | Physical load trace uses declared SI duration/substeps. State observations are correlated to committed World cuts and explicit Embodiment progression. Do not infer a damage rate from wall-clock time. |
| Units/frame | Declare the selected load unit and frame; for example force `N`, moment `N·m`, pressure `Pa`, or dimensionless strain, only when that is the protocol's measured variable. Define the endpoint's unit, range, resolution, and calibration before execution. |
| Method | Compare preregistered stress exposures with matched sham/no-stress controls while holding morphology, initial state, and resource condition matched. Measure the damage endpoint independently of the state update being tested. Repeat only within a preregistered dose range and analysis plan. |
| Controls/baselines | Sham/no-stress; matched initial body/morphology revision; matched resource reserve; apparatus-only reference; no simultaneous repair condition unless it is an explicit arm. |
| Required evidence | Calibrated load traces; independent structural endpoint and uncertainty; Body state before/after; physical/causal correlation IDs; initial condition; randomization/control record; owner adoption decision; protocol deviations. |
| Accept/reject criterion | Accept a damage-production relation only for the tested body/configuration/load domain if the preregistered contrast is reproduced on the independent endpoint, the matched controls exclude the specified alternatives, and the effect survives independent review. Reject that bounded model if a valid, adequately discriminating preregistered test contradicts it. Otherwise report inconclusive or not testable. Do not infer a universal damage law, damage threshold, or energy cost. |

### Stage D — Repair/removal separately from new damage

**Question.** Does a specifically declared repair/removal opportunity change an independently measured damage/structure endpoint when no new damaging stress is applied, and is the change distinguishable from measurement drift or reversible functional performance?

| Requirement | Proposed design |
|---|---|
| Independent variable(s) | A defined repair/removal condition versus matched no-repair/sham condition. Resource availability may be studied as a separately declared factor; it must not be bundled into “repair” without a mechanism. |
| Measured variable(s) | Independent damage/structural endpoint before and after; direct function/structural measures as separate outcomes; resource amount and transfers when manipulated. A performance rebound alone does not demonstrate damage removal. |
| Domain owner(s) | Embodiment owns body structural state and adopts any repair candidate. Environment owns controlled external repair conditions/resources. World supplies causal ordering/commit. Lab owns study and apparatus record. |
| Time basis | Observe over declared Embodiment progression; record any physical intervals in SI seconds if relevant. World cuts correlate transitions. Do not use a fixed host-second duration as a biological recovery constant. |
| Units/frame | Reuse the validated Stage C endpoint and its units/calibration. Declare units and ranges for any repair resource or intervention. No repair-rate unit is assigned before a mechanism and time basis are specified. |
| Method | After a defined initial damage condition, compare repair-opportunity and matched no-repair arms with no new damaging load during the observation window. Validate endpoint repeatability before interpreting change. If necessary, use an independent structural measure to distinguish true removal from reversible deformation or function restoration. |
| Controls/baselines | No-repair/sham; no-new-stress control; matched initial damage and morphology; resource-matched controls if resources are not the intervention; repeated measurement of an unchanging reference to quantify drift. |
| Required evidence | Stage C endpoint validity; intervention identity/configuration; initial/body state and revision; independent before/after measurements; any resource inputs; owner adoption/candidate record; causal cut and explicit horizon; deviations. |
| Accept/reject criterion | Accept a bounded repair/removal relation only if the endpoint changes reproducibly in the repair arm relative to controls, is distinguishable from measurement drift and new-stress differences, and is supported by independent review. Reject the tested relation if a valid preregistered test contradicts it. If only function changes or the endpoint is not independently interpretable, the damage-removal claim is not supported. Do not infer a universal repair rate or resource conversion. |

### Stage E — Viability, only after A–D

**Entry gate.** Stages A–D must have valid bounded measurement/state relations sufficient to formulate a non-circular viability question. The current proposal cannot define or implement a viability threshold.

| Requirement | Proposed design |
|---|---|
| Independent variable(s) | Preregistered combinations/trajectories of previously characterized Body-owned states, such as measured resource availability and damage/repair history. Select only factors that earlier evidence supports and that the question can manipulate ethically and reproducibly within the simulator. |
| Measured variable(s) | A predeclared, independently observable Embodiment endpoint for continued body function/state transition and recovery, plus the relevant prior-stage state measurements. First define what observation would count as viability/non-viability without using the candidate threshold under test as its own oracle. |
| Domain owner(s) | Embodiment owns body viability semantics/state if and when an evidence-backed contract exists. World owns presence/lifecycle coordination, not body viability. Organism lifecycle remains distinct and cannot be inferred from body viability or World presence. Lab owns protocol and evidence custody. |
| Time basis | Explicit Embodiment progression and World causal cuts; any physical durations use SI units. Define follow-up horizon before execution. Neither host time nor Organism step is a proxy for somatic age. |
| Units/frame | State variables retain their validated prior-stage units. The endpoint may be categorical only after an operational definition and testability criteria are frozen; no numerical viability threshold is presently specified or authorized. |
| Method | First validate the endpoint against independent observations and recovery/continuation cases. Then run a preregistered, controlled study across previously characterized state combinations, preserving valid, not-testable, invalid, and contradictory outcomes. Require an independent held-out confirmation before generalizing beyond tested bodies/configurations. |
| Controls/baselines | Continued-function controls; reversible/recovery cases; matched initial state and morphology; protocol-valid boundary cases; negative controls demonstrating that body damage/viability is not being substituted for Organism death or presence termination. |
| Required evidence | Valid prior A–D evidence; independent endpoint definition and calibration; state/identity/revision provenance; preregistration; run and stopping records; false-positive/false-negative analysis or equivalent declared uncertainty; independent Advisor and Lab-owner review. |
| Accept/reject criterion | No viability model is accepted until the endpoint is independently defined, can distinguish the preregistered competing outcomes, is reproducible, and survives confirmatory/held-out review within its declared scope. Reject a proposed model if valid held-out evidence contradicts its prediction. If the endpoint is circular, not observable, or confounded with Organism/World lifecycle, the study is not testable and no threshold or transition may be implemented. |

## 5. Senescence as a later, separate hypothesis

Senescence is not part of Stages A–E as an assumed transition. A future longitudinal proposal may ask whether a distinct senescence process exists, but it must:

- specify an observable endpoint distinct from accumulated damage, resource state, and viability;
- distinguish time/progression exposure from damage/repair history and other candidate causes;
- declare its Body population, morphology/configuration, domain-time basis, and follow-up horizon;
- avoid reusing historical `age_ticks`, `senescence_rate`, or `somatic_reference_duration_s` as TARGET semantics;
- remain exploratory until an independently reviewed protocol supports a narrower confirmatory question.

The absence of an observed senescence effect is a valid result; a clock-driven counter is not a default.

## 6. Required protocol deliverable before any campaign

This programme becomes executable only through one or more bounded Lab protocols. Each protocol must identify:

1. scientific question and regime (`EXPLORATORY`, `CONFIRMATORY`, or `HELD-OUT`);
2. exact body/episode/morphology, Environment, solver, and software revisions;
3. supported source/target authority for every variable;
4. independent/dependent variables and operational measurement definitions;
5. units, calibration, uncertainty, reference frame, and missing-data handling;
6. arms, controls, randomization/seed policy, horizon, and stopping rules;
7. preregistered analysis and acceptance/rejection/inconclusive criteria;
8. evidence artifacts, source revisions, content hashes, custody, and retention;
9. candidate/owner adoption, checkpoint and World causal-cut references;
10. required independent Advisor review and Lab-owner scientific acceptance.

No sample count, threshold, effect size, or parameter value is fixed by this document. Those belong to the specific question and must be justified and frozen before confirmatory/held-out outcome inspection.

## 7. Explicit non-claims

This plan does not establish:

- that mechanical work is a physiological cost;
- that any resource amount is biological energy;
- that current Body damage, integrity, reserve, fatigue, senescence, or viability fields are calibrated measurements;
- that historical protocols/results are scientifically valid, reproducible, admissible, or equivalent to a TARGET method;
- a universal material-to-resource or work-to-resource conversion;
- a damage, repair, viability, death, or senescence law;
- that Organism death follows Body death or presence termination;
- that any campaign has been run.

Until a protocol is separately specified and reviewed, unsupported relationships remain absent from TARGET implementation rather than being filled by defaults.
