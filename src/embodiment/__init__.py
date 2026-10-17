"""Physical/somatic state extraction candidate for Biopeia Embodiment."""

from .checkpoint import (
    EmbodimentAdoptionBindingV1,
    EmbodimentCheckpoint,
    ReserveStateObservationProjection,
    project_committed_reserve_state,
)
from .metabolism import MetabolicLedger, MetabolicSnapshot, ResourcePressure
from .physiology import (
    BodyStructureState,
    LivingBodyState,
    PhysiologyController,
    PhysiologySnapshot,
    VitalState,
)
from .physiology_config import DEFAULT_PHYSIOLOGY_CONFIG, PhysiologyConfig
from .intake import MaterialTransfer, absorb_material_transfer

__all__ = [
    "BodyStructureState",
    "EmbodimentCheckpoint",
    "EmbodimentAdoptionBindingV1",
    "DEFAULT_PHYSIOLOGY_CONFIG",
    "LivingBodyState",
    "MaterialTransfer",
    "MetabolicLedger",
    "MetabolicSnapshot",
    "PhysiologyConfig",
    "PhysiologyController",
    "PhysiologySnapshot",
    "ResourcePressure",
    "ReserveStateObservationProjection",
    "VitalState",
    "absorb_material_transfer",
    "project_committed_reserve_state",
]
