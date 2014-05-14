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

import utils


class RollChecker(object):
    def start(self, archive):
        """Called when a new archive is selected."""
        pass

    def check(self, archive):  # pragma: no cover
        """Should the current archive roll?"""
        pass


class NeverRollChecker(RollChecker):
    def check(self, archive):
        return False


class TimeRollChecker(RollChecker):
    def __init__(self, timedelta):
        self.timedelta = timedelta

    def start(self, archive):
        self.start_time = utils.now()
        self.end_time = self.start_time + self.timedelta

    def check(self, archive):
        return utils.now() >= self.end_time


class SizeRollChecker(RollChecker):
    def __init__(self, size_in_mb):
        self.size_in_mb = size_in_mb

    def check(self, archive):
        size = archive.get_file_handle().tell()
        return (size / 1048576) >= self.size_in_mb
