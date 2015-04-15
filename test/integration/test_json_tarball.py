import datetime
import gzip
import hashlib
import json
import mock
import os
import shutil
import unittest

import notification_utils
import notigen

from shoebox import roll_manager


TEMPDIR = "test_temp/working"
DESTDIR = "test_temp/output"
EXTRACTDIR = "test_temp/extract"


class TestDirectory(unittest.TestCase):
    def setUp(self):
        for d in [TEMPDIR, DESTDIR, EXTRACTDIR]:
            shutil.rmtree(d, ignore_errors=True)
            os.mkdir(d)

    def test_size_rolling(self):
        manager = roll_manager.WritingJSONRollManager(
                                    "%Y_%m_%d_%X_%f_[[CRC]].event",
                                    directory=TEMPDIR,
                                    destination_directory=DESTDIR,
                                    roll_size_mb=10)

        g = notigen.EventGenerator("test/integration/templates")
        entries = {}
        now = datetime.datetime.utcnow()
        while len(entries) < 10000:
            events = g.generate(now)
            if events:
                for event in events:
                    metadata = {}
                    json_event = json.dumps(event,
                                        cls=notification_utils.DateTimeEncoder)
                    manager.write(metadata, json_event)
                    msg_id = event['message_id']
                    entries[msg_id] = json_event

            now = g.move_to_next_tick(now)
        manager.close()
        manager._archive_working_files()

        print "Starting entries:", len(entries)

        actual = len(entries)

        # Confirm there's nothing in working directory ...
        for f in os.listdir(TEMPDIR):
            full = os.path.join(TEMPDIR, f)
            if os.path.isfile(full):
                self.fail("Working directory not empty.")

        # Read the gzip files ...
        total = 0
        for f in os.listdir(DESTDIR):
            archive = gzip.open(os.path.join(DESTDIR, f), 'rb')
            file_content = archive.read().split('\n')
            archive.close()

            num = len(file_content) - 1
            total += num
            print "In %s: %d of %d Remaining: %d" % (f, num, actual,
                                                     actual - total)

        if actual != total:
            raise Exception("Num generated != actual")
