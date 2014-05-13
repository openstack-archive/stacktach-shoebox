import datetime
import mock
import os
import shutil
import unittest


from shoebox import roll_checker
from shoebox import roll_manager
from shoebox import utils

import test.integration.gen_events as egen


TEMPDIR = "test_temp"


class TestSizeRolling(unittest.TestCase):
    def setUp(self):
        shutil.rmtree(TEMPDIR, ignore_errors=True)
        os.mkdir(TEMPDIR)

    def tearDown(self):
        shutil.rmtree(TEMPDIR)

    def test_size_rolling(self):
        checker = roll_checker.SizeRollChecker(1)
        manager = roll_manager.WritingRollManager("test_%c.events",
                                                  checker,
                                                  TEMPDIR)
        g = egen.EventGenerator(6000)
        nevents = 0
        now = datetime.datetime.utcnow()
        while nevents < 1000:
            e = g.generate(now)
            if e:
                nevents += len(e)
            now = g.move_to_next_tick(now)
