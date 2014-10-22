import datetime
import json
import mock
import os
import shutil
import unittest

import notification_utils
import notigen

from shoebox import disk_storage
from shoebox import roll_checker
from shoebox import roll_manager


TEMPDIR = "test_temp"


class ArchiveCallback(object):
    def __init__(self):
        self.active_files = {}
        self.ordered_files = []

    def on_open(self, filename):
        self.active_files[filename] = True
        self.ordered_files.append(filename)

    def on_close(self, filename):
        self.active_files[filename] = False


class VerifyArchiveCallback(object):
    def __init__(self, original_files):
        self.original_files = original_files

    def on_open(self, filename):
        o = self.original_files.pop(0)
        if filename != o:
            raise Exception("Wrong order: Got %s, Expected %s" %
                            (filename, o))

    def on_close(self, filename):
        pass


class TestSizeRolling(unittest.TestCase):
    def setUp(self):
        shutil.rmtree(TEMPDIR, ignore_errors=True)
        os.mkdir(TEMPDIR)

    def test_size_rolling(self):
        callback = ArchiveCallback()

        checker = roll_checker.SizeRollChecker(roll_size_mb=1)
        manager = roll_manager.WritingRollManager("test_%Y_%m_%d_%X_%f.events",
                                                  checker,
                                                  TEMPDIR,
                                                  archive_callback=callback)

        g = notigen.EventGenerator("test/integration/templates")
        entries = []
        now = datetime.datetime.utcnow()
        while len(entries) < 10000:
            events = g.generate(now)
            if events:
                for event in events:
                    metadata = {'event': event['event_type'],
                                'request_id': event['_context_request_id'],
                                'generated': str(event['timestamp']),
                                'uuid': event.get('payload', {}
                                                  ).get("instance_id", ""),
                                }
                    json_event = json.dumps(event,
                                        cls=notification_utils.DateTimeEncoder)
                    manager.write(metadata, json_event)
                    entries.append((metadata, json_event))

            now = g.move_to_next_tick(now)
        manager.close()

        for filename, is_open in callback.active_files.items():
            self.assertFalse(is_open)

        vcallback = VerifyArchiveCallback(callback.ordered_files)
        manager = roll_manager.ReadingRollManager("test_*.events",
                                                  TEMPDIR,
                                                  archive_callback=vcallback)

        while True:
            try:
                # By comparing the json'ed version of
                # the payloads we avoid all the issues
                # with unicode and datetime->decimal conversions.
                metadata, jpayload = manager.read()
                orig_metadata, orig_jpayload = entries.pop(0)
                self.assertEqual(orig_metadata, metadata)
                self.assertEqual(orig_jpayload, jpayload)
            except roll_manager.NoMoreFiles:
                break

        self.assertEqual(0, len(vcallback.original_files))
