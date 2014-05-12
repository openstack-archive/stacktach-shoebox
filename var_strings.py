import calendar
import datetime
import json
import struct

event = {"event_type": "nova.compute.run_instance.start",
         "generated": datetime.datetime.utcnow(),
         "request_id": "req-1234abcd5678efgh",
         "source": "n-compute-1973",
         "payload": {
            "foo": 123,
            "blah": "abc",
            "zoo": False
         }
        }


def handle_datetime(obj):
    if isinstance(obj, datetime.datetime):
        if obj.utcoffset() is not None:
            obj = obj - obj.utcoffset()
    millis = int(
        calendar.timegm(obj.timetuple()) * 1000 +
        obj.microsecond / 1000
    )
    return millis


json_event = json.dumps(event, default=handle_datetime)
metadata = {'request_id': event['request_id'],
            'event_type': event['event_type'],
            'source': event['source'],
           }

CURRENT_VERSION = 1

# Version 1 SCHEMA
# ----------------
# i = 0x69867884  (EVNT)
# h = version
# i = metadata block length
# i = raw notification block length
# i = 0x00000000 EOR

# Metadata block
# i = number of strings
# [i, i] = length of key, length of value
# [*s, *s] = key, value

# Raw notification block
# *s = raw data

raw_block_schema = "%ds" % len(json_event)
raw_block = struct.pack(raw_block_schema, json_event)

metadata_items = ["i"] # appended with N "%ds"'s
metadata_values = [len(metadata) * 4]  # [n]=key, [n+1]=value
for key, value in metadata.iteritems():
    metadata_items.append("i")
    metadata_items.append("i")
    metadata_values.append(len(key))
    metadata_values.append(len(value))

for key, value in metadata.iteritems():
    metadata_items.append("%ds" % len(key))
    metadata_values.append(key)
    metadata_items.append("%ds" % len(value))
    metadata_values.append(value)
metadata_schema = "".join(metadata_items)

metadata = struct.pack(metadata_schema, *metadata_values)

header_schema = "ihiii"
header_size = struct.calcsize(header_schema)
header = struct.pack(header_schema, 0x69867884, CURRENT_VERSION,
                     struct.calcsize(metadata_schema),
                     struct.calcsize(raw_block_schema), 0)

with open("test.dat", "wb") as f:
    f.write(header)
    f.write(metadata)
    f.write(raw_block)

with open("test.dat", "rb") as f:
    header = f.read(header_size)
    header = struct.unpack(header_schema, header)
    print "Marker:", hex(header[0])
    print "Version:", header[1]
    print "Metadata length:", header[2]
    print "Raw notification:", header[3]
    print "EOR:", header[4]

    metadata = f.read(header[2])
    num_strings = struct.unpack_from("i", metadata)
    print "Num metadata strings:", num_strings
    offset = struct.calcsize("i")
    lengths = num_strings[0] / 2
    lengths_schema = "i" * lengths
    print "Lengths schema:", lengths_schema
    key_value_sizes = struct.unpack_from(lengths_schema, metadata,
                                         offset=offset)
    key_value_schema_list = ["%ds" % sz for sz in key_value_sizes]
    key_value_schema = "".join(key_value_schema_list)
    offset += struct.calcsize(lengths_schema)
    key_values = struct.unpack_from(key_value_schema, metadata,
                                    offset=offset)
    metadata_dict = dict((key_values[n], key_values[n+1])
                         for n in range(len(key_values))[::2])

    print "Key Value schema:", key_value_schema
    print "Metadata:", metadata_dict
