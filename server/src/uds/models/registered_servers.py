# -*- coding: utf-8 -*-
#
# Copyright (c) 2012-2021 Virtual Cable S.L.U.
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
'''
Author: Adolfo Gómez, dkmaster at dkmon dot com
'''
import typing
import enum
import secrets

from uds.core.util.os_detector import KnownOS

from django.db import models
from uds.core.util.request import ExtendedHttpRequest

from .consts import MAX_DNS_NAME_LENGTH, MAX_IPV6_LENGTH

DEFAULT_LISTEN_PORT: typing.Final[int] = 43910


class RegisteredServers(models.Model):
    """
    UDS Registered Servers

    This table stores the information about registered servers for tunnel servers (on v3.6) or
    more recently, for other kind of servers that may be need to be registered (as app servers)

    kind field is a flag that indicates the kind of server that is registered. This is used to
    allow or deny access to the API for this server.
    Currently there are two kinds of servers:
    - Tunnel servers: This is the original use of this table, and is used to allow tunnel servers (1)
    - Other servers: This is used to register server that needs to access some API methods, but
        that are not tunnel servers (2)

    If server is Other, but not Tunnel, it will be allowed to access API, but will not be able to
    create tunnels.
    """

    class ServerType(enum.IntEnum):
        TUNNEL = 1
        ACTOR = 2
        APP_SERVER = 3
        OTHER = 99

        def as_str(self) -> str:
            return self.name.lower()  # type: ignore

        def path(self) -> str:
            return {
                RegisteredServers.ServerType.TUNNEL: 'tunnel',
                RegisteredServers.ServerType.ACTOR: 'actor',
                RegisteredServers.ServerType.APP_SERVER: 'app',
                RegisteredServers.ServerType.OTHER: 'other',
            }[self]

    MAC_UNKNOWN = '00:00:00:00:00:00'

    username = models.CharField(max_length=128)
    ip_from = models.CharField(max_length=MAX_IPV6_LENGTH)
    ip = models.CharField(max_length=MAX_IPV6_LENGTH)
    ip_version = models.IntegerField(default=4)  # 4 or 6, version of ip fields

    hostname = models.CharField(max_length=MAX_DNS_NAME_LENGTH)
    listen_port = models.IntegerField(
        default=DEFAULT_LISTEN_PORT
    )  # Port where server listens for connections (if it listens)

    token = models.CharField(max_length=48, db_index=True, unique=True)
    stamp = models.DateTimeField()  # Date creation or validation of this entry

    # Type of server. Defaults to tunnel, so we can migrate from previous versions
    # Note that a server can register itself several times, so we can have several entries
    # for the same server, but with different types.
    # (So, for example, an APP_SERVER can be also a TUNNEL_SERVER, because will use both APP API and TUNNEL API)
    kind = models.IntegerField(default=ServerType.TUNNEL.value)
    # os type of server (linux, windows, etc..)
    os_type = models.CharField(max_length=32, default=KnownOS.UNKNOWN.os_name())
    # mac address of registered server, if any. Important for VDI actor servers mainly, informative for others
    mac = models.CharField(max_length=32, default=MAC_UNKNOWN, db_index=True)

    # Extra data, for custom server type use (i.e. actor keeps command related data here)
    data = models.JSONField(null=True, blank=True, default=None)

    class Meta:  # pylint: disable=too-few-public-methods
        app_label = 'uds'

    @staticmethod
    def create_token() -> str:
        return secrets.token_urlsafe(36)

    @staticmethod
    def validateToken(
        token: str,
        serverType: typing.Union[typing.Iterable[ServerType], ServerType],
        request: typing.Optional[ExtendedHttpRequest] = None,
    ) -> bool:
        # Ensure tiken is composed of
        try:
            if isinstance(serverType, RegisteredServers.ServerType):
                tt = RegisteredServers.objects.get(token=token, kind=serverType.value)
            else:
                tt = RegisteredServers.objects.get(token=token, kind__in=[st.value for st in serverType])
            # We could check the request ip here
            if request and request.ip != tt.ip:
                raise Exception('Invalid ip')
            return True
        except RegisteredServers.DoesNotExist:
            pass
        return False

    @property
    def server_type(self) -> ServerType:
        return RegisteredServers.ServerType(self.kind)

    @server_type.setter
    def server_type(self, value: ServerType) -> None:
        self.kind = value.value

    def url(self, path: str, *, port: int = DEFAULT_LISTEN_PORT, secret: typing.Optional[str] = None) -> str:
        """
        Returns the url for a path to this server

        Args:
            path: Path to add to url
            port: Port to use (if not provided, default port will be used, that is
            secret: Secret to use (if not provided, token will be used)

        Returns:
            The url for the path

        Note:
            Currently, Actor urls are managed by the actor itself.
            This is so because every VDI actor has a different tocken, not registered here
            (This only registers "Master" actor, the descendants obtains a token from it)
            App Servers, future implementations of Tunnel and Other servers will use this method
            to obtain the url for the path.
            Currently, only App Servers uses this method. Tunnel servers does not expose any url.
        """
        if secret is None:
            secret = self.token  # If no custom secret, use token

        if secret:
            secret = '/' + secret

        if not path.startswith('/'):
            path = '/' + path

        path = f'/{self.server_type.path()}{secret}{path}'

        if self.ip_version == 4:
            return f'https://{self.ip}:{port}{path}'
        return f'https://[{self.ip}]:{port}{path}'

    def __str__(self):
        return f'<RegisterdServer {self.token} created on {self.stamp} by {self.username} from {self.ip}/{self.hostname}>'
