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

import simport


class ArchiveCallback(object):
    def __init__(self, **kwargs):
        pass

    def on_open(self, filename):
        """Called when an Archive is opened."""
        pass

    def on_close(self, filename):
        """Called when an Archive is closed."""
        pass


class CallbackList(ArchiveCallback):
    def __init__(self, **kwargs):
        super(CallbackList, self).__init__(**kwargs)
        self.callbacks = []
        self.config = kwargs.get('config', {})
        callback_list_str = self.config.get('callback_list', "")
        callback_list = [x.strip() for x in callback_list_str.split(",")]
        self.callback_list = [simport.load(c) for c in callback_list]

    # TODO(Sandy): Need some exception handling around these.
    # The failure of one shouldn't stop processing.
    def on_open(self, filename):
        for c in self.callbacks:
            c.on_open(filename)

    def on_close(self, filename):
        for c in self.callbacks:
            c.on_close(filename)


class ChangeExtensionCallback(object):
    """filename.dat becomes filename.dat.done"""
    def __init__(self, **kwargs):
        super(ChangeExtensionCallback, self).__init__(**kwargs)
        self.new_extension = kwargs.get('new_extension', '.done')

    def on_close(self, filename):
        os.rename(filename, "%s.%s" % (filename, self.new_extension))


class MoveFileCallback(object):
    def __init__(self, **kwargs):
        super(MoveFileCallback, self).__init__(**kwargs)
        self.destination_folder = kwargs.get('destination_folder', '.')

    def on_close(self, filename):
        """Move this file to destination folder."""
        shutil.move(filename, self.destination_folder)
