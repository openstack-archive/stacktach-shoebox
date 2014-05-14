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

import disk_storage


class Archive(object):
    def __init__(self, filename):
        self._handle = None
        self.filename = filename

    def get_file_handle(self):  # pragma: no cover
        return self._handle

    def close(self):
        self._handle.close()


class ArchiveWriter(Archive):
    """The active Archive for appending.
    """
    def __init__(self, filename):
        super(ArchiveWriter, self).__init__(filename)
        self._open_file(filename)

    def _open_file(self, filename):
        # Broken out for testing.
        self._handle = open(filename, "wb+")

    def write(self, metadata, payload):
        binary = disk_storage.pack_notification(payload, metadata)
        for block in binary:
            self._handle.write(block)


class ArchiveReader(Archive):
    """The active Archive for consuming.
    """
    def __init__(self, filename):
        super(ArchiveReader, self).__init__(filename)
        self._open_file(filename)

    def _open_file(self, filename):
        # Broken out for testing.
        self._handle = open(filename, "rb")

    def read(self):
        # (metadata, payload)
        return disk_storage.unpack_notification(self._handle)
