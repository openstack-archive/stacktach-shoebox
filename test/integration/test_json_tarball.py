import datetime
import hashlib
import json
import mock
import os
import shutil
import tarfile
import unittest

import notification_utils
import notigen

from shoebox import roll_manager


TEMPDIR = "test_temp"
DESTDIR = "test_temp/output"


class TestDirectory(unittest.TestCase):
    def setUp(self):
        shutil.rmtree(TEMPDIR, ignore_errors=True)
        shutil.rmtree(DESTDIR, ignore_errors=True)
        os.mkdir(TEMPDIR)
        os.mkdir(DESTDIR)

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
                    crc = hashlib.sha256(json_event).hexdigest()
                    entries[crc] = json_event

            now = g.move_to_next_tick(now)
        manager.close()

        # Confirm files and tarballs ...
        print "Starting entries:", len(entries)
        date_len = len("2015_02_24_14_15_58_037080_")
        num = 0
        for f in os.listdir(TEMPDIR):
            full = os.path.join(TEMPDIR, f)
            if os.path.isfile(full):
                crc = f[date_len:-len(".event")]
                del entries[crc]
                num += 1
        print "Untarred entries:", num, "Remaining:", len(entries)

        # the rest have to be in tarballs ...
        for f in os.listdir(DESTDIR):
            num = 0
            actual = 0
            tar = tarfile.open(os.path.join(DESTDIR, f), "r:gz")
            for tarinfo in tar:
                crc = tarinfo.name[len(TEMPDIR) + 1 + date_len:-len(".event")]
                actual += 1
                if crc:
                    del entries[crc]
                    num += 1

            if actual == 1:
                raise Exception("tarball has 1 entry. Something is wrong.")

            print "In %s: %d of %d Remaining: %d" % (f, num, actual,
                                                     len(entries))
            tar.close()

        if len(entries):
            raise Exception("%d more events than generated." % len(entries))
