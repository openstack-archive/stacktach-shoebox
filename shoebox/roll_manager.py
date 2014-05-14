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

import os.path

import archive
import utils


class ArchiveCallback(object):
    def on_open(self, filename):
        """Called when an Archive is opened."""
        pass

    def on_close(self, filename):
        """Called when an Archive is closed."""
        pass


class RollManager(object):
    def __init__(self, filename_template, roll_checker, directory=".",
                 archive_class=None, archive_callback=None):
        self.filename_template = filename_template
        self.roll_checker = roll_checker
        self.directory = directory
        self.active_archive = None
        self.archive_class = archive_class
        self.active_filename = None
        self.archive_callback = archive_callback

    def _make_filename(self):
        f = utils.now().strftime(self.filename_template)
        f = f.replace(" ", "_")
        f = f.replace("/", "_")
        return os.path.join(self.directory, f)

    def get_active_archive(self):
        if not self.active_archive:
            self.active_filename = self._make_filename()
            self.active_archive = self.archive_class(self.active_filename)
            if self.archive_callback:
                self.archive_callback.on_open(self.active_filename)
            self.roll_checker.start(self.active_archive)

        return self.active_archive

    def _should_roll_archive(self):
        return self.roll_checker.check(self.active_archive)

    def _roll_archive(self):
        self.close()
        self.get_active_archive()

    def close(self):
        if self.active_archive:
            self.active_archive.close()
            if self.archive_callback:
                self.archive_callback.on_close(self.active_filename)
            self.active_archive = None
            self.active_filename = None


class ReadingRollManager(RollManager):
    def __init__(self, filename_template, roll_checker, directory=".",
                 archive_class = archive.ArchiveReader,
                 archive_callback=None):
        super(ReadingRollManager, self).__init__(filename_template,
                                                 roll_checker,
                                                 directory=directory,
                                                 archive_callback=event_callback,
                                                 archive_class=archive_class)

    def read(self):
        pass


class WritingRollManager(RollManager):
    def __init__(self, filename_template, roll_checker, directory=".",
                 archive_class=archive.ArchiveWriter,
                 archive_callback=None):
        super(WritingRollManager, self).__init__(
                                            filename_template,
                                            roll_checker,
                                            directory=directory,
                                            archive_callback=archive_callback,
                                            archive_class=archive_class)

    def write(self, metadata, payload):
        """metadata is string:string dict.
           payload must be encoded as string.
        """
        a = self.get_active_archive()
        a.write(metadata, payload)
        if self._should_roll_archive():
            self._roll_archive()
