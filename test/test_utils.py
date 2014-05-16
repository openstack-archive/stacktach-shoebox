import datetime
import decimal
import unittest

import dateutil.tz

from shoebox import utils


class TestUtils(unittest.TestCase):
    def setUp(self):
        self.handler = utils.DateTimeEncoder()

    def test_handle_datetime_non_datetime(self):
        self.assertRaises(TypeError, self.handler.default, "text")

    def test_handle_datetime(self):
        now = datetime.datetime(day=1, month=2, year=2014,
                                hour=10, minute=11, second=12)
        self.assertEqual("1391249472", self.handler.default(now))

    def test_handle_datetime_offset(self):
        now = datetime.datetime(day=1, month=2, year=2014,
                                hour=10, minute=11, second=12,
                                tzinfo=dateutil.tz.tzoffset(None, 4*60*60))
        self.assertEqual("1391220672", self.handler.default(now))


class TestDatetimeToDecimal(unittest.TestCase):
    def test_datetime_to_decimal(self):
        expected_decimal = decimal.Decimal('1356093296.123')
        utc_datetime = datetime.datetime.utcfromtimestamp(expected_decimal)
        actual_decimal = utils.dt_to_decimal(utc_datetime)
        self.assertEqual(actual_decimal, expected_decimal)

    def test_decimal_to_datetime(self):
        expected_decimal = decimal.Decimal('1356093296.123')
        expected_datetime = datetime.datetime.utcfromtimestamp(expected_decimal)
        actual_datetime = utils.dt_from_decimal(expected_decimal)
        self.assertEqual(actual_datetime, expected_datetime)

    def test_dt_from_decimal_none(self):
        self.assertEqual("n/a", utils.dt_from_decimal(None))
