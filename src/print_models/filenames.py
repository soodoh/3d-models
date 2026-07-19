"""Safe filenames for models intended for Prusa CORE One+ workflows."""

from __future__ import annotations

import hashlib
import re

# Buddy firmware 6.6.2, released for the CORE One+, defines FILE_NAME_MAX_LEN
# as 160 + 1 + 5 + 1. The limit covers the complete filename, including its
# extension: https://github.com/prusa3d/Prusa-Firmware-Buddy/blob/v6.6.2/src/gui/file_list_defs.h
PRUSA_CORE_ONE_PLUS_MAX_FILENAME_LENGTH = 167

# Stock PrusaSlicer profiles derive the G-code name from the input stem and append
# print metadata. Reserve enough room for the longest stock CORE One+ form, such as
# "_0.25n_0.05mm_PETG_COREONE_1d23h59m.bgcode" (42 characters). The input
# extension is replaced, rather than retained, when PrusaSlicer creates that name.
# https://github.com/prusa3d/PrusaSlicer/blob/master/resources/profiles/PrusaResearch.ini
PRUSA_SLICER_MAX_OUTPUT_SUFFIX_LENGTH = 42
PRUSA_SLICER_INPUT_MAX_FILENAME_LENGTH = (
    PRUSA_CORE_ONE_PLUS_MAX_FILENAME_LENGTH
    - PRUSA_SLICER_MAX_OUTPUT_SUFFIX_LENGTH
    + len(".stl")
)
_TRUNCATION_HASH_LENGTH = 8


def output_filename(base_name: str, extension: str) -> str:
    """Return a sanitized filename with room for PrusaSlicer's print metadata."""
    normalized_extension = extension.removeprefix(".")
    if not normalized_extension:
        raise ValueError("A filename extension is required.")

    stem = sanitize_filename(base_name)
    suffix = f".{normalized_extension}"
    maximum_stem_length = PRUSA_SLICER_INPUT_MAX_FILENAME_LENGTH - len(suffix)
    if maximum_stem_length < _TRUNCATION_HASH_LENGTH + 3:
        raise ValueError(f"Filename extension is too long: {extension!r}")

    if len(stem) <= maximum_stem_length:
        return f"{stem}{suffix}"

    digest = hashlib.sha256(base_name.encode()).hexdigest()[:_TRUNCATION_HASH_LENGTH]
    marker = f"-{digest}-"
    retained_length = maximum_stem_length - len(marker)
    prefix_length = (retained_length + 1) // 2
    suffix_length = retained_length // 2
    retained_suffix = stem[-suffix_length:] if suffix_length else ""
    shortened_stem = f"{stem[:prefix_length]}{marker}{retained_suffix}"
    return f"{shortened_stem}{suffix}"


def sanitize_filename(value: str) -> str:
    """Replace characters that are unsafe in local, USB, and URL filenames."""
    return re.sub(r"[^A-Za-z0-9_.-]+", "_", value).strip("_") or "model"
