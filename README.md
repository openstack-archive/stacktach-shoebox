shoebox
=======

binary data archiving library - supports uploading to object storage

There are ArchiveReaders and ArchiveWriters which are managed
by RollManager. "Roll" comes from "roll over". When does a file roll-over
from one to the next? There is only one Archiver active at a time. 

The RollManager opens and closes Archivers as
needed. "As needed" is determined by which RollChecker that was
passed into the RollManager. Archive files can roll over based
on file size or elapsed time (for writing). For reading, archive
files are only rolled over when the EOF is reached.

Roll Managers also take care of filename creation, compression
of completed archives and transfer of archive files to remote
storage locations.

The RollChecker's have a reference to the current Archive so
they can ask file-related questions (like "how big are you?")

Usage:

    # Make a roll checker of whatever strategy you choose.
    checker = roll_checker.NeverRollChecker()  # one big file.
    # Make a roll manager for reading or writing. 
    # Give the filename template and the checker. 
    # (and an optional working directory for new files)
    x = roll_manager.WritingRollManager("template_%s", checker)
    # Write metadata and payload ...
    for index in range(10):
        x.write({"index": str(index)}, "payload_%d" % index)
    # WritingRollManager.write(metadata, payload) where
    # metadata = string:string dict
    # payload = string of data. Most likely a json structure.

TODO: How will the ReadingRollManager know which files to read
from, and in which order, if the filename is templated?
