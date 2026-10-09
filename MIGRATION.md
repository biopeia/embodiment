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

## Known rewrites

- `physiology_config.py` excludes unused `prospective_*` parameters for Organism deliberation; no other physiology semantics were changed.
- Python distribution/import name is `embodiment`; no `biopeia_*` prefix is used.
- This package is an extraction candidate only; no CURRENT/TARGET compliance is implied.
- The copied `LivingBodyState` uses the CURRENT enum label `VitalState.DEAD`; this extraction does not reinterpret it as TARGET `ORGANISM_DEATH`. Applicability is bounded to body-state code and requires later contract mapping.

## Validation

Build/install/test results are recorded in the migration PR/check run. No
scientific assets or historical checkpoints were copied.
