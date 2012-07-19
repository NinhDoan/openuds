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

from functools import wraps
import logging
import base64, random, string

logger = logging.getLogger(__name__)

SCRAMBLE_SES = 'scrSid'
SCRAMBLE_LEN = 10

# Decorator to make easier protect pages
def transformId(view_func):
    '''
    Decorator to untransform id used in a function. Its generates a hash of it
    To use this decorator, the view must receive 'response' and 'id' and (optionaly) 'id2', 'id3'
    example: def view(response, id)
    '''
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        for k in kwargs.keys():
            if k[:2] == 'id':
                kwargs[k] = unscrambleId(request, kwargs[k])
        return view_func(request, *args, **kwargs)
    return _wrapped_view


def scrambleId(request, id):
    if request.session.get(SCRAMBLE_SES) == None:
        request.session[SCRAMBLE_SES] =  ''.join(random.choice(string.letters) for i in xrange(SCRAMBLE_LEN))
    return base64.b64encode(str(id) + request.session.get(SCRAMBLE_SES)).encode('hex')

def unscrambleId(request, id):
    idd = base64.b64decode(id.decode('hex'))
    return idd[:-SCRAMBLE_LEN]
