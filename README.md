# Embodiment

Copy-first Biopeia extraction candidate for physical/somatic body state. This
repository is a migration rehearsal, not a declaration that the extracted code
already satisfies the ratified TARGET contracts.

The first slice contains the current physical physiology and body-backed
metabolic accounting modules. It intentionally does not include the mixed
`Body` actuator/receptor aggregate, Organism-longitudinal embodiment learning,
or Lab/Physics3D runtime composition.

## Development

```sh
python -m pip install -e '.[dev]'
python -m pytest
```

Python package and distribution name: `embodiment`.
