"""Model catalog used by the export CLI."""

from __future__ import annotations

from importlib import import_module
from types import ModuleType

MODEL_MODULES = (
    "print_models.models.dutch_blitz_storage_box",
    "print_models.models.five_crowns_storage_box",
    "print_models.models.gridfinity_exact_fit_baseplate",
)


def load_models() -> dict[str, ModuleType]:
    """Load all registered model modules by their public NAME."""
    models: dict[str, ModuleType] = {}

    for module_path in MODEL_MODULES:
        module = import_module(module_path)
        name = module.NAME
        models[name] = module

    return models
