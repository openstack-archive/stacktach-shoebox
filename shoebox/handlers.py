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
import shutil


class ArchiveCallback(object):
    def on_open(self, filename):
        """Called when an Archive is opened."""
        pass

    def on_close(self, filename):
        """Called when an Archive is closed."""
        pass


class MoveFileCallback(object):
    def __init__(self, destination_folder):
        self.destination_folder = destination_folder

    def on_close(self, filename):
        """Move this file to destination folder."""
        shutil.move(filename, self.destination_folder)
