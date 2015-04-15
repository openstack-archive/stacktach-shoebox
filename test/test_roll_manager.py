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
        "shoebox.roll_manager.WritingJSONRollManager._archive_working_files")
    def test_make_filename(self, awf):
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

    @mock.patch('os.listdir')
    @mock.patch('os.path.isfile')
    def test_archive_working_files(self, isf, ld):
        rm = roll_manager.WritingJSONRollManager("template.foo")
        ld.return_value = ['a', 'b', 'c']
        isf.return_value = True
        with mock.patch.object(rm, "_do_roll") as dr:
            rm._archive_working_files()
            self.assertEqual(dr.call_count, 3)

    @mock.patch(
        "shoebox.roll_manager.WritingJSONRollManager._archive_working_files")
    def test_should_roll(self, awf):
        rm = roll_manager.WritingJSONRollManager("template.foo")
        rm.roll_size_mb = 10
        self.assertFalse(rm._should_roll(9*1048576))
        self.assertTrue(rm._should_roll(10*1048576))

        rm = roll_manager.WritingJSONRollManager("template.foo", roll_minutes=10)
        self.assertFalse(rm._should_roll(0))
        self.assertFalse(rm._should_roll(1))
        with mock.patch.object(rm, "_get_time") as gt:
            gt.return_value = rm.start_time + datetime.timedelta(minutes=11)
            self.assertTrue(rm._should_roll(1))

    @mock.patch('os.remove')
    @mock.patch(
        "shoebox.roll_manager.WritingJSONRollManager._archive_working_files")
    def test_clean_working_directory(self, awf, rem):
        rm = roll_manager.WritingJSONRollManager("template.foo")
        rm._clean_working_directory("foo")
        self.assertEqual(1, rem.call_count)

    @mock.patch(
        "shoebox.roll_manager.WritingJSONRollManager._archive_working_files")
    def test_gzip_working_file(self, awf):
        rm = roll_manager.WritingJSONRollManager("template.foo")

        with mock.patch.object(rm, "_get_file_sha") as gfs:
            gfs.return_value = "aabbcc"

            open_name = '%s.open' % roll_manager.__name__
            with mock.patch(open_name, create=True) as mock_open:
                handle = mock.MagicMock()
                mock_open.return_value = handle
                with mock.patch.object(roll_manager.gzip, 'open') as gzip:
                    gzip.return_value = mock.MagicMock()
                    rm._gzip_working_file("foo")
                    self.assertTrue(gzip.called)

    @mock.patch(
        "shoebox.roll_manager.WritingJSONRollManager._archive_working_files")
    def test_write(self, awf):
        rm = roll_manager.WritingJSONRollManager("template.foo")
        payload = "some big payload"
        with mock.patch.object(rm, "_get_handle") as gh:
            with mock.patch.object(rm, "_should_roll") as sr:
                with mock.patch.object(rm, "_do_roll") as dr:
                    sr.return_value = False
                    gh.return_value = mock.MagicMock()
                    rm.write("metadata", payload)
                    self.assertFalse(dr.called)
                    self.assertEqual(rm.size, len(payload))

    @mock.patch(
        "shoebox.roll_manager.WritingJSONRollManager._archive_working_files")
    def test_get_file_sha(self, awf):
        rm = roll_manager.WritingJSONRollManager("template.foo")
        with mock.patch.object(roll_manager.hashlib, "sha256") as sha:
            sha_obj = mock.MagicMock()
            sha.return_value = sha_obj
            hexdigest = mock.MagicMock()
            hexdigest.return_value = "aabbcc"
            sha_obj.hexdigest = hexdigest
            open_name = '%s.open' % roll_manager.__name__
            with mock.patch(open_name, create=True) as mock_open:
                handle = mock.MagicMock()
                mock_open.return_value = handle
                data = mock.MagicMock()
                handle.read = data
                data.side_effect = ["a", "b", "c", False]
                self.assertEqual("aabbcc", rm._get_file_sha('foo'))

    @mock.patch(
        "shoebox.roll_manager.WritingJSONRollManager._archive_working_files")
    def test_get_handle(self, awf):
        rm = roll_manager.WritingJSONRollManager("template.foo")
        rm.handle = "abc"
        self.assertEqual("abc", rm._get_handle())

        with mock.patch.object(rm, "_make_filename") as mf:
            mf.return_value = "foo"
            open_name = '%s.open' % roll_manager.__name__
            with mock.patch(open_name, create=True) as mock_open:
                handle = mock.MagicMock()
                mock_open.return_value = handle
                rm.handle = None
                self.assertEqual(handle, rm._get_handle())
