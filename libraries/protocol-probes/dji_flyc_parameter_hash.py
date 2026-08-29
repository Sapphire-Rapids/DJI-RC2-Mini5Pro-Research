"""Independently written DJI flight-controller parameter-name hash.

DJI flight controllers address parameters by a 32-bit hash of the parameter
name rather than by the name itself. This module re-implements the public
algorithm recovered in ``o-gs/dji-firmware-tools``
(``comm_mkdupc.flyc_parameter_compute_hash``, pinned at commit
``195692263c2684cf1ddc4995f2736be6c0fb135e``) from its published behaviour, not
from DJI code:

- encode the parameter name as GBK;
- start ``hash = 0``;
- for each encoded byte ``b``:
  ``hash = (((hash & 0xFFFFFFFF) << 8) + b) % 0xFFFFFFFB``.

Every current flight-controller parameter name is a plain ASCII identifier, for
which GBK and byte-wise iteration coincide. The pinned vectors are therefore
all ASCII; the non-ASCII GBK path is deliberately not asserted here because the
public prior-art loop is byte-ambiguous for multi-byte names and no such name is
reachable on the current products.

The result is the 4-byte little-endian value carried by the by-hash FLYC
parameter commands (``0x03/0xF7`` metadata, ``0x03/0xF8`` read, ``0x03/0xF9``
write). It is a pure function with no I/O and no device effect.

This module is intentionally source-only. It does not bundle, derive from, or
redistribute DJI software; the algorithm is reproduced from the public
prior-art description and pinned to fixed regression vectors below.
"""

from __future__ import annotations

_MODULUS = 0xFFFFFFFB

# Regression vectors cross-checked against the public prior-art implementation.
# Each vector is ``(name, expected_hash)``. They pin the current RID policy
# parameters, the by-index wa150 EU C0 rows, and the known-good positive-control
# parameters (all ASCII names).
REGRESSION_VECTORS: tuple[tuple[str, int], ...] = (
    ("rid_ctrl_enable_0", 0x3CBD864F),
    ("ccc_broadcast_signal_quality_0", 0xD7757AD2),
    ("EU_CE_enable_c0_rid_0", 0xF80992FE),
    ("EU_CE_enable_c0_rid", 0xA3F6F806),
    ("EU_CE_Reg_RID_Enable", 0xF486A2BE),
    ("eu_ce_support_remote_set_level", 0x9BC5A8E6),
    ("g_config.flying_limit.max_height", 0xF412036C),
    ("g_config.flying_limit.max_height_0", 0x0371238A),
    ("g_config.flying_limit.max_radius_0", 0x425C0A94),
    ("g_config.advanced_function.radius_limit_enabled_0", 0x7ECE6D19),
)


def dji_flyc_parameter_hash(name: str) -> int:
    """Return the 32-bit FLYC parameter hash for ``name``.

    The name is encoded as GBK to match DJI's wire behaviour; for the ASCII
    parameter names in use this is byte-for-byte identical to the original
    encoding. The function performs no I/O and never sends a name anywhere.
    """

    if not isinstance(name, str):
        raise TypeError("parameter name must be a string")
    if not name:
        raise ValueError("parameter name must not be empty")

    parameter_hash = 0
    for byte in name.encode("gbk"):
        parameter_hash = (
            ((parameter_hash & 0xFFFFFFFF) << 8) + byte
        ) % _MODULUS
    return parameter_hash


def dji_flyc_parameter_hash_le(name: str) -> bytes:
    """Return the 4-byte little-endian wire form of the parameter hash."""

    return dji_flyc_parameter_hash(name).to_bytes(4, "little")


def load_dji_flyc_parameter_hash_module(
    *,
    module_name: str = "dji_flyc_parameter_hash",
    path: str | None = None,
):
    """Load this file as a standalone module for callers outside this package.

    The by-index and by-hash probes live in different directories, so they load
    this single source file through ``importlib`` with a caller-chosen module
    name instead of relying on package import paths.
    """

    import importlib.util
    from pathlib import Path

    resolved = Path(path) if path else Path(__file__).resolve()
    spec = importlib.util.spec_from_file_location(module_name, resolved)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {resolved}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module
