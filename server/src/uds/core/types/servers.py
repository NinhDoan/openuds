# -*- coding: utf-8 -*-
#
# Copyright (c) 2023 Virtual Cable S.L.U.
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
import enum
import typing

from uds.core.util import singleton


class ServerType(enum.IntEnum):
    TUNNEL = 1
    ACTOR = 2
    SERVER = 3

    UNMANAGED = 100

    def as_str(self) -> str:
        return self.name.lower()  # type: ignore

    def path(self) -> str:
        return {
            ServerType.TUNNEL: 'tunnel',
            ServerType.ACTOR: 'actor',
            ServerType.SERVER: 'server',
            ServerType.UNMANAGED: '',  # Unmanaged has no path, does not listen to anything
        }[self]


class ServerSubType(metaclass=singleton.Singleton):
    class Info(typing.NamedTuple):
        type: ServerType
        subtype: str
        description: str
        managed: bool

    registered: typing.Dict[typing.Tuple[ServerType, str], Info]

    def __init__(self) -> None:
        self.registered = {}

    @staticmethod
    def manager() -> 'ServerSubType':
        return ServerSubType()

    def register(self, type: ServerType, subtype: str, description: str, managed: bool) -> None:
        self.registered[(type, subtype)] = ServerSubType.Info(
            type=type, subtype=subtype, description=description, managed=managed
        )

    def enum(self) -> typing.Iterable[Info]:
        return self.registered.values()

    def get(self, type: ServerType, subtype: str) -> typing.Optional[Info]:
        return self.registered.get((type, subtype))


# Registering default subtypes (basically, ip unmanaged is the "global" one), any other will be registered by the providers
# I.e. "linuxapp" will be registered by the Linux Applications Provider
ServerSubType.manager().register(ServerType.UNMANAGED, 'ip', 'Unmanaged IP Server', False)
