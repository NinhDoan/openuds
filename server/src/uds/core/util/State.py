# -*- coding: utf-8 -*-

#
# Copyright (c) 2012 Virtual Cable S.L.
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
#    * Neither the name of Virtual Cable S.L. nor the names of its contributors 
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
@author: Adolfo Gómez, dkmaster at dkmon dot com
'''


from django.utils.translation import ugettext_noop as _, ugettext

# States for different objects. Not all objects supports all States
class State(object):
    '''
    This class represents possible states for objects at database.
    Take in consideration that objects do not have to support all states, they are here for commodity
    '''
    ACTIVE = 'A'
    INACTIVE = 'I'
    BLOCKED = 'B'
    LAUNCHING = 'L'
    PREPARING = 'P' 
    USABLE = 'U' 
    REMOVABLE = 'R' 
    REMOVING = 'M' 
    REMOVED = 'S'
    CANCELED = 'C' 
    CANCELING = 'K'
    ERROR = 'E'
    RUNNING = 'W'
    FINISHED = 'F'
    FOR_EXECUTE = 'X'
    
    string = { ACTIVE: _('Active'), INACTIVE: _('Inactive'), BLOCKED: _('Blocked'), LAUNCHING: _('Waiting publication'), 
               PREPARING: _('In preparation'), USABLE: _('Valid'), 
               REMOVABLE: _('Waiting for removal'), REMOVING: _('Removing'),  REMOVED: _('Removed'), CANCELED: _('Canceled'), 
               CANCELING: _('Canceling'), ERROR: _('Error'), RUNNING: _('Running'), FINISHED: _('Finished'), FOR_EXECUTE: _('Waiting execution') }
    
    # States that are merely for "information" to the user. They don't contain any usable instance
    INFO_STATES = [REMOVED, CANCELED, ERROR]
    
    # States that indicates that the service is "Valid" for a user
    VALID_STATES = [USABLE,PREPARING]

    # Publication States
    PUBLISH_STATES = [LAUNCHING, PREPARING]

    @staticmethod
    def isActive(state):
        return state == State.ACTIVE

    @staticmethod
    def isInactive(state):
        return state == State.INACTIVE
    
    @staticmethod
    def isBlocked(state):
        return state == State.BLOCKED
    
    @staticmethod
    def isPreparing(state):
        return state == State.PREPARING
    
    @staticmethod
    def isUsable(state):
        return state == State.USABLE
    
    @staticmethod
    def isRemovable(state):
        return state == State.REMOVABLE
    
    @staticmethod
    def isRemoving(state):
        return state == State.REMOVING
    
    @staticmethod
    def isRemoved(state):
        return state == State.REMOVED
    
    @staticmethod
    def isCanceling(state):
        return state == State.CANCELING

    @staticmethod
    def isCanceled(state):
        return state == State.CANCELED

    @staticmethod
    def isErrored(state):
        return state == State.ERROR
    
    @staticmethod
    def isFinished(state):
        return state == State.FINISHED

    @staticmethod
    def isRuning(state):
        return state == State.RUNNING
    
    @staticmethod
    def isForExecute(state):
        return state == State.FOR_EXECUTE
    
    @staticmethod
    def toString(state):
        try:
            return State.string[state]
        except Exception:
            return ''
    
