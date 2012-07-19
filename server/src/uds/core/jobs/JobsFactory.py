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

from datetime import timedelta
import logging

logger = logging.getLogger(__name__)

class JobsFactory(object):
    _factory = None
    
    def __init__(self):
        self._jobs = {}
    
    @staticmethod        
    def factory():
        if JobsFactory._factory  == None:
            JobsFactory._factory = JobsFactory()
        return JobsFactory._factory
    
    def jobs(self):
        return self._jobs
    
    def insert(self, name, type):
        try:
            self._jobs[name] = type
        except Exception, e:
            logger.debug('Exception at insert in JobsFactory: {0}, {1}'.format(e.__class__, e))
        
    def ensureJobsInDatabase(self):
        from uds.models import Scheduler, getSqlDatetime, State
        try:
            logger.debug('Ensuring that jobs are registered inside database')
            for name, type in self._jobs.iteritems():
                try:
                    # We use database server datetime
                    now = getSqlDatetime()
                    next = now 
                    job = Scheduler.objects.create(name = name, frecuency = type.frecuency, last_execution = now, next_execution = next, state = State.FOR_EXECUTE)
                except Exception: # already exists
                    job = Scheduler.objects.get(name=name)
                    job.frecuency = type.frecuency
                    job.save()
        except Exception, e:
            logger.debug('Exception at insert in JobsFactory: {0}, {1}'.format(e.__class__, e))
        
        
    def lookup(self, typeName):
        try:
            return self._jobs[typeName]
        except KeyError:
            return None
