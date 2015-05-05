# Copyright (c) 2014 Dark Secret Software Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import datetime
import mock
import unittest

import notification_utils

from shoebox import roll_checker


class TestRollChecker(unittest.TestCase):
    def test_time_roll_checker_start(self):
        x = roll_checker.TimeRollChecker(roll_minutes=60)
        now = datetime.datetime.utcnow()
        with mock.patch.object(notification_utils, 'now') as dt:
            dt.return_value = now
            x.start(None)
        self.assertEqual(x.start_time, now)
        one_hour = datetime.timedelta(hours=1)
        self.assertEqual(x.end_time, now + one_hour)

    def test_time_roll_checker_end(self):
        one_hour = datetime.timedelta(hours=1)
        x = roll_checker.TimeRollChecker(roll_minutes=60)
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
            dt.return_value = now + one_hour - datetime.timedelta(seconds=1)
            self.assertFalse(x.check(None))

    def test_size_roll_checker_end(self):
        x = roll_checker.SizeRollChecker(roll_size_mb=10)
        archive = mock.Mock()
        one_mb = 1048576
        archive.get_file_handle.return_value.tell.return_value = one_mb * 5
        self.assertFalse(x.check(archive))

        archive.get_file_handle.return_value.tell.return_value = one_mb * 10
        self.assertTrue(x.check(archive))

        archive.get_file_handle.return_value.tell.return_value = one_mb * 11
        self.assertTrue(x.check(archive))
