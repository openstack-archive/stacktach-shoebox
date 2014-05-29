import calendar
import datetime
import json
import struct


class InvalidVersion(Exception):
    pass


class OutOfSync(Exception):
    pass


class EndOfFile(Exception):
    pass


BOR_MAGIC_NUMBER = 0x69867884


class Version0(object):
    # Preamble ... same for all versions.
    # i = 0x69867884  (EVNT)
    # h = version

    def __init__(self):
        self.preamble_schema = "ih"
        self.preamble_size = struct.calcsize(self.preamble_schema)

    def make_preamble(self, version):
        return struct.pack(self.preamble_schema, BOR_MAGIC_NUMBER, version)

    def _check_eof(self, expected, actual):
        if actual < expected:
            raise EndOfFile()

    def load_preamble(self, file_handle):
        raw = file_handle.read(self.preamble_size)
        self._check_eof(self.preamble_size, len(raw))
        header = struct.unpack(self.preamble_schema, raw)
        if header[0] != BOR_MAGIC_NUMBER:
            raise OutOfSync("Expected Beginning of Record marker")
        return header[1]


class Version1(Version0):
    # Version 1 SCHEMA
    # ----------------
    # i = metadata block length
    # i = raw notification block length
    # i = 0x00000000 EOR

    # Metadata dict block
    # i = number of strings (N) - key/value = 2 strings
    # N * i = length of key followed by length of value
    # N * (*s) = key followed by value

    # Raw notification block
    # i = length of raw data block
    # *s = raw data

    # EXAMPLE
    #--------
    # With above Event and Metadata
    #
    # Header schema: "iii"
    # Metadata length: 119
    # Raw notification length: 201
    # Metadata = 6 strings (3 key-value pairs)
    # Metadata schema: "iiiiiii6s14s10s31s10s20s"
    #                                     ------ key/value
    #                               ------ key/value
    #                          ----- key/value
    #                    ------ length of the 6 strings
    #                   - 12 entries (6 string sizes + 6 strings)
    # Raw notification: "i197s"
    #                     ---- json notification
    #                    - 197

    def __init__(self):
        super(Version1, self).__init__()
        self.header_schema = "iii"
        self.header_size = struct.calcsize(self.header_schema)

    def _encode(self, s):
         if isinstance(s, unicode):
            return s.encode('utf-8')
         return s

    def pack(self, notification, metadata):
        nsize = len(notification)
        raw_block_schema = "i%ds" % nsize
        raw_block = struct.pack(raw_block_schema, nsize, notification)

        metadata_items = ["i"] # appended with N "%ds"'s
        metadata_values = [len(metadata) * 4]  # [n]=key, [n+1]=value
        for key, value in metadata.iteritems():
            key = self._encode(key)
            value = self._encode(value)
            metadata_items.append("i")
            metadata_items.append("i")
            metadata_values.append(len(key))
            metadata_values.append(len(value))

        for key, value in metadata.iteritems():
            key = self._encode(key)
            value = self._encode(value)
            metadata_items.append("%ds" % len(key))
            metadata_values.append(key)
            metadata_items.append("%ds" % len(value))
            metadata_values.append(value)
        metadata_schema = "".join(metadata_items)

        metadata = struct.pack(metadata_schema, *metadata_values)

        header = struct.pack(self.header_schema,
                             struct.calcsize(metadata_schema),
                             struct.calcsize(raw_block_schema), 0)

        preamble = self.make_preamble(1)
        return (preamble, header, metadata, raw_block)

    def unpack(self, file_handle):
        header_bytes = file_handle.read(self.header_size)
        self._check_eof(self.header_size, len(header_bytes))
        header = struct.unpack(self.header_schema, header_bytes)

        if header[2] != 0:
            raise OutOfSync("Didn't find 0 EOR marker.")

        metadata_bytes = file_handle.read(header[0])
        self._check_eof(header[0], len(metadata_bytes))
        num_strings = struct.unpack_from("i", metadata_bytes)
        offset = struct.calcsize("i")
        lengths = num_strings[0] / 2
        lengths_schema = "i" * lengths
        key_value_sizes = struct.unpack_from(lengths_schema, metadata_bytes,
                                             offset=offset)
        key_value_schema_list = ["%ds" % sz for sz in key_value_sizes]
        key_value_schema = "".join(key_value_schema_list)
        offset += struct.calcsize(lengths_schema)
        key_values = struct.unpack_from(key_value_schema, metadata_bytes,
                                        offset=offset)
        metadata = dict((key_values[n], key_values[n+1])
                        for n in range(len(key_values))[::2])

        raw = file_handle.read(header[1])
        self._check_eof(header[1], len(raw))
        raw_len = struct.unpack_from("i", raw)
        offset = struct.calcsize("i")
        jnot = struct.unpack_from("%ds" % raw_len[0], raw, offset=offset)
        return (metadata, jnot[0])


VERSIONS = {1: Version1()}
CURRENT_VERSION = 1

def get_version_handler(version=CURRENT_VERSION):
    global VERSIONS

    version_handler = VERSIONS.get(version)
    if not version_handler:
        raise InvalidVersion()
    return version_handler


def pack_notification(notification, metadata, version=CURRENT_VERSION):
    version_handler = get_version_handler(version)
    return version_handler.pack(notification, metadata)


def unpack_notification(file_handle):
    v0 = Version0()
    version = v0.load_preamble(file_handle)
    version_handler = get_version_handler(version)
    return version_handler.unpack(file_handle)
