import datetime
import mock
import unittest

from shoebox import shoebox


class TestRollChecker(unittest.TestCase):
    def test_time_roll_checker_start(self):
        one_hour = datetime.timedelta(hours=1)
        x = shoebox.TimeRollChecker(one_hour)
        now = datetime.datetime.utcnow()
        with mock.patch.object(shoebox, 'now') as dt:
            dt.return_value = now
            x.start(None)
        self.assertEqual(x.start_time, now)
        self.assertEqual(x.end_time, now + one_hour)

    def test_time_roll_checker_end(self):
        one_hour = datetime.timedelta(hours=1)
        x = shoebox.TimeRollChecker(one_hour)
        now = datetime.datetime.utcnow()
        x.start_time = now
        x.end_time = now + one_hour
        with mock.patch.object(shoebox, 'now') as dt:
            dt.return_value = now + one_hour
            self.assertTrue(x.check(None))

        with mock.patch.object(shoebox, 'now') as dt:
            dt.return_value = now
            self.assertFalse(x.check(None))

        with mock.patch.object(shoebox, 'now') as dt:
            dt.return_value = now + one_hour - datetime.timedelta(seconds = 1)
            self.assertFalse(x.check(None))

    def test_size_roll_checker_end(self):
        one_gig = 1073741824
        x = shoebox.SizeRollChecker(10)

        archive = mock.Mock()
        archive._get_file_handle.return_value.tell.return_value = one_gig * 5
        self.assertFalse(x.check(archive))

        archive._get_file_handle.return_value.tell.return_value = one_gig * 10
        self.assertTrue(x.check(archive))

        archive._get_file_handle.return_value.tell.return_value = one_gig * 11
        self.assertTrue(x.check(archive))


class TestRollManager(unittest.TestCase):
    def test_make_filename(self):
        filename_template = "filename_%c"
        now = datetime.datetime(day=1, month=2, year=2014,
                                hour=10, minute=11, second=12)
        x = shoebox.RollManager("filename_%c.dat", None)

        with mock.patch.object(shoebox, "now") as dt:
            dt.return_value = now
            filename = x._make_filename()
            self.assertEqual(filename, "filename_Sat_Feb__1_10:11:12_2014.dat")

class TestWritingRollManager(unittest.TestCase):
    def test_get_active_archive(self):
        roll_checker = mock.Mock()
        filename_template = "filename_%c.dat"
        x = shoebox.WritingRollManager(filename_template, roll_checker)
        archive = x.get_active_archive()
        self.assertTrue(isinstance(archive, shoebox.ArchiveWriter))
        self.assertTrue(roll_checker.start.called)