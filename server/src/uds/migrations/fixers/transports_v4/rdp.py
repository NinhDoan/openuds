# -*- coding: utf-8 -*-
#
# Copyright (c) 2023 Virtual Cable S.L.U.
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without modification
# are permitted provided that the following conditions are met:
#
#    * Redistributions of source code must retain the above copyright notice
#      this list of conditions and the following disclaimer.
#    * Redistributions in binary form must reproduce the above copyright notice
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
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY
# OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
"""
Author: Adolfo Gómez, dkmaster at dkmon dot com
"""
import logging

from uds.core import consts, transports
from uds.core.ui import gui

from . import _migrator

logger = logging.getLogger(__name__)


# Copy for migration
class TRDPTransport(transports.Transport):
    """
    Provides access via RDP to service.
    This transport can use an domain. If username processed by authenticator contains '@', it will split it and left-@-part will be username, and right password
    """

    typeType = 'TSRDPTransport'

    tunnelServer = gui.TextField(label='')
    tunnelWait = gui.NumericField(label='', default=60)
    verifyCertificate = gui.CheckBoxField(label='', default=False)
    useEmptyCreds = gui.CheckBoxField(label='')
    fixedName = gui.TextField(label='')
    fixedPassword = gui.PasswordField(label='')
    withoutDomain = gui.CheckBoxField(label='')
    fixedDomain = gui.TextField(label='')
    allowSmartcards = gui.CheckBoxField(label='')
    allowPrinters = gui.CheckBoxField(label='')
    allowDrives = gui.ChoiceField(label='', default='false')
    enforceDrives = gui.TextField(label='')
    allowSerials = gui.CheckBoxField(label='')
    allowClipboard = gui.CheckBoxField(label='', default=True)
    allowAudio = gui.CheckBoxField(label='', default=True)
    allowWebcam = gui.CheckBoxField(label='', default=False)
    usbRedirection = gui.ChoiceField(label='', default='false')
    credssp = gui.CheckBoxField(label='', default=True)
    rdpPort = gui.NumericField(label='', default=3389)
    screenSize = gui.ChoiceField(label='', default='-1x-1')
    colorDepth = gui.ChoiceField(label='', default='24')
    wallpaper = gui.CheckBoxField(label='')
    multimon = gui.CheckBoxField(label='')
    aero = gui.CheckBoxField(label='')
    smooth = gui.CheckBoxField(label='', default=True)
    showConnectionBar = gui.CheckBoxField(label='', default=True)
    multimedia = gui.CheckBoxField(label='')
    alsa = gui.CheckBoxField(label='')
    printerString = gui.TextField(label='')
    smartcardString = gui.TextField(label='')
    customParameters = gui.TextField(label='')
    allowMacMSRDC = gui.CheckBoxField(label='', default=False)
    customParametersMAC = gui.TextField(label='')
    customParametersWindows = gui.TextField(label='')
    optimizeTeams = gui.CheckBoxField(label='')

    # This value is the new "tunnel server"
    # Old guacamoleserver value will be stored also on database, but will be ignored
    tunnel = gui.ChoiceField(label='')


def migrate(apps, schema_editor) -> None:
    _migrator.tunnel_transport(apps, TRDPTransport, 'tunnelServer', is_html_server=False)


def rollback(apps, schema_editor) -> None:
    _migrator.tunnel_transport_back(apps, TRDPTransport, 'tunnelServer', is_html_server=False)
