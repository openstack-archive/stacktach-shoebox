import datetime
import mock
import os
import unittest

from shoebox import archive
from shoebox import roll_checker
from shoebox import roll_manager
from shoebox import utils


class TestRollManager(unittest.TestCase):
    def test_make_filename(self):
        now = datetime.datetime(day=1, month=2, year=2014,
                                hour=10, minute=11, second=12)
        x = roll_manager.RollManager("filename_%c.dat", None)

        with mock.patch.object(utils, "now") as dt:
            dt.return_value = now
            filename = x._make_filename()
            self.assertEqual(filename, "filename_Sat_Feb__1_10:11:12_2014.dat")


class FakeArchive(object):
    def __init__(self, filename):
        self.filename = filename
        self.data = []

    def write(self, metadata, payload):
        self.data.append((metadata, payload))


class TestWritingRollManager(unittest.TestCase):
    def test_get_active_archive(self):
        checker = mock.Mock()
        filename_template = "filename_%c.dat"
        x = roll_manager.WritingRollManager(filename_template, checker)
        with mock.patch("shoebox.archive.ArchiveWriter._open_file") as of:
            arc = x.get_active_archive()
            self.assertTrue(isinstance(arc, archive.ArchiveWriter))
            self.assertTrue(checker.start.called)

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
