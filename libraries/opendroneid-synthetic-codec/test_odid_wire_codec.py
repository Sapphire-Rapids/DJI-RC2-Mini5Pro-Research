"""Synthetic tests for the independently written OpenDroneID wire codec.

The encode reference vectors below were produced by compiling the public
OpenDroneID Core C library (``opendroneid-core-c``, Apache-2.0, Intel) and
running its official encoders on identical inputs. Every synthetic value is
``TEST*`` and uses no real identity or coordinate.
"""

from __future__ import annotations

import unittest

import odid_wire_codec as c


REFERENCE_VECTORS = {
    "basic": (
        c.encode_basic_id(
            c.BasicID(
                ua_type=c.UATYPE_HELICOPTER_OR_MULTIROTOR,
                id_type=c.IDTYPE_SERIAL_NUMBER,
                uas_id="TEST000000000000001",
            )
        ),
        "02125445535430303030303030303030303030303100000000",
    ),
    "location": (
        c.encode_location(
            c.Location(
                status=c.STATUS_AIRBORNE,
                direction=90.0,
                speed_horizontal=5.0,
                speed_vertical=-1.5,
                latitude=30.1234567,
                longitude=120.7654321,
                altitude_baro=101.5,
                altitude_geo=102.5,
                height_type=c.HEIGHT_REF_OVER_TAKEOFF,
                height=50.0,
                horiz_accuracy=12,
                vert_accuracy=6,
                baro_accuracy=6,
                speed_accuracy=3,
                ts_accuracy=1,
                timestamp=123.4,
            )
        ),
        "12205a14fd8779f411b157fb479b089d0834086c63d2040100",
    ),
    "self_id": (
        c.encode_self_id(c.SelfID(desc_type=c.DESC_TYPE_TEXT, desc="TEST SELF ID")),
        "3200544553542053454c462049440000000000000000000000",
    ),
    "system": (
        c.encode_system(
            c.System(
                operator_location_type=c.OPERATOR_LOCATION_TYPE_FIXED,
                classification_type=c.CLASSIFICATION_TYPE_EU,
                operator_latitude=31.0,
                operator_longitude=121.0,
                area_count=1,
                area_radius=30,
                area_ceiling=120.0,
                area_floor=0.0,
                category_eu=c.CATEGORY_EU_OPEN,
                class_eu=c.CLASS_EU_CLASS_0,
                operator_altitude_geo=5.0,
                timestamp=1700000000,
            )
        ),
        "420680397a1280221f48010003c008d00711da0700f1536500",
    ),
    "operator_id": (
        c.encode_operator_id(
            c.OperatorID(operator_id_type=c.OPERATOR_ID_TYPE_OPERATOR, operator_id="OPID0000000000000001")
        ),
        "52004f50494430303030303030303030303030303031000000",
    ),
}


class ReferenceVectorTests(unittest.TestCase):
    def test_encode_matches_reference(self):
        for name, (actual, expected) in REFERENCE_VECTORS.items():
            self.assertEqual(actual.hex(), expected, name)

    def test_every_message_is_25_bytes(self):
        for name, (actual, _) in REFERENCE_VECTORS.items():
            self.assertEqual(len(actual), c.MESSAGE_SIZE, name)


