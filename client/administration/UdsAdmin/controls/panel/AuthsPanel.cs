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
using System.ComponentModel;
using System.Drawing;
using System.Data;
using System.Linq;
using System.Text;
using System.Windows.Forms;

namespace UdsAdmin.controls.panel
{
    public partial class AuthsPanel : UserControl
    {
        gui.ListViewSorter _listSorter;

        public AuthsPanel()
        {
            InitializeComponent();

            listView.ListViewItemSorter = _listSorter = new gui.ListViewSorter(listView);
            updateList();
        }

        private void UsersPanel_VisibleChanged(object sender, EventArgs e)
        {
            if (Visible == true)
            {
                updateList();
            }
        }

        private void updateList()
        {
            try
            {
                xmlrpc.Authenticator[] auths = xmlrpc.UdsAdminService.GetAuthenticators();
                List<ListViewItem> lst = new List<ListViewItem>();
                foreach (xmlrpc.Authenticator auth in auths)
                {
                    ListViewItem itm = new ListViewItem(new string[] { auth.name, auth.typeName, auth.comments, auth.priority });
                    itm.ForeColor = gui.Colors.ActiveColor;
                    itm.Tag = auth.id;
                    lst.Add(itm);
                }
                listView.Items.Clear();
                listView.Items.AddRange(lst.ToArray());
            }
            catch (CookComputing.XmlRpc.XmlRpcFaultException ex)
            {
                gui.UserNotifier.notifyRpcException(ex);
            }

            if (listView.Items.Count > 0)
            {
                listView.Items[0].Selected = listView.Items[0].Focused = true;
                listView.Focus();
            }
        }

        private void listView_KeyUp(object sender, KeyEventArgs e)
        {
            switch (e.KeyCode)
            {
                case Keys.F5:
                    updateList();
                    updateLogs();
                    break;
                case Keys.E:
                    if (e.Modifiers == Keys.Control)
                        foreach (ListViewItem i in listView.Items)
                            i.Selected = true;
                    break;
            }
        }

        private void listView_ColumnClick(object sender, ColumnClickEventArgs e)
        {
            _listSorter.ColumnClick(sender, e);
        }

        private void listView_SelectedIndexChanged(object sender, EventArgs e)
        {
            updateLogs();
        }

        private void updateLogs()
        {
            List<xmlrpc.LogEntry> data = new List<xmlrpc.LogEntry>();
            foreach (ListViewItem i in listView.SelectedItems)
            {
                try
                {
                    xmlrpc.LogEntry[] logs = xmlrpc.UdsAdminService.GetAuthLogs((string)i.Tag);
                    data.AddRange(logs);
                }
                catch (CookComputing.XmlRpc.XmlRpcFaultException ex)
                {
                    gui.UserNotifier.notifyRpcException(ex);
                }

            }
            logViewer1.setLogs(data.ToArray());
        }

        private void AuthsPanel_Resize(object sender, EventArgs e)
        {
            // Workaround to "dock" not fitting the content correctly
            splitContainer1.Size = this.Size;
        }

    }
}
