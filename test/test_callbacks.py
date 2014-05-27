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

