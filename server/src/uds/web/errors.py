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

from django.utils.translation import ugettext_lazy as _
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse
from transformers import scrambleId
from uds.models import DeployedService, Transport, UserService, Authenticator
from uds.core.auths.Exceptions import InvalidUserException, InvalidAuthenticatorException
from uds.core.services.Exceptions import InvalidServiceException, MaxServicesReachedException
import logging

logger = logging.getLogger(__name__)

UNKNOWN_ERROR = 0
TRANSPORT_NOT_FOUND = 1
SERVICE_NOT_FOUND = 2
ACCESS_DENIED = 3
INVALID_SERVICE = 4
MAX_SERVICES_REACHED = 5
COOKIES_NEEDED = 6
USER_SERVICE_NOT_FOUND = 7
AUTHENTICATOR_NOT_FOUND = 8
INVALID_CALLBACK = 9


strings = [ 
           _('Unknown error'), 
           _('Transport not found'), 
           _('Service not found'), 
           _('Access denied'), 
           _('Invalid service. The service is not available at this moment. Please, try later'),
           _('Maximum services limit reached. Please, contact administrator'),
           _('You need to enable cookies to let this application work'),
           _('User service not found'),
           _('Authenticator not found'),
           _('Invalid authenticator callback')
        ]


def errorString(errorId):
    errorId = int(errorId)
    if errorId < len(strings):
        return strings[errorId]
    return strings[0]
    
    
def errorView(request, idError):
    return HttpResponseRedirect( reverse('uds.web.views.error', kwargs = { 'idError': scrambleId(request, idError) }) )


def exceptionView(request, exception):
    '''
    Tries to render an error page with error information
    '''
    try:
        raise exception
    except UserService.DoesNotExist:
        return errorView(request, USER_SERVICE_NOT_FOUND)
    except DeployedService.DoesNotExist:
        return errorView(request, SERVICE_NOT_FOUND)
    except Transport.DoesNotExist:
        return errorView(request, TRANSPORT_NOT_FOUND)
    except Authenticator.DoesNotExist:
        return errorView(request, AUTHENTICATOR_NOT_FOUND)
    except InvalidUserException:
        return errorView(request, ACCESS_DENIED)
    except InvalidServiceException:
        return errorView(request, INVALID_SERVICE)
    except MaxServicesReachedException:
        return errorView(request, MAX_SERVICES_REACHED)
    except InvalidAuthenticatorException:
        return errorView(request, INVALID_CALLBACK)
    except Exception as e:
        logger.exception('Exception cauthg at view!!!')
        raise e
