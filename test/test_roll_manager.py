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
    @mock.patch(
        "shoebox.roll_manager.WritingJSONRollManager._get_directory_size")
    def test_make_filename(self, gds):
        gds.return_value = 1000
        now = datetime.datetime(day=1, month=2, year=2014,
                                hour=10, minute=11, second=12)
        with mock.patch.object(notification_utils, "now") as dt:
            with mock.patch.object(notification_utils, "dt_to_decimal") as td:
                td.return_value = 123.45
                dt.return_value = now
                x = roll_manager.WritingJSONRollManager(
                                        "%Y%m%d [[TIMESTAMP]] [[CRC]].foo")
                fn = x._make_filename("mycrc", "foo")
                self.assertEqual("foo/20140201_123.45_mycrc.foo", fn)

    @mock.patch('os.path.getsize')
    @mock.patch('os.listdir')
    @mock.patch('os.path.isfile')
    def test_get_directory_size(self, isf, ld, gs):
        rm = roll_manager.WritingJSONRollManager("template.foo")
        gs.return_value = 250000
        ld.return_value = ['a', 'b', 'c']
        isf.return_value = True
        self.assertEqual(250000*3, rm._get_directory_size())
        ld.return_value = ['a', 'b', 'c', 'd', 'e', 'f']
        self.assertEqual(250000*6, rm._get_directory_size())

    @mock.patch(
        "shoebox.roll_manager.WritingJSONRollManager._get_directory_size")
    def test_should_tar(self, gds):
        gds.return_value = 1000
        rm = roll_manager.WritingJSONRollManager("template.foo")
        rm.directory_size = 9 * 1048576
        rm.roll_size_mb = 10
        self.assertFalse(rm._should_tar())
        rm.directory_size = 10 * 1048576
        rm.roll_size_mb = 10
        self.assertTrue(rm._should_tar())

    @mock.patch('os.listdir')
    @mock.patch('os.remove')
    @mock.patch('os.path.isfile')
    @mock.patch(
        "shoebox.roll_manager.WritingJSONRollManager._get_directory_size")
    def test_clean_working_directory(self, gds, isf, rem, ld):
        gds.return_value = 1000
        isf.return_value = True
        rm = roll_manager.WritingJSONRollManager("template.foo")
        ld.return_value = ['a', 'b', 'c']
        rm._clean_working_directory()
        self.assertEqual(3, rem.call_count)

    @mock.patch('os.listdir')
    @mock.patch('tarfile.open')
    @mock.patch('os.path.isfile')
    @mock.patch(
        "shoebox.roll_manager.WritingJSONRollManager._get_directory_size")
    def test_tar_directory(self, gds, isf, to, ld):
        gds.return_value = 1000
        ld.return_value = ['a', 'b', 'c']
        isf.return_value = True
        gds = 1000
        rm = roll_manager.WritingJSONRollManager("template.foo")

        open_name = '%s.open' % roll_manager.__name__
        with mock.patch(open_name, create=True) as mock_open:
            mock_open.return_value = mock.MagicMock(spec=file)

            rm._tar_directory()
            self.assertTrue(to.called)

    @mock.patch(
        "shoebox.roll_manager.WritingJSONRollManager._get_directory_size")
    def test_write(self, gds):
        gds.return_value = 0
        rm = roll_manager.WritingJSONRollManager("template.foo")
        payload = "some big payload"
        open_name = '%s.open' % roll_manager.__name__
        with mock.patch(open_name, create=True) as mock_open:
            with mock.patch.object(rm, "_should_tar") as st:
                with mock.patch.object(rm, "_tar_directory") as td:
                    st.return_value = False
                    mock_open.return_value = mock.MagicMock(spec=file)
                    rm.write("metadata", payload)
                    self.assertTrue(mock_open.called_once_with(
                                                "template.foo", "wb"))
                    self.assertFalse(td.called)
                    self.assertEqual(rm.directory_size, len(payload))
