"""Model catalog used by the export CLI."""

from __future__ import annotations

from importlib import import_module
from types import ModuleType

MODEL_MODULES = (
    "print_models.models.dutch_blitz_storage_box",
    "print_models.models.five_crowns_storage_box",
    "print_models.models.monopoly_deal_storage_box",
    "print_models.models.ratchet_toothpaste_tube_squeezer",
    "print_models.models.platypus_quickdraw_backflush_adapter",
    "print_models.models.gridfinity_box",
    "print_models.models.gridfinity_cup_holder",
    "print_models.models.gridfinity_whiskey_snifter",
    "print_models.models.gridfinity_small_snifter",
    "print_models.models.gridfinity_double_jigger",
    "print_models.models.gridfinity_tea_cup",
    "print_models.models.gridfinity_shot_glass",
    "print_models.models.gridfinity_exact_fit_baseplate",
    "print_models.models.gridfinity_shims",
)


def load_models() -> dict[str, ModuleType]:
    """Load all registered model modules by their public NAME."""
    models: dict[str, ModuleType] = {}

    for module_path in MODEL_MODULES:
        module = import_module(module_path)
        name = module.NAME
        models[name] = module

    return models
