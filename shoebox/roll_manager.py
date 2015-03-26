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

import fnmatch
import hashlib
import os
import os.path
import tarfile

import notification_utils

import archive
import disk_storage


class NoMoreFiles(Exception):
    pass


class NoValidFile(Exception):
    pass


class BadWorkingDirectory(Exception):
    pass


class RollManager(object):
    def __init__(self, filename_template, directory=".",
                 archive_class=None, archive_callback=None):
        self.filename_template = filename_template
        self.directory = directory
        self.active_archive = None
        self.archive_class = archive_class
        self.active_filename = None
        self.archive_callback = archive_callback

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
    def __init__(self, filename_template, directory=".",
                 destination_directory=".",
                 archive_class = archive.ArchiveReader,
                 archive_callback=None, roll_size_mb=1000):
        super(ReadingRollManager, self).__init__(
                                            filename_template,
                                            directory=directory,
                                            archive_callback=archive_callback,
                                            archive_class=archive_class)
        self.files_to_read = self._get_matching_files(directory,
                                                      filename_template)

    def _get_matching_files(self, directory, filename_template):
        files = [os.path.join(directory, f)
                    for f in os.listdir(self.directory)
                        if os.path.isfile(os.path.join(directory, f))]
        return sorted(fnmatch.filter(files, filename_template))

    def read(self):
        # (metadata, payload)
        for x in range(3):  # 3 attempts to file a valid file.
            a = self.get_active_archive()
            try:
                return a.read()
            except disk_storage.EndOfFile:
                self._roll_archive()
        raise NoValidFile("Unable to find a valid file after 3 attempts")

    def get_active_archive(self):
        if not self.active_archive:
            if not self.files_to_read:
                raise NoMoreFiles()
            self.active_filename = self.files_to_read.pop(0)
            self.active_archive = self.archive_class(self.active_filename)
            if self.archive_callback:
                self.archive_callback.on_open(self.active_filename)
        return self.active_archive


class WritingRollManager(RollManager):
    def __init__(self, filename_template, roll_checker, directory=".",
                 destination_directory=".",
                 archive_class=archive.ArchiveWriter,
                 archive_callback=None, roll_size_mb=1000):
        super(WritingRollManager, self).__init__(
                                            filename_template,
                                            directory=directory,
                                            archive_callback=archive_callback,
                                            archive_class=archive_class)
        self.roll_checker = roll_checker

    def write(self, metadata, payload):
        """metadata is string:string dict.
           payload must be encoded as string.
        """
        a = self.get_active_archive()
        a.write(metadata, payload)
        if self._should_roll_archive():
            self._roll_archive()

    def _make_filename(self):
        f = notification_utils.now().strftime(self.filename_template)
        f = f.replace(" ", "_")
        f = f.replace("/", "_")
        f = f.replace(":", "_")
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


class WritingJSONRollManager(object):
    """No archiver. No roll checker. Just write the file locally.
       Once the working_directory gets big enough, the files are
       .tar.gz'ed into the destination_directory. Then
       the working_directory is erased.
       Expects an external tool like rsync to move the file.
       A SHA-256 of the payload may be included in the filename."""
    def __init__(self, *args, **kwargs):
        self.filename_template = args[0]
        self.directory = kwargs.get('directory', '.')
        self.destination_directory = kwargs.get('destination_directory', '.')
        self.roll_size_mb = int(kwargs.get('roll_size_mb', 1000))

        # Read the directory at the start, but incrementally
        # update the size as we write more files. Doing a full
        # disk stat every time is way too expensive.
        # Of course, this means we are not accounting for
        # block size.
        self.directory_size = self._get_directory_size()

    def _make_filename(self, crc, prefix):
        now = notification_utils.now()
        dt = str(notification_utils.dt_to_decimal(now))
        f = now.strftime(self.filename_template)
        f = f.replace(" ", "_")
        f = f.replace("/", "_")
        f = f.replace(":", "_")
        f = f.replace("[[CRC]]", crc)
        f = f.replace("[[TIMESTAMP]]", dt)
        return os.path.join(prefix, f)

    def _should_tar(self):
        return (self.directory_size / 1048576) >= self.roll_size_mb

    def _get_directory_size(self):
        size = 0
        for f in os.listdir(self.directory):
            full = os.path.join(self.directory, f)
            if os.path.isfile(full):
                size += os.path.getsize(full)
        return size

    def _tar_directory(self):
        # tar all the files in working directory into an archive
        # in destination_directory.
        crc = "archive"
        filename = self._make_filename(crc, self.destination_directory) + \
                            ".tar.gz"

        # No contextmgr for tarfile in 2.6 :(
        tar = tarfile.open(filename, "w:gz")
        for f in os.listdir(self.directory):
            full = os.path.join(self.directory, f)
            if os.path.isfile(full):
                tar.add(full)
        tar.close()

    def _clean_working_directory(self):
        for f in os.listdir(self.directory):
            full = os.path.join(self.directory, f)
            if os.path.isfile(full):
                os.remove(full)
        self.directory_size = self._get_directory_size()

    def write(self, metadata, json_payload):
        # Metadata is ignored.
        crc = hashlib.sha256(json_payload).hexdigest()
        filename = self._make_filename(crc, self.directory)
        with open(filename, "w") as f:
            f.write(json_payload)

        self.directory_size += len(json_payload)

        if not self._should_tar():
            return

        self._tar_directory()
        self._clean_working_directory()

    def close(self):
        pass
