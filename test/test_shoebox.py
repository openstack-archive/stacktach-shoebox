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
    pass  # Next ...
