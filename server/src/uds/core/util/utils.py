# -*- coding: utf-8 -*-

#
# Copyright (c) 2012-2022 Virtual Cable S.L.U.
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without modification,
# are permitted provided that the following conditions are met:
#
#    * Redistributions of source code must retain the above copyright notice,
#      this list of conditions and the following disclaimer.
#    * Redistributions in binary form must reproduce the above copyright notice,
#      this list of conditions and the following disclaimer in the documentation
#      and/or other materials provided with the distribution.
#    * Neither the name of Virtual Cable S.L.U. nor the names of its contributors
#      may be used to endorse or promote products derived from this software
#      without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
# FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
# SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
# OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

"""
Author: Adolfo Gómez, dkmaster at dkmon dot com
"""
import sys
import os
import datetime
import unicodedata
import typing
import contextlib

from django.utils import formats
from django.utils.translation import gettext
import django.template.defaultfilters as filters


class CaseInsensitiveDict(dict):
    @classmethod
    def _k(cls, key):
        return key.lower() if isinstance(key, str) else key

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._convert_keys()

    def __getitem__(self, key):
        return super().__getitem__(self.__class__._k(key))

    def __setitem__(self, key, value):
        super().__setitem__(self.__class__._k(key), value)

    def __delitem__(self, key):
        return super().__delitem__(self.__class__._k(key))

    def __contains__(self, key):
        return super().__contains__(self.__class__._k(key))

    def pop(self, key, *args, **kwargs):
        return super().pop(
            self.__class__._k(key), *args, **kwargs  # pylint: disable=protected-access
        )

    def get(self, key, *args, **kwargs):
        return super().get(
            self.__class__._k(key), *args, **kwargs  # pylint: disable=protected-access
        )

    def setdefault(self, key, *args, **kwargs):
        return super().setdefault(
            self.__class__._k(key), *args, **kwargs  # pylint: disable=protected-access
        )

    def update(self, E=None, **F):
        if E is None:
            E = {}
        super().update(self.__class__(E))
        super().update(self.__class__(**F))

    def _convert_keys(self):
        for k in list(self.keys()):
            v = super().pop(k)
            self.__setitem__(k, v)  # pylint: disable=unnecessary-dunder-call


def as_list(value: typing.Any) -> typing.List[typing.Any]:
    """If value is not a list, returns a list with value as only element

    Args:
        value (typing.Any): Value to convert to list

    Returns:
        typing.List[typing.Any]: List with value as only element
    """
    if isinstance(value, (bytes, str, int, float)):
        return [value]
    try:
        return list(value)
    except Exception:
        return [value]


def package_relative_file(moduleName: str, fileName: str) -> str:
    """
    Helper to get image path from relative to a module.
    This allows to keep images alongside report
    """
    mod = sys.modules[moduleName]
    if mod and hasattr(mod, '__file__') and mod.__file__:
        pkgpath = os.path.dirname(mod.__file__)
        return os.path.join(pkgpath, fileName)
    # Not found, return fileName
    return fileName


def timestampAsStr(stamp, format_='SHORT_DATETIME_FORMAT'):
    """
    Converts a timestamp to date string using specified format (DJANGO format such us SHORT_DATETIME_FORMAT..)
    """
    format_ = formats.get_format(format_)
    return filters.date(datetime.datetime.fromtimestamp(stamp), format_)


def secondsToTimeString(seconds: int) -> str:
    seconds = int(seconds)
    minutes = seconds // 60
    seconds %= 60
    hours = minutes // 60
    minutes %= 60
    days = hours // 24
    hours %= 24
    return gettext('{} days {:d}:{:02d}:{:02d}').format(days, hours, minutes, seconds)


def removeControlCharacters(s: str) -> str:
    """
    Removes control characters from an unicode string

    Arguments:
        s {str} -- string to remove control characters from

    Returns:
        str -- string without control characters
    """
    return ''.join(ch for ch in s if unicodedata.category(ch)[0] != "C")


@contextlib.contextmanager
def ignoreExceptions():
    """
    Ignores exceptions of type exceptions
    """
    try:
        yield
    except Exception:  # nosec: want to catch all exceptions
        pass
    