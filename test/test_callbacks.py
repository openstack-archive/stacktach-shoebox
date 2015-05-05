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

import unittest

from shoebox import handlers


class FooCallback(handlers.ArchiveCallback):
    pass


class BlahCallback(handlers.ArchiveCallback):
    pass


class TestCallbackList(unittest.TestCase):
    def test_list(self):
        config = {"callback_list": "test|test_callbacks:FooCallback,"
                                   "shoebox.handlers:ChangeExtensionCallback, "
                                   "%s:BlahCallback" % __name__}
        c = handlers.CallbackList(**config)

        # Note: isinstance will fail for this check because it's technically a
        # different class since it comes from a different module i
        # (the 'test' module).
        self.assertTrue("FooCallback" in str(type(c.callbacks[0])))
        self.assertTrue(isinstance(c.callbacks[1],
                                   handlers.ChangeExtensionCallback))
        self.assertTrue(isinstance(c.callbacks[2], BlahCallback))
