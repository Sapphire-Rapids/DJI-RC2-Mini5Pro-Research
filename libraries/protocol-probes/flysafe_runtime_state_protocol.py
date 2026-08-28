"""Pure, fail-closed decoders for DJI FlySafe runtime capability pushes.

The field layouts in this module were recovered from DJI Fly 1.21.10's
``libflightrestrictcore.so`` and cross-checked against DJI MSDK 5.18.  This
module has no transport dependency and intentionally contains no request or
write builder.
"""

from __future__ import annotations

from dataclasses import dataclass


CMD_TYPE_PUSH_PLAINTEXT = 0x00
CMD_SET_FLIGHT_CONTROLLER = 0x03
CMD_ID_AREA_INFO = 0x09
CMD_ID_WHITE_LIST_INFO = 0x42

MINI_5_PRO_PRODUCT = 139
# Current DJI Fly 1.21.10 first looks up the product in a 21-item tree.  A
# lookup miss selects 0x92.  Products found in the tree also select 0x92
# unless they are in this exact nine-item retain set.  In particular, product
# 139 is a lookup miss and therefore uses 0x92 for all supported versions.
PRODUCTS_RETAINING_VERSION_SESSION_RECEIVER = frozenset(
    {59, 67, 73, 75, 76, 96, 112, 113, 127}
)


class FlySafeStateError(ValueError):
    """A runtime state cannot be interpreted without guessing."""


@dataclass(frozen=True)
class WhiteListSupportUpdate:
    usable: bool
    supported: bool | None
    encoding: str


def decode_area_unlock_version(payload: bytes) -> int:
    """Decode the cached unlock protocol version from MC Area Info.

    The current DJI implementation requires at least eight payload bytes and
    reads the upper two bits of the little-endian word at offsets 3..4.
    Values 0, 1, and 2 select V2, V3, and V4; raw value 3 is unknown (255).
    """

    if len(payload) < 8:
        raise FlySafeStateError("area-info payload is shorter than 8 bytes")
    raw = int.from_bytes(payload[3:5], "little") >> 14
    return raw if raw in (0, 1, 2) else 255


def decode_whitelist_support(payload: bytes) -> WhiteListSupportUpdate:
    """Decode an MC WhiteList Info support update.

    Short legacy-form payloads with a first byte below 10 do not update DJI's
    cache, so they are returned as unusable rather than being treated as
    ``False``.
    """

    if not payload:
        raise FlySafeStateError("white-list payload is empty")
    first = payload[0]
    if first >= 10:
        return WhiteListSupportUpdate(
            usable=True,
            supported=first != 0xFF,
            encoding="version_byte",
        )
    if len(payload) >= 28:
        return WhiteListSupportUpdate(
            usable=True,
            supported=payload[3] != 0,
            encoding="legacy_flag",
        )
    return WhiteListSupportUpdate(
        usable=False,
        supported=None,
        encoding="short_legacy_no_update",
    )


def select_inventory_receiver(*, unlock_version: int, product: int) -> int:
    """Select the one receiver used by DJI's type-6 inventory read path."""

    if unlock_version not in (0, 1, 2):
        raise FlySafeStateError("unlock protocol version is unknown")
    receiver = 0xB1 if unlock_version == 2 else 0x03
    if product not in PRODUCTS_RETAINING_VERSION_SESSION_RECEIVER:
        receiver = 0x92
    return receiver
