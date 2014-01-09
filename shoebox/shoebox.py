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


class RollChecker(object):
    pass


class TimeRollChecker(RollChecker):
    def start(self, file_handle):
        pass

    def check(self, file_handle):
        pass


class SizeRollChecker(RollChecker):
    def start(self, file_handle):
        pass

    def check(self, file_handle):
        pass


class RollManager(object):
    def __init__(self, filename_template, roll_checker):
        self.filename_template = filename_template
        self.roll_checker = roll_checker


class ReadingRollManager(RollManager):
     def read_block(self):
        pass

    def read_header(self):
        pass

    def read_payload(self):
        pass


class WritingRollManager(RollManager):
    def write(self, payload):
        pass


class ArchiveWriter(object):
    """The active Archive for appending.
    """
    def __init__(self, filename):
        pass

    def write(self, payload):
        pass


class ArchiveReader(object):
    """The active Archive for consuming.
    """
    def __init__(self, filename):
        pass

    def read_block(self):
        pass

    def read_header(self):
        pass

    def read_payload(self):
        pass

