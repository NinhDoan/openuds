# -*- coding: utf-8 -*-

#
# Copyright (c) 2022 Virtual Cable S.L.U.
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
@author: Adolfo Gómez, dkmaster at dkmon dot com
"""
import datetime
import random
import typing

from django.utils.translation import ugettext_noop as _
from uds.models import getSqlDatetime
from uds.core import Module
from uds.core.auths import exceptions

if typing.TYPE_CHECKING:
    from uds.core.environment import Environment


class MFA(Module):
    """
    this class provides an abstraction of a notifier system for administrator defined events
    This class will be responsible os sendig emails, messaging notifications, etc.. to administrators
    """

    # informational related data
    # : Name of type, used at administration interface to identify this
    # : notifier type (e.g. "Email", "SMS", etc.)
    # : This string will be translated when provided to admin interface
    # : using gettext, so you can mark it as "_" at derived classes (using gettext_noop)
    # : if you want so it can be translated.
    typeName: typing.ClassVar[str] = _('Base MFA')

    # : Name of type used by Managers to identify this type of service
    # : We could have used here the Class name, but we decided that the
    # : module implementator will be the one that will provide a name that
    # : will relation the class (type) and that name.
    typeType: typing.ClassVar[str] = 'baseMFA'

    # : Description shown at administration level for this authenticator.
    # : This string will be translated when provided to admin interface
    # : using gettext, so you can mark it as "_" at derived classes (using gettext_noop)
    # : if you want so it can be translated.
    typeDescription: typing.ClassVar[str] = _('Base MFA')

    # : Icon file, used to represent this authenticator at administration interface
    # : This file should be at same folder as this class is, except if you provide
    # : your own :py:meth:uds.core.module.BaseModule.icon method.
    iconFile: typing.ClassVar[str] = 'mfa.png'

    # : Cache time for the generated MFA code
    # : this means that the code will be valid for this time, and will not 
    # : be resent to the user until the time expires.
    # : This value is in seconds
    # : Note: This value is used by default "process" methos, but you can
    # : override it in your own implementation.
    cacheTime: typing.ClassVar[int] = 300

    def __init__(self, environment: 'Environment', values: Module.ValuesType):
        super().__init__(environment, values)
        self.initialize(values)

    def initialize(self, values: Module.ValuesType):
        """
        This method will be invoked from __init__ constructor.
        This is provided so you don't have to provide your own __init__ method,
        and invoke base methods.
        This will get invoked when all initialization stuff is done

        Args:
            values: If values is not none, this object is being initialized
            from administration interface, and not unmarshal will be done.
            If it's None, this is initialized internally, and unmarshal will
            be called after this.

        Default implementation does nothing
        """

    def label(self) -> str:
        """
        This method will be invoked from the MFA form, to know the human name of the field
        that will be used to enter the MFA code.
        """
        return 'MFA Code'

    def validity(self) -> int:
        """
        This method will be invoked from the MFA form, to know the validity in secods
        of the MFA code.
        If value is 0 or less, means the code is always valid.
        """
        return self.cacheTime

    def sendCode(self, code: str) -> None:
        """
        This method will be invoked from "process" method, to send the MFA code to the user.
        """
        raise NotImplementedError('sendCode method not implemented')

    def process(self, userId: str, identifier: str) -> None:
        """
        This method will be invoked from the MFA form, to send the MFA code to the user.
        The identifier where to send the code, will be obtained from "mfaIdentifier" method.
        Default implementation generates a random code and sends invokes "sendCode" method.
        """
        # try to get the stored code
        data: typing.Any = self.storage.getPickle(userId)
        try:
            if data:
                # if we have a stored code, check if it's still valid
                if data[0] + datetime.timedelta(seconds=self.cacheTime) < getSqlDatetime():
                    # if it's still valid, just return without sending a new one
                    return
        except Exception:
            # if we have a problem, just remove the stored code
            self.storage.remove(userId)

        # Generate a 6 digit code (0-9)
        code = ''.join(random.SystemRandom().choices('0123456789', k=6))
        # Store the code in the database, own storage space
        self.storage.putPickle(userId, (getSqlDatetime(), code))
        # Send the code to the user
        self.sendCode(code)

    def validate(self, userId: str, identifier: str, code: str) -> None:
        """
        If this method is provided by an authenticator, the user will be allowed to enter a MFA code
        You must raise an "exceptions.MFAError" if the code is not valid.
        """
        # Validate the code
        try:
            data = self.storage.getPickle(userId)
            if data and len(data) == 2:
                # Check if the code is valid
                if data[1] == code:
                    # Code is valid, remove it from storage
                    self.storage.remove(userId)
                    return
        except Exception as e:
            # Any error means invalid code
            raise exceptions.MFAError(e)
                
