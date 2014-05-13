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

import archive
import utils


class RollManager(object):
    def __init__(self, filename_template, roll_checker, directory="."):
        self.filename_template = filename_template
        self.roll_checker = roll_checker
        self.directory = directory
        self.active_archive = None

    def _make_filename(self):
        f = utils.now().strftime(self.filename_template)
        return f.replace(" ", "_")

    def get_active_archive(self):
        if not self.active_archive:
            filename = self._make_filename()
            self.active_archive = self.archive_class(filename)
            self.roll_checker.start(self.active_archive)

        return self.active_archive

    def _should_roll_archive(self):
        return self.roll_checker.check(self.active_archive)

    def _roll_archive(self):
        pass


class ReadingRollManager(RollManager):
    def __init__(self, filename_template, roll_checker, directory="."):
        super(ReadingRollManager, self).__init__(filename_template,
                                                 roll_checker, directory)
        self.archive_class = archive.ArchiveReader

    def read_block(self):
        pass

    def read_header(self):
        pass

    def read_payload(self):
        pass


class WritingRollManager(RollManager):
    def __init__(self, filename_template, roll_checker, directory="."):
        super(WritingRollManager, self).__init__(filename_template,
                                                 roll_checker, directory)
        self.archive_class = archive.ArchiveWriter

    def write(self, payload):
        a = self.get_active_archive()
        a.write(payload)
        if self._should_roll_archive():
            self._roll_archive()
