# Embodiment

Copy-first Biopeia extraction candidate for physical/somatic body state. This
repository is a migration rehearsal, not a declaration that the extracted code
already satisfies the ratified TARGET contracts.

The first slice contains the current physical physiology and body-backed
metabolic accounting modules. It intentionally does not include the mixed
`Body` actuator/receptor aggregate, Organism-longitudinal embodiment learning,
or Lab/Physics3D runtime composition.

The follow-up mechanics slice contains immutable Physics3D value contracts and
physical parameter constants only. It does not include a solver or claim that
the Physics3D runtime is owned by Embodiment as a whole.

## Development

```sh
python -m pip install -e '.[dev]'
python -m pytest
```

Python package and distribution name: `embodiment`.
