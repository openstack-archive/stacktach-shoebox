# Copyright (c) 2014 Dark Secret Software Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import calendar
import collections
import datetime
import decimal
import json


def now():
    """Broken out for testing."""
    return datetime.datetime.utcnow()


def dt_to_decimal(utc):
    decimal.getcontext().prec = 30
    return decimal.Decimal(str(calendar.timegm(utc.utctimetuple()))) + \
           (decimal.Decimal(str(utc.microsecond)) /
           decimal.Decimal("1000000.0"))


def dt_from_decimal(dec):
    if dec == None:
        return "n/a"
    integer = int(dec)
    micro = (dec - decimal.Decimal(integer)) * decimal.Decimal(1000000)

    daittyme = datetime.datetime.utcfromtimestamp(integer)
    return daittyme.replace(microsecond=micro)


class DateTimeEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime.datetime):
            if obj.utcoffset() is not None:
                obj = obj - obj.utcoffset()
            return str(dt_to_decimal(obj))
        return super(DateTimeEncoder, self).default(obj)


# This is a hack for comparing structures load'ed from json
# (which are always unicode) back to strings. It's used
# for assertEqual() in the tests and is very slow and expensive.
def unicode_to_string(data):
    if isinstance(data, basestring):
        return str(data)
    elif isinstance(data, collections.Mapping):
        return dict(map(unicode_to_string, data.iteritems()))
    elif isinstance(data, collections.Iterable):
        return type(data)(map(unicode_to_string, data))
    else:
        return data
