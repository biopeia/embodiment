"""Physical/somatic state extraction candidate for Biopeia Embodiment."""

from .checkpoint import EmbodimentCheckpoint
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
from .somatic_cycle import SomaticCycle

__all__ = [
    "BodyStructureState",
    "EmbodimentCheckpoint",
    "DEFAULT_PHYSIOLOGY_CONFIG",
    "LivingBodyState",
    "MaterialTransfer",
    "MetabolicLedger",
    "MetabolicSnapshot",
    "PhysiologyConfig",
    "PhysiologyController",
    "PhysiologySnapshot",
    "ResourcePressure",
    "SomaticCycle",
    "VitalState",
    "absorb_material_transfer",
]
