# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals

from datetime import datetime, timedelta

import pytz

def strptime_iso8601(timestamp):
    """Convert a ISO8601 date string to a UTC datetime.

    The string must be in ISO8601 basic format (no hypen or colon
    between each part).

    The timestamp must include the seconds; the conversion drops
    seconds fractions, if any.

    """
    dt = datetime.strptime(timestamp[:15], '%Y%m%dT%H%M%S')
    dt = pytz.utc.localize(dt)
    tz = timestamp[15:]
    if tz and tz != 'Z':
        # Apply the inverse timezone correction to get UTC time.
        sign = tz[0]
        hours = tz[1:3]
        minutes = tz[3:] or '00'
        delta = timedelta(hours=int(hours),minutes=int(minutes))
        if sign == '+':
            dt -= delta
        else:
            dt += delta

    return dt


if __name__ == "__main__":
    tests = ['20101231T142342Z', '20101231T142342-0500',
             '20101231T142342+0100', '20101231T232342-0500',
             '20101231T002342+0100']

    for t in tests:
        print(t, strptime_iso8601(t))
