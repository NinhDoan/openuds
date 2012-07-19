﻿//
// Copyright (c) 2012 Virtual Cable S.L.
// All rights reserved.
//
// Redistribution and use in source and binary forms, with or without modification, 
// are permitted provided that the following conditions are met:
//
//    * Redistributions of source code must retain the above copyright notice, 
//      this list of conditions and the following disclaimer.
//    * Redistributions in binary form must reproduce the above copyright notice, 
//      this list of conditions and the following disclaimer in the documentation 
//      and/or other materials provided with the distribution.
//    * Neither the name of Virtual Cable S.L. nor the names of its contributors 
//      may be used to endorse or promote products derived from this software 
//      without specific prior written permission.
//
// THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" 
// AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE 
// IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE 
// DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE 
// FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
// DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR 
// SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER 
// CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, 
// OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE 
// OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

// author: Adolfo Gómez, dkmaster at dkmon dot com

using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;

namespace UdsAdmin.xmlrpc
{
    internal class Util
    {
        public static string GetStringFromState(string state, string osState = "")
        {
            switch (state)
            {
                case Constants.STATE_USABLE:
                    if (osState != "" && osState != Constants.STATE_USABLE )
                        return Strings.waitingOsReady;
                    return Strings.stateUsable;
                case Constants.STATE_LAUNCHING:
                    return Strings.stateLaunching;
                case Constants.STATE_PREPARING:
                    return Strings.statePreparing;
                case Constants.STATE_CANCELING:
                    return Strings.stateCanceling;
                case Constants.STATE_CANCELED:
                    return Strings.stateCanceled;
                case Constants.STATE_REMOVABLE:
                    return Strings.stateRemovable;
                case Constants.STATE_REMOVING:
                    return Strings.stateRemoving;
                case Constants.STATE_REMOVED:
                    return Strings.stateRemoved;
                case Constants.STATE_ERROR:
                    return Strings.stateError;
                // From here, user, groups, ... states
                case Constants.STATE_ACTIVE:
                    return Strings.stateActive;
                case Constants.STATE_BLOCKED:
                    return Strings.stateBlocked;
                case Constants.STATE_INACTIVE:
                    return Strings.stateInactive;
                default:
                    return Strings.stateUnknown;
            }
        }

    }
}
