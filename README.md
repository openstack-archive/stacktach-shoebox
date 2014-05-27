shoebox
=======

binary data archiving library - supports uploading to object storage

Json payloads and string:string metadata dicts are stored in local-disk
binary files. The binary file format is versioned and tagged to allow
for easy extension. 

There are ArchiveReaders and ArchiveWriters which are managed
by the RollManager. "Roll" comes from "roll over". It controls when 
roll-over occurs from one Archive to the next. There is only one 
Archiver active at a time per RollManager. 

The RollManager opens and closes Archivers as
needed. "As needed" is determined by which RollChecker that was
passed into the RollManager. Archive files can roll over based
on file size or elapsed time (for writing). For reading, archive
files are only rolled over when the EOF is reached.

Roll Managers also take care of filename creation, compression
of completed archives and transfer of archive files to remote
storage locations.

The RollCheckers have a reference to the current Archive so
they can ask file-related questions (like "how big are you?")

You can register callbacks with the RollManager for notifications
on when new Archive files are opened or closed.

Important Note! The Callback handlers and the RollCheckers take
kwargs in the constructor since they can be dynamically loaded as
plugins. So, make sure you provide named parameters to the constructors. 

Usage:

    # Make a roll checker of whatever strategy you choose.
    checker = roll_checker.SizeRollChecker(roll_size_mb=100)  # 100mb files

    # Make a roll manager for reading or writing. 
    # Give the filename template and the checker. 
    # (and an optional working directory for new files)

    # The %c in the template is per the python strptime method: 
    # https://docs.python.org/2/library/datetime.html#strftime-strptime-behavior 

    x = roll_manager.WritingRollManager("test_%c.events", checker)

    # Write some metadata and payload ...
    #
    # WritingRollManager.write(metadata, payload) where
    # metadata = string:string dict
    # payload = string of data. Most likely a json structure.

    # If the archive file grows beyond 100mb the old one
    # will automatically close and a new one created.
    for index in range(10):
        x.write({"index": str(index)}, "payload_%d" % index)

    x.close()

For Reading:

    # Read from all the event data files using wildcards ...
    manager = roll_manager.ReadingRollManager("test_*.events")

    # This will keep reading across all files in the archive
    # until we reach the end.
    while True:
        try:
            metadata, json_payload = manager.read()
        except roll_manager.NoMoreFiles:
            break

Look at `test/integration/test_rolling.py` for a more complete example.
