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
#      and/or other materials provided with the distribution
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
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY
# OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

"""
@author: Adolfo Gómez, dkmaster at dkmon dot com
"""
import logging
import typing
from django.db import models

from django.utils.translation import gettext
from django.utils.translation import gettext_lazy as _

import uds.core.types.permissions
from uds.core import types, consts, ui
from uds.core.util import permissions, validators
from uds.core.util.model import processUuid
from uds.models import Server, ServerGroup
from uds.REST.model import DetailHandler, ModelHandler

# Not imported at runtime, just for type checking
if typing.TYPE_CHECKING:
    from django.db import models

    from uds.core.module import Module

logger = logging.getLogger(__name__)


class TunnelServers(DetailHandler):
    # tunnels/[id]/servers
    custom_methods = ['maintenance']

    def getItems(self, parent: 'ServerGroup', item: typing.Optional[str]):
        try:
            multi = False
            if item is None:
                multi = True
                q = parent.servers.all().order_by('hostname')
            else:
                q = parent.servers.filter(uuid=processUuid(item))
            res = []
            i = None
            for i in q:
                val = {
                    'id': i.uuid,
                    'hostname': i.hostname,
                    'ip': i.ip,
                    'mac': i.mac if not multi or i.mac != consts.MAC_UNKNOWN else '',
                    'maintenance': i.maintenance_mode,
                }
                res.append(val)
            if multi:
                return res
            if not i:
                raise Exception('Item not found')
            return res[0]
        except Exception as e:
            logger.exception('REST groups')
            raise self.invalidItemException() from e

    def getTitle(self, parent: 'ServerGroup') -> str:
        try:
            return _('Servers of {0}').format(parent.name)
        except Exception:
            return _('Servers')

    def getFields(self, parent: 'ServerGroup') -> typing.List[typing.Any]:
        return [
            {
                'hostname': {
                    'title': _('Hostname'),
                }
            },
            {'ip': {'title': _('Ip')}},
            {'mac': {'title': _('Mac')}},
            {
                'maintenance_mode': {
                    'title': _('State'),
                    'type': 'dict',
                    'dict': {True: _('Maintenance'), False: _('Normal')},
                }
            },
        ]

    def getRowStyle(self, parent: 'ServerGroup') -> typing.Dict[str, typing.Any]:
        return {'field': 'maintenance_mode', 'prefix': 'row-maintenance-'}

    # Cannot save a tunnel server, it's not editable...

    def deleteItem(self, parent: 'ServerGroup', item: str) -> None:
        try:
            parent.servers.remove(Server.objects.get(uuid=processUuid(item)))
        except Exception:
            raise self.invalidItemException() from None

    # Custom methods
    def maintenance(self, parent: 'ServerGroup', id: str) -> typing.Any:
        """
        Custom method that swaps maintenance mode state for a tunnel server
        :param item:
        """
        item = Server.objects.get(uuid=processUuid(id))
        self.ensureAccess(item, uds.core.types.permissions.PermissionType.MANAGEMENT)
        item.maintenance_mode = not item.maintenance_mode
        item.save()
        return 'ok'


# Enclosed methods under /auth path
class Tunnels(ModelHandler):
    path = 'tunnels'
    name = 'tunnels'
    model = ServerGroup
    model_filter = {'type': types.servers.ServerType.TUNNEL}
    custom_methods = [
        types.rest.ModelCustomMethodType('tunnels', needs_parent=True),
        types.rest.ModelCustomMethodType('assign', needs_parent=True),
    ]

    detail = {'servers': TunnelServers}
    save_fields = ['name', 'comments', 'host:', 'port:0']

    table_title = _('Tunnels')
    table_fields = [
        {'name': {'title': _('Name'), 'visible': True, 'type': 'iconType'}},
        {'comments': {'title': _('Comments')}},
        {'host': {'title': _('Host')}},
        {'port': {'title': _('Port')}},
        {'servers_count': {'title': _('Servers'), 'type': 'numeric', 'width': '1rem'}},
        {'tags': {'title': _('tags'), 'visible': False}},
    ]

    def getGui(self, type_: str) -> typing.List[typing.Any]:
        return self.addField(
            self.addDefaultFields(
                [],
                ['name', 'comments', 'tags'],
            ),
            [
                {
                    'name': 'host',
                    'value': '',
                    'label': gettext('Hostname'),
                    'tooltip': gettext(
                        'Hostname or IP address of the server where the tunnel is visible by the users'
                    ),
                    'type': types.ui.FieldType.TEXT,
                    'order': 100,  # At end
                },
                {
                    'name': 'port',
                    'value': 443,
                    'label': gettext('Port'),
                    'tooltip': gettext('Port where the tunnel is visible by the users'),
                    'type': types.ui.FieldType.NUMERIC,
                    'order': 101,  # At end
                },
            ],
        )

    def item_as_dict(self, item: 'ServerGroup') -> typing.Dict[str, typing.Any]:
        return {
            'id': item.uuid,
            'name': item.name,
            'comments': item.comments,
            'host': item.host,
            'port': item.port,
            'tags': [tag.tag for tag in item.tags.all()],
            'transports_count': item.transports.count(),
            'servers_count': item.servers.count(),
            'permission': permissions.getEffectivePermission(self._user, item),
        }

    def beforeSave(self, fields: typing.Dict[str, typing.Any]) -> None:
        fields['type'] = types.servers.ServerType.TUNNEL.value
        fields['port'] = int(fields['port'])
        # Ensure host is a valid IP(4 or 6) or hostname
        validators.validateHost(fields['host'])

    def assign(self, parent: 'ServerGroup') -> typing.Any:
        self.ensureAccess(parent, uds.core.types.permissions.PermissionType.MANAGEMENT)

        server: typing.Optional['Server'] = None  # Avoid warning on reference before assignment

        item = self._args[-1]

        if item is None:
            raise self.invalidItemException('No server specified')

        try:
            server = Server.objects.get(uuid=processUuid(item))
            self.ensureAccess(server, uds.core.types.permissions.PermissionType.READ)
            parent.servers.add(server)
        except Exception:
            raise self.invalidItemException() from None

        # TODO: implement this
        return 'ok'

    def tunnels(self, parent: 'ServerGroup') -> typing.Any:
        """
        Custom method that returns all tunnels of a tunnel server NOT already assigned to a group
        :param item:
        """
        allServers = set(parent.servers.all())
        return [
            {
                'id': i.uuid,
                'name': i.hostname,
            }
            for i in Server.objects.filter(type=types.servers.ServerType.TUNNEL)
            if permissions.getEffectivePermission(self._user, i)
            >= uds.core.types.permissions.PermissionType.READ
            and i not in allServers
        ]
