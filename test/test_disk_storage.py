import datetime
import mock
import json
import struct
import unittest

import dateutil.tz

from shoebox import disk_storage


class TestDiskStorage(unittest.TestCase):
    def setUp(self):
        self.handler = disk_storage.DatetimeEncoder()

    def test_handle_datetime_non_datetime(self):
        self.assertRaises(TypeError, self.handler.default, "text")

    def test_handle_datetime(self):
        now = datetime.datetime(day=1, month=2, year=2014,
                                hour=10, minute=11, second=12)
        self.assertEqual(1391249472000, self.handler.default(now))

    def test_handle_datetime_offset(self):
        now = datetime.datetime(day=1, month=2, year=2014,
                                hour=10, minute=11, second=12,
                                tzinfo=dateutil.tz.tzoffset(None, 4*60*60))
        self.assertEqual(1391235072000, self.handler.default(now))


class TestVersion0(unittest.TestCase):
    def setUp(self):
       self.v0 = disk_storage.Version0()

    def test_make_preamble(self):
       self.assertEqual(6, len(self.v0.make_preamble(99)))

    def test_load_preamble_bad_bor(self):
        file_handle = mock.Mock()
        file_handle.read.return_value = "abcdef"
        self.assertRaises(disk_storage.OutOfSync, self.v0.load_preamble,
                          file_handle)

    def test_load_preamble(self):
        file_handle = mock.Mock()
        file_handle.read.return_value = struct.pack("ih",
                          disk_storage.BOR_MAGIC_NUMBER, 99)
        self.assertEqual(99, self.v0.load_preamble(file_handle))


class TestVersion1(unittest.TestCase):
    def setUp(self):
       self.v1 = disk_storage.Version1()

    def test_no_metadata(self):
        metadata = {}
        payload = "shoebox"
        package = self.v1.pack(payload, metadata)
        self.assertEqual(4, len(package))
        self.assertEqual(12, len(package[1]))  # header
        self.assertEqual(4, len(package[2]))  # metadata
        self.assertEqual("\x00\x00\x00\x00", package[2])
        self.assertEqual(11, len(package[3]))  # payload 4+7

    def test_empty_payload(self):
        metadata = {"key": "value", "some": "stuff"}
        payload = ""
        package = self.v1.pack(payload, metadata)
        self.assertEqual(4, len(package))
        self.assertEqual(12, len(package[1]))  # header
        self.assertEqual(37, len(package[2]))  # metadata 4+(4*4)+3+5+4+5
        self.assertEqual(4, len(package[3]))  # payload 4+0
        self.assertEqual("\x00\x00\x00\x00", package[3])

    def test_unpack_happy_day(self):
        metadata = {"key": "value", "some": "stuff"}
        payload = {"shoebox": 1234}
        jpayload = json.dumps(payload)
        blocks = self.v1.pack(jpayload, metadata)
        blocks = blocks[1:]  # Remove preamble

        file_handle = mock.Mock()
        file_handle.read.side_effect = blocks

        m, p = self.v1.unpack(file_handle)
        self.assertEqual(metadata, m)
        self.assertEqual(payload, p)

    def test_unpack_bad_eor(self):
        metadata = {"key": "value", "some": "stuff"}
        payload = {"shoebox": 1234}
        jpayload = json.dumps(payload)
        blocks = self.v1.pack(jpayload, metadata)
        blocks = blocks[1:]  # Remove preamble

        # break the EOR marker
        print len(blocks[0])
        newblock = blocks[0][:8] + '\x00\x00\x01\x02'
        blocks = list(blocks)
        blocks[0] = newblock
        blocks = tuple(blocks)

        file_handle = mock.Mock()
        file_handle.read.side_effect = blocks

        self.assertRaises(disk_storage.OutOfSync, self.v1.unpack, file_handle)


class TestHelpers(unittest.TestCase):
    def test_get_version_handler_bad(self):
        self.assertRaises(disk_storage.InvalidVersion,
                          disk_storage.get_version_handler, 99)

    def test_get_version_handler(self):
        self.assertTrue(isinstance(disk_storage.get_version_handler(1),
                                   disk_storage.Version1))

        # Default version ...
        self.assertTrue(isinstance(disk_storage.get_version_handler(),
                                   disk_storage.Version1))


