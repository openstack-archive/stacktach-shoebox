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
import fnmatch
import gzip
import hashlib
import os
import os.path

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
    """No archiver. No roll checker. Just write 1 file line per json payload.
       Once the file gets big enough, gzip the file and move
       into the destination_directory.
       Expects an external tool like rsync to move the file.
       A SHA-256 of the payload may be included in the archive filename."""
    def __init__(self, *args, **kwargs):
        self.filename_template = args[0]
        self.directory = kwargs.get('directory', '.')
        self.destination_directory = kwargs.get('destination_directory', '.')
        self.roll_size_mb = int(kwargs.get('roll_size_mb', 1000))
        minutes = kwargs.get('roll_minutes', 60)
        self.roll_after = datetime.timedelta(minutes=minutes)

        # Look in the working directory for any files. Move them to the
        # destination directory before we start. This implies we
        # have to make sure multiple workers don't point at the same
        # working directory.
        self.handle = None
        self.size = 0
        self.start_time = self._get_time()

        self._archive_working_files()

    def _get_time(self):
        # Broken out for testing ...
        return datetime.datetime.utcnow()

    def _archive_working_files(self):
        for f in os.listdir(self.directory):
            full = os.path.join(self.directory, f)
            if os.path.isfile(full):
                self._do_roll(full)

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

    def _should_roll(self, size):
        return ((size / 1048576) >= self.roll_size_mb or
                (size > 0 and
                 self._get_time() >= (self.start_time + self.roll_after)))

    def _get_file_sha(self, filename):
        block_size=2**20
        sha256 = hashlib.sha256()
        # no context manager, just to keep testing simple.
        f = open(filename, "r")
        while True:
            data = f.read(block_size)
            if not data:
                break
            sha256.update(data)
        f.close()
        return sha256.hexdigest()

    def _gzip_working_file(self, filename):
        # gzip the working file in the destination_directory.
        crc = self._get_file_sha(filename)

        fn = self._make_filename(crc, self.destination_directory) + ".gz"

        with open(filename, 'r') as file_in:
            file_out = gzip.open(fn, 'wb')
            file_out.writelines(file_in)
            file_out.close()

    def _clean_working_directory(self, filename):
        os.remove(filename)
        self.size = 0

    def _do_roll(self, filename):
        self.close()
        self._gzip_working_file(filename)
        self._clean_working_directory(filename)

    def write(self, metadata, json_payload):
        # Metadata is ignored.
        handle = self._get_handle()
        handle.write("%s\n" % json_payload)
        handle.flush()

        self.size += len(json_payload)

        if self._should_roll(self.size):
            self._do_roll(self.filename)

    def _get_handle(self):
        if not self.handle:
            self.filename = self._make_filename('[[CRC]]', self.directory)
            self.handle = open(self.filename, "w")
            self.start_time = self._get_time()

        return self.handle

    def close(self):
        if self.handle:
            self.handle.close()
            self.handle = None
