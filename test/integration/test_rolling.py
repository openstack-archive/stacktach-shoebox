import datetime
import json
import mock
import os
import shutil
import unittest


from shoebox import disk_storage
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
            events = g.generate(now)
            if events:
                nevents += len(events)
                for event in events:
                    metadata = {'event': event['event'],
                                'request_id': event['request_id'],
                                'generated': str(event['when']),
                                'uuid': event['uuid'],
                                }
                    json_event = json.dumps(event,
                                            cls=utils.DateTimeEncoder)
                    manager.write(metadata, json_event)

            now = g.move_to_next_tick(now)

