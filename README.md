shoebox
=======

binary data archiving library - supports uploading to object storage

There are ArchiveReaders and ArchiveWriters which are managed
by RollManager. The RollManager opens and closes Archivers as
needed. "As needed" is determined by which RollChecker that was
passed into the RollManager. Archive files can roll over based
on file size or elapsed time (for writing). For reading, archive
files are only rolled over when the EOF is reached.

Roll Managers also take care of filename creation, compression
of completed archives and transfer of archive files to remote
storage locations.

TODO: How will the ReadingRollManager know which files to read
from, and in which order, if the filename is templated?
