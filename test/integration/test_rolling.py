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


class ArchiveCallback(object):
    def __init__(self, active_files):
        self.active_files = active_files

    def on_open(self, filename):
        self.active_files.add(filename)
        print "Opened:", filename

    def on_close(self, filename):
        self.active_files.remove(filename)
        print "Closed:", filename


class TestSizeRolling(unittest.TestCase):
    def setUp(self):
        shutil.rmtree(TEMPDIR, ignore_errors=True)
        os.mkdir(TEMPDIR)

    def tearDown(self):
        # shutil.rmtree(TEMPDIR)
        pass

    def test_size_rolling(self):
        active_files = set()
        callback = ArchiveCallback(active_files)

        checker = roll_checker.SizeRollChecker(1)
        manager = roll_manager.WritingRollManager("test_%Y_%m_%d_%f.events",
                                                  checker,
                                                  TEMPDIR,
                                                  archive_callback=callback)

        g = egen.EventGenerator(6000)
        entries = []
        now = datetime.datetime.utcnow()
        while len(entries) < 10000:
            events = g.generate(now)
            if events:
                for event in events:
                    metadata = {'event': event['event'],
                                'request_id': event['request_id'],
                                'generated': str(event['when']),
                                'uuid': event['uuid'],
                                }
                    json_event = json.dumps(event,
                                            cls=utils.DateTimeEncoder)
                    manager.write(metadata, json_event)
                    entries.append((metadata, json_event))

            now = g.move_to_next_tick(now)
        manager.close()

        raise Exception("Boom")

