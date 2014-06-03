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

import os
import os.path
import shutil

import pyrax

import simport


class MissingArgument(Exception):
    pass


class ArchiveCallback(object):
    def __init__(self, **kwargs):
        pass

    def on_open(self, filename):
        """Called when an Archive is opened."""
        pass

    def on_close(self, filename):
        """Called when an Archive is closed.
           If you move/change the file/name return the
           new location so subsequent callbacks will
           have the right location.
        """
        return filename


class CallbackList(ArchiveCallback):
    def __init__(self, **kwargs):
        super(CallbackList, self).__init__(**kwargs)
        self.callbacks = []
        self.config = kwargs
        callback_str = self.config.get('callback_list', "")
        callback_str_list = [x.strip() for x in callback_str.split(",")]
        self.callbacks = [simport.load(c)(**self.config)
                            for c in callback_str_list]
    # TODO(Sandy): Need some exception handling around these.
    # The failure of one shouldn't stop processing.
    def on_open(self, filename):
        for c in self.callbacks:
            c.on_open(filename)

    def on_close(self, filename):
        for c in self.callbacks:
            filename = c.on_close(filename)


class ChangeExtensionCallback(ArchiveCallback):
    """filename.dat becomes filename.dat.done"""
    def __init__(self, **kwargs):
        super(ChangeExtensionCallback, self).__init__(**kwargs)
        self.new_extension = kwargs.get('new_extension', '.done')

    def on_close(self, filename):
        new = "%s.%s" % (filename, self.new_extension)
        os.rename(filename, new)
        return new


class MoveFileCallback(ArchiveCallback):
    def __init__(self, **kwargs):
        super(MoveFileCallback, self).__init__(**kwargs)
        self.destination_folder = kwargs.get('destination_folder', '.')

    def on_close(self, filename):
        """Move this file to destination folder."""
        shutil.move(filename, self.destination_folder)
        path, fn = os.path.split(filename)
        return os.path.join(self.destination_folder, fn)


class DeleteFileCallback(ArchiveCallback):
    def on_close(self, filename):
        """Delete this file."""
        os.remove(filename)
        return None


class SwiftUploadCallback(ArchiveCallback):
    def __init__(self, **kwargs):
        super(SwiftUploadCallback, self).__init__(**kwargs)
        self.credentials_file = kwargs.get('credentials_file')
        if not self.credentials_file:
            raise MissingArgument("No credentials_file defined.")

        self.container = kwargs.get('container', 'shoebox')
        self.auth_method = kwargs.get('auth_method', 'rackspace')
        self.region = kwargs.get('region', 'DFW')

        pyrax.set_setting('identity_type', self.auth_method)
        pyrax.set_setting("region", self.region)
        pyrax.set_credential_file(self.credentials_file)

        self.cloud_files = pyrax.cloudfiles

        self.cloud_files.create_container(self.container)

    def on_close(self, filename):
        checksum = pyrax.utils.get_checksum(filename)
        # Blocking call ...
        obj = self.cloud_files.upload_file(self.container, filename,
                                           etag=checksum)
        return filename
