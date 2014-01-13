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

"""Binary data archiving library.

Data is written in the following format:

[HEADER]
[PAYLOAD]
[FOOTER]

where:
    [HEADER] =
        [START-OF-BLOCK]
        [BLOCK-TYPE]
        [SIZE]

    [FOOTER] =
        [CRC]
        [END-OF-BLOCK]

There are ArchiveReaders and ArchiveWriters which are managed
by RollManager. The RollManager opens and closes Archivers as
needed. "As needed" is determined by which RollChecker that was
passed into the RollManager. Archive files can roll over based
on file size or elapsed time (for writing). For reading, archive
files are only rolled over when the EOF is reached.

Roll Managers also take care of filename creation, compression
of completed archives and transfer of archive files to remote
storage locations.

TODO: How will the ReadingRollManager know which files to read
from, and in which order, if the filename is templated?
"""

def now():
    """Broken out for testing."""
    return datetime.datetime.utcnow()


class RollChecker(object):
    def start(self, archive):
        pass

    def check(self, archive):
        pass


class TimeRollChecker(RollChecker):
    def __init__(self, timedelta):
        self.timedelta = timedelta

    def start(self, archive):
        self.start_time = now()
        self.end_time = self.start_time + self.timedelta

    def check(self, archive):
        return now() >= self.end_time


class SizeRollChecker(RollChecker):
    def __init__(self, size_in_gb):
        self.size_in_gb = size_in_gb

    def check(self, archive):
        size = archive._get_file_handle().tell()
        return size / 1073741824 >= self.size_in_gb


class RollManager(object):
    def __init__(self, filename_template, roll_checker, directory="."):
        self.filename_template = filename_template
        self.roll_checker = roll_checker
        self.directory = directory
        self.active_archive = None

    def _make_filename(self):
        f = now().strftime(self.filename_template)
        return f.replace(" ", "_")

    def get_active_archive(self):
        if not self.active_archive:
            filename = self._make_filename()
            self.active_archive = self.archive_class(filename)
            self.roll_checker.start(self.active_archive)

        return self.active_archive

    def _should_roll_archive(self):
        return False

    def _roll_archive(self):
        pass


class ReadingRollManager(RollManager):

    def __init__(self, filename_template, roll_checker, directory="."):
        super(ReadingRollManager, self).__init__(filename_template,
                                                 roll_checker, directory)
        self.archive_class = ArchiveReader

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
        self.archive_class = ArchiveWriter

    def write(self, payload):
        a = self.get_active_archive()
        a.write(payload)
        if self._should_roll_archive(a):
            self._roll_archive()


class Archive(object):
    def __init__(self, filename):
        self._handle = None
        self.filename = filename

    def get_file_handle(self):
        return self._handle


class ArchiveWriter(Archive):
    """The active Archive for appending.
    """
    def __init__(self, filename):
        super(ArchiveWriter, self).__init__(filename)
        self._handle = open(filename, "wb+")

    def write(self, payload):
        pass



class ArchiveReader(Archive):
    """The active Archive for consuming.
    """
    def __init__(self, filename):
        super(ArchiveReader, self).__init__(filename)

    def read_block(self):
        pass

    def read_header(self):
        pass

    def read_payload(self):
        pass

