import datetime
import mock
import unittest

import notification_utils

from shoebox import roll_checker


class TestRollChecker(unittest.TestCase):
    def test_time_roll_checker_start(self):
        one_hour = datetime.timedelta(hours=1)
        x = roll_checker.TimeRollChecker(one_hour)
        now = datetime.datetime.utcnow()
        with mock.patch.object(notification_utils, 'now') as dt:
            dt.return_value = now
            x.start(None)
        self.assertEqual(x.start_time, now)
        self.assertEqual(x.end_time, now + one_hour)

    def test_time_roll_checker_end(self):
        one_hour = datetime.timedelta(hours=1)
        x = roll_checker.TimeRollChecker(one_hour)
        now = datetime.datetime.utcnow()
        x.start_time = now
        x.end_time = now + one_hour
        with mock.patch.object(notification_utils, 'now') as dt:
            dt.return_value = now + one_hour
            self.assertTrue(x.check(None))

        with mock.patch.object(notification_utils, 'now') as dt:
            dt.return_value = now
            self.assertFalse(x.check(None))

        with mock.patch.object(notification_utils, 'now') as dt:
            dt.return_value = now + one_hour - datetime.timedelta(seconds = 1)
            self.assertFalse(x.check(None))

    def test_size_roll_checker_end(self):
        one_mb = 1048576
        x = roll_checker.SizeRollChecker(10)

        archive = mock.Mock()
        archive.get_file_handle.return_value.tell.return_value = one_mb * 5
        self.assertFalse(x.check(archive))

        archive.get_file_handle.return_value.tell.return_value = one_mb * 10
        self.assertTrue(x.check(archive))

        archive.get_file_handle.return_value.tell.return_value = one_mb * 11
        self.assertTrue(x.check(archive))
