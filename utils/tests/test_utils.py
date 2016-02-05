# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals

import unittest

from binascii import hexlify
from datetime import datetime

import pytz

from woodbox.utils.time import strptime_iso8601
from woodbox.utils.pbkdf2_hmac import pbkdf2_hmac

class TestUtils(unittest.TestCase):
    def test_strptime_iso8601(self):
        tests = [
            ('20101231T142342Z', datetime(2010, 12, 31, 14, 23, 42)),
            ('20101231T142342-0500', datetime(2010, 12, 31, 19, 23, 42)),
            ('20101231T142342+0100', datetime(2010, 12, 31, 13, 23, 42)),
            ('20101231T232342-0500', datetime(2011, 1, 1, 4, 23, 42)),
            ('20101231T002342+0100', datetime(2010, 12, 30, 23, 23, 42))
        ]

        for t in tests:
            self.assertEqual(strptime_iso8601(t[0]), pytz.utc.localize(t[1]))

    def test_pbkdf2_hmac(self):
        tests = [
            (b'some_password', b'saltandpepper', b'1fa4e2cb077cc58d23d8e4305f23defa08e604383209c4ea5e3c0ea2181a0984'),
            (b'', b'saltandpepper', b'6b4c38d3924037d31040ed69c5c81929d53050384d8a397e4244b7ad9ce7d504'),
            (b'some_password', b'', b'44005d745bca7f729a5bb19b2e6c91b2f3c6b042b909c81ed55e599494538426'),
            (b'', b'', b'c99414a1b4fa88584cfc65040e69e06a007aa0017409a30c28a109581e717082'),
        ]

        for t in tests:
            r = hexlify(pbkdf2_hmac(str('sha256'), t[0], t[1], 100))
            self.assertEqual(r, t[2])
