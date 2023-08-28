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

from django.utils.translation import gettext as _

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

    @staticmethod
    def enumerate() -> typing.List[typing.Tuple[int, str]]:
        return [
            (ServerType.TUNNEL, _('Tunnel')),
            (ServerType.ACTOR, _('Actor')),
            (ServerType.SERVER, _('Server')),
            (ServerType.UNMANAGED, _('Unmanaged')),
        ]


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
# The main usage of this subtypes is to allow to group servers by type, and to allow to filter by type
ServerSubType.manager().register(ServerType.UNMANAGED, 'ip', 'Unmanaged IP Server', False)


class ServerStatsType(typing.NamedTuple):
    memused: int = 1  # In bytes
    memtotal: int = 1  # In bytes
    cpuused: float = 0  # 0-1 (cpu usage)
    uptime: int = 0  # In seconds
    disks: typing.List[typing.Tuple[str, int, int]] = []  # List of tuples (name, used, total)
    connections: int = 0  # Number of connections
    current_users: int = 0  # Number of current users
    
    @property
    def cpufree_ratio(self) -> float:
        return (1 - self.cpuused) / (self.current_users + 1)
    
    @property
    def memfree_ratio(self) -> float:
        return (self.memtotal - self.memused) / (self.memtotal or 1) / (self.current_users + 1)
        

    def weight(self, minMemory: int = 0) -> float:
        # Weights are calculated as:
        # 0.5 * cpu_usage + 0.5 * (1 - mem_free / mem_total) / (current_users + 1)
        # +1 is because this weights the connection of current users + new user
        # Dividing by number of users + 1 gives us a "ratio" of available resources per user when a new user is added
        # Also note that +512 forces that if mem_free is less than 512 MB, this server will be put at the end of the list
        if self.memtotal - self.memused < minMemory:
            return 1000000000  # At the end of the list

        # Higher weight is worse
        return 1 / ((self.cpufree_ratio * 1.3 + self.memfree_ratio) or 1)

    @staticmethod
    def fromDict(dct: typing.Dict[str, typing.Any]) -> 'ServerStatsType':
        disks: typing.List[typing.Tuple[str, int, int]] = []
        for disk in dct.get('disks', []):
            disks.append((disk['name'], disk['used'], disk['total']))
        return ServerStatsType(
            memused=dct.get('memused', 1),
            memtotal=dct.get('memtotal', dct.get('mem_free', 1)),  # Avoid division by zero
            cpuused=dct.get('cpuused', 0),
            uptime=dct.get('uptime', 0),
            disks=disks,
            connections=dct.get('connections', 0),
            current_users=dct.get('current_users', 0),
        )

    @staticmethod
    def empty() -> 'ServerStatsType':
        return ServerStatsType()

    def __str__(self) -> str:
        # Human readable
        return f'memory: {self.memused//(1024*1024)}/{self.memtotal//(1024*1024)} cpu: {self.cpuused*100} users: {self.current_users}, weight: {self.weight()}'

class ServerCounterType(typing.NamedTuple):
    server_uuid: str
    counter: int
    
    @staticmethod
    def fromIterable(data: typing.Optional[typing.Iterable]) -> typing.Optional['ServerCounterType']:
        if data is None:
            return None
        return ServerCounterType(*data)

    @staticmethod
    def empty() -> 'ServerCounterType':
        return ServerCounterType('', 0)