class RoundTripTests(unittest.TestCase):
    def test_basic_id_round_trip(self):
        msg = c.BasicID(uas_id="TEST1234567890123456", id_type=2, ua_type=2)
        decoded = c.decode_basic_id(c.encode_basic_id(msg))
        self.assertEqual(decoded.uas_id, msg.uas_id)
        self.assertEqual(decoded.id_type, msg.id_type)
        self.assertEqual(decoded.ua_type, msg.ua_type)

    def test_location_round_trip(self):
        msg = c.Location(
            status=c.STATUS_AIRBORNE,
            direction=275.0,
            speed_horizontal=12.25,
            speed_vertical=0.5,
            latitude=-33.8765432,
            longitude=151.2345678,
            altitude_baro=80.5,
            altitude_geo=85.75,
            height=45.0,
            horiz_accuracy=11,
            vert_accuracy=5,
            baro_accuracy=4,
            speed_accuracy=2,
            ts_accuracy=10,
            timestamp=3599.9,
        )
        decoded = c.decode_location(c.encode_location(msg))
        self.assertAlmostEqual(decoded.latitude, msg.latitude, places=6)
        self.assertAlmostEqual(decoded.longitude, msg.longitude, places=6)
        self.assertAlmostEqual(decoded.direction, msg.direction, places=0)
        self.assertAlmostEqual(decoded.speed_horizontal, msg.speed_horizontal, places=2)
        self.assertAlmostEqual(decoded.speed_vertical, msg.speed_vertical, places=1)
        self.assertAlmostEqual(decoded.altitude_baro, msg.altitude_baro, places=1)
        self.assertAlmostEqual(decoded.height, msg.height, places=1)
        self.assertEqual(decoded.status, msg.status)

    def test_system_round_trip(self):
        msg = c.System(
            operator_location_type=c.OPERATOR_LOCATION_TYPE_LIVE_GNSS,
            classification_type=c.CLASSIFICATION_TYPE_EU,
            operator_latitude=40.0,
            operator_longitude=-74.0,
            area_count=2,
            area_radius=100,
            area_ceiling=150.0,
            area_floor=0.0,
            category_eu=c.CATEGORY_EU_SPECIFIC,
            class_eu=c.CLASS_EU_CLASS_1,
            operator_altitude_geo=10.0,
            timestamp=1700000000,
        )
        decoded = c.decode_system(c.encode_system(msg))
        self.assertAlmostEqual(decoded.operator_latitude, msg.operator_latitude, places=6)
        self.assertEqual(decoded.area_radius, msg.area_radius)
        self.assertEqual(decoded.area_ceiling, msg.area_ceiling)
        self.assertEqual(decoded.category_eu, msg.category_eu)
        self.assertEqual(decoded.class_eu, msg.class_eu)

    def test_auth_round_trip(self):
        msg = c.Auth(
            data_page=0,
            auth_type=c.AUTH_NONE,
            last_page_index=0,
            length=4,
            timestamp=1234,
            auth_data=b"\x01\x02\x03\x04",
        )
        decoded = c.decode_auth(c.encode_auth(msg))
        self.assertEqual(decoded.data_page, 0)
        self.assertEqual(decoded.auth_type, msg.auth_type)
        self.assertEqual(decoded.auth_data[: msg.length], msg.auth_data)


class PackTests(unittest.TestCase):
    def test_pack_round_trip(self):
        msgs = [REFERENCE_VECTORS["basic"][0], REFERENCE_VECTORS["location"][0]]
        packed = c.encode_pack(msgs)
        unpacked = c.decode_pack(packed)
        self.assertEqual(unpacked, msgs)
        self.assertEqual(len(packed), 3 + 2 * c.MESSAGE_SIZE)

    def test_pack_rejects_too_many(self):
        msgs = [REFERENCE_VECTORS["basic"][0]] * (c.PACK_MAX_MESSAGES + 1)
        with self.assertRaises(c.CodecError):
            c.encode_pack(msgs)

    def test_decode_message_dispatch(self):
        raw = REFERENCE_VECTORS["location"][0]
        msg_type, obj = c.decode_message(raw)
        self.assertEqual(msg_type, c.MSG_LOCATION)
        self.assertIsInstance(obj, c.Location)


class ErrorTests(unittest.TestCase):
    def test_rejects_wrong_size(self):
        with self.assertRaises(c.CodecError):
            c.decode_basic_id(b"\x00" * 24)

    def test_rejects_wrong_message_type(self):
        with self.assertRaises(c.CodecError):
            c.decode_location(REFERENCE_VECTORS["basic"][0])

    def test_rejects_oversize_id(self):
        with self.assertRaises(c.CodecError):
            c.encode_basic_id(c.BasicID(uas_id="X" * (c.ID_SIZE + 1)))


if __name__ == "__main__":
    unittest.main()
