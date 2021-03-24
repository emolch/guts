# http://pyrocko.org - GPLv3
#
# The Pyrocko Developers, 21st Century
# ---|P------/S----------~Lg----------
"""Utility functions for guts."""

import time
import re
import calendar

import numpy as num


class TimeStrError(Exception):
    pass


class FractionalSecondsMissing(TimeStrError):
    """
    Exception raised by :py:func:`str_to_time` when the given string lacks
    fractional seconds.
    """

    pass


class FractionalSecondsWrongNumberOfDigits(TimeStrError):
    """
    Exception raised by :py:func:`str_to_time` when the given string has an
    incorrect number of digits in the fractional seconds part.
    """

    pass


class GlobalVars(object):
    re_frac = None


def _endswith_n(s, endings):
    for ix, x in enumerate(endings):
        if s.endswith(x):
            return ix
    return -1


def str_to_time(s, format='%Y-%m-%d %H:%M:%S.OPTFRAC'):
    """
    Convert string representing UTC time to floating point system time.

    :param s: string representing UTC time
    :param format: time string format
    :returns: system time stamp as floating point value

    Uses the semantics of :py:func:`time.strptime` but allows for fractional
    seconds. If the format ends with ``'.FRAC'``, anything after a dot is
    interpreted as fractional seconds. If the format ends with ``'.OPTFRAC'``,
    the fractional part, including the dot is made optional. The latter has the
    consequence, that the time strings and the format may not contain any other
    dots. If the format ends with ``'.xFRAC'`` where x is 1, 2, or 3, it is
    ensured, that exactly that number of digits are present in the fractional
    seconds.
    """

    fracsec = 0.
    fixed_endings = '.FRAC', '.1FRAC', '.2FRAC', '.3FRAC'

    iend = _endswith_n(format, fixed_endings)
    if iend != -1:
        dotpos = s.rfind('.')
        if dotpos == -1:
            raise FractionalSecondsMissing(
                'string=%s, format=%s' % (s, format))

        if iend > 0 and iend != (len(s)-dotpos-1):
            raise FractionalSecondsWrongNumberOfDigits(
                'string=%s, format=%s' % (s, format))

        format = format[:-len(fixed_endings[iend])]
        fracsec = float(s[dotpos:])
        s = s[:dotpos]

    elif format.endswith('.OPTFRAC'):
        dotpos = s.rfind('.')
        format = format[:-8]
        if dotpos != -1 and len(s[dotpos:]) > 1:
            fracsec = float(s[dotpos:])

        if dotpos != -1:
            s = s[:dotpos]

    try:
        return calendar.timegm(time.strptime(s, format)) + fracsec
    except ValueError as e:
        raise TimeStrError('%s, string=%s, format=%s' % (str(e), s, format))


stt = str_to_time


def time_to_str(t, format='%Y-%m-%d %H:%M:%S.3FRAC'):
    """
    Get string representation for floating point system time.

    :param t: floating point system time
    :param format: time string format
    :returns: string representing UTC time

    Uses the semantics of :py:func:`time.strftime` but additionally allows for
    fractional seconds. If ``format`` contains ``'.xFRAC'``, where ``x`` is a
    digit between 1 and 9, this is replaced with the fractional part of ``t``
    with ``x`` digits precision.
    """

    if isinstance(format, int):
        if format > 0:
            format = '%Y-%m-%d %H:%M:%S.' + '%iFRAC' % format
        else:
            format = '%Y-%m-%d %H:%M:%S'

    if not GlobalVars.re_frac:
        GlobalVars.re_frac = re.compile(r'\.[1-9]FRAC')
        GlobalVars.frac_formats = dict(
            [('.%sFRAC' % x, '%.'+x+'f') for x in '123456789'])

    ts = float(num.floor(t))
    tfrac = t-ts

    m = GlobalVars.re_frac.search(format)
    if m:
        sfrac = (GlobalVars.frac_formats[m.group(0)] % tfrac)
        if sfrac[0] == '1':
            ts += 1.

        format, nsub = GlobalVars.re_frac.subn(sfrac[1:], format, 1)

    return time.strftime(format, time.gmtime(ts))


tts = time_to_str
