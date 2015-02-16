import datetime
import mock
import os
import unittest

import notification_utils

from shoebox import archive
from shoebox import roll_checker
from shoebox import roll_manager


class FakeArchive(object):
    def __init__(self, filename):
        self.filename = filename
        self.data = []

    def write(self, metadata, payload):
        self.data.append((metadata, payload))


class TestRollManager(unittest.TestCase):
    def test_close(self):
        callback = mock.Mock()
        x = roll_manager.RollManager("template",
                                     archive_callback=callback)
        x.active_archive = mock.Mock()
        x.active_filename = "foo"
        x.close()
        self.assertTrue(x.active_archive is None)
        self.assertTrue(x.active_filename is None)
        self.assertTrue(callback.on_close.called)


class TestWritingRollManager(unittest.TestCase):
    def test_write_always_roll(self):
        checker = mock.Mock()
        checker.check.return_value = True
        x = roll_manager.WritingRollManager("template", checker,
                                            archive_class=FakeArchive)
        with mock.patch.object(x, "_roll_archive") as ra:
            x.write({}, "payload")
            self.assertTrue(ra.called)

    def test_write_never_roll(self):
        checker = mock.Mock()
        checker.check.return_value = False
        x = roll_manager.WritingRollManager("template", checker,
                                            archive_class=FakeArchive)
        with mock.patch.object(x, "_roll_archive") as ra:
            x.write({}, "payload")
            self.assertFalse(ra.called)

    def test_correct_archiver(self):
        x = roll_manager.WritingRollManager("foo", None)
        print x.archive_class
        self.assertEqual(x.archive_class, archive.ArchiveWriter)

    def test_get_active_archive(self):
        checker = mock.Mock()
        callback = mock.Mock()
        filename_template = "filename_%c.dat"
        x = roll_manager.WritingRollManager(filename_template, checker,
                                            archive_callback=callback,
                                            archive_class=FakeArchive)
        with mock.patch("shoebox.archive.ArchiveWriter._open_file") as of:
            arc = x.get_active_archive()
            self.assertTrue(checker.start.called)
            self.assertTrue(callback.on_open.called)

    def test_make_filename(self):
        now = datetime.datetime(day=1, month=2, year=2014,
                                hour=10, minute=11, second=12)
        x = roll_manager.WritingRollManager("filename_%c.dat", None)

        with mock.patch.object(notification_utils, "now") as dt:
            dt.return_value = now
            filename = x._make_filename()
            self.assertEqual(filename,
                             "./filename_Sat_Feb__1_10_11_12_2014.dat")


class TestWriting(unittest.TestCase):
    def test_write(self):
        checker = roll_checker.NeverRollChecker()
        x = roll_manager.WritingRollManager("template_%s", checker,
                                            archive_class=FakeArchive)

        for index in range(10):
            x.write({"index": str(index)}, "payload_%d" % index)

        arc = x.get_active_archive()
        self.assertEqual(10, len(arc.data))
        self.assertEqual(({"index": "0"}, "payload_0"), arc.data[0])


class TestJSONRollManager(unittest.TestCase):
    def test_bad_directory(self):
        try:
            roll_manager.WritingJSONRollManager("x", directory="bad_directory")
            self.fail("Should raise BadWorkingDirectory")
        except roll_manager.BadWorkingDirectory as e:
            pass


    def test_make_filename(self):
        now = datetime.datetime(day=1, month=2, year=2014,
                                hour=10, minute=11, second=12)
        with mock.patch.object(notification_utils, "now") as dt:
            with mock.patch.object(notification_utils, "dt_to_decimal") as td:
                td.return_value = 123.45
                dt.return_value = now
                x = roll_manager.WritingJSONRollManager(
                                        "%Y%m%d [[TIMESTAMP]] [[CRC]].foo")
                fn = x._make_filename("mycrc")
                self.assertEqual("./20140201_123.45_mycrc.foo", fn)

    def test_write(self):
        x = roll_manager.WritingJSONRollManager("template.foo")
        with mock.patch.object(roll_manager.gzip, "open") as gz:
            x.write("metadata", "json_payload")

        self.assertTrue(gz.called_once_with("template.foo", "wb"))
