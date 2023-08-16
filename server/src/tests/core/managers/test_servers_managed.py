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
Author: Adolfo Gómez, dkmaster at dkmon dot com
"""
from contextlib import contextmanager
import typing
import datetime
import time
from unittest import mock
import functools
import logging

from uds import models
from uds.core import types, exceptions
from uds.core.managers import servers

from ...fixtures import servers as servers_fixtures
from ...fixtures import services as services_fixtures
from ...utils.test import UDSTestCase

logger = logging.getLogger(__name__)

NUM_REGISTEREDSERVERS = 8
NUM_USERSERVICES = NUM_REGISTEREDSERVERS + 1


class ServerManagerManagedServersTest(UDSTestCase):
    user_services: typing.List['models.UserService']
    manager: 'servers.ServerManager'
    registered_servers_group: 'models.RegisteredServerGroup'
    assign: typing.Callable[..., typing.Tuple[str, int]]
    all_uuids: typing.List[str]

    def setUp(self) -> None:
        super().setUp()
        self.user_services = []
        self.manager = servers.ServerManager().manager()
        # Manager is a singleton, clear counters
        # self.manager.clearCounters()

        for i in range(NUM_USERSERVICES):
            # So we have 8 userservices, each one with a different user
            self.user_services.extend(services_fixtures.createCacheTestingUserServices())

        self.registered_servers_group = servers_fixtures.createRegisteredServerGroup(
            type=types.servers.ServerType.UNMANAGED, subtype='test', num_servers=NUM_REGISTEREDSERVERS
        )
        # commodity call to assign
        self.assign = functools.partial(
            self.manager.assign,
            serverGroup=self.registered_servers_group,
            serviceType=types.services.ServiceType.VDI,
        )
        self.all_uuids: typing.List[str] = list(
            self.registered_servers_group.servers.all().values_list('uuid', flat=True)
        )

    @contextmanager
    def createMockApiRequester(self) -> typing.Iterator[mock.Mock]:
        with mock.patch('uds.core.managers.servers_api.request.ServerApiRequester') as mockServerApiRequester:

            stats_dct = {
                server.uuid: types.servers.ServerStatsType(
                    mem=i*100,
                    maxmem=NUM_REGISTEREDSERVERS*100,
                    cpu=100/NUM_REGISTEREDSERVERS * (i+1),
                    uptime=0,
                    disk=0,
                    maxdisk=0,
                    connections=0,
                    current_users=0,
                    )
                for i, server in enumerate(self.registered_servers_group.servers.all())
            }
                
            def getStats() -> typing.Optional[types.servers.ServerStatsType]:
                # Get first argument from call to init on serverApiRequester
                server = mockServerApiRequester.call_args[0][0]
                return stats_dct.get(server.uuid, None)

            # return_value returns the instance of the mock
            mockServerApiRequester.return_value.getStats.side_effect = getStats
            yield mockServerApiRequester

    def testAssignAuto(self) -> None:
        with self.createMockApiRequester() as mockServerApiRequester:
            for elementNumber, userService in enumerate(self.user_services[:NUM_REGISTEREDSERVERS]):
                expected_getStats_calls = NUM_REGISTEREDSERVERS * (elementNumber + 1)
                expected_notifyAssign_calls = elementNumber * 33  # 32 in loop + 1 in first assign
                uuid, counter = self.assign(userService)
                storage_key = self.manager.storage_key(self.registered_servers_group, userService.user)
                # uuid shuld be one on registered servers
                self.assertTrue(uuid in self.all_uuids)
                # Server locked should be None
                self.assertIsNone(models.RegisteredServer.objects.get(uuid=uuid).locked_until)

                # mockServer.getStats has been called NUM_REGISTEREDSERVERS times
                self.assertEqual(
                    mockServerApiRequester.return_value.getStats.call_count,
                    expected_getStats_calls,
                    f'Error on loop {elementNumber}',
                )
                # notifyAssign should has been called once for each user service
                self.assertEqual(
                    mockServerApiRequester.return_value.notifyAssign.call_count, expected_notifyAssign_calls + 1
                )
                # notifyAssign paramsh should have been
                # request.ServerApiRequester(bestServer).notifyAssign(userService, serviceType, uuid_counter[1])
                self.assertEqual(
                    mockServerApiRequester.return_value.notifyAssign.call_args[0][0], userService
                )  # userService
                self.assertEqual(
                    mockServerApiRequester.return_value.notifyAssign.call_args[0][1],
                    types.services.ServiceType.VDI,
                )
                self.assertEqual(
                    mockServerApiRequester.return_value.notifyAssign.call_args[0][2], counter
                )  # counter

                # Server storage should contain the assignation
                with self.manager.svrStorage() as stor:
                    self.assertEqual(len(stor), elementNumber + 1)
                    uuid_counter = stor[storage_key]
                    # uuid_counter is (uuid, assign counter)
                    self.assertEqual(uuid_counter[0], uuid)
                    self.assertEqual(uuid_counter[1], counter)

                # Again, try to assign, same user service, same group, same service type, same minMemoryMB and same uuid
                for i in range(32):
                    uuid2, counter = self.assign(userService)
                    # uuid2 should be the same as uuid
                    self.assertEqual(uuid, uuid2)
                    # uuid2 should be one on registered servers
                    self.assertTrue(uuid2 in self.all_uuids)
                    self.assertIsNone(
                        models.RegisteredServer.objects.get(uuid=uuid).locked_until
                    )  # uuid is uuid2

                    # mockServer.getStats has been called NUM_REGISTEREDSERVERS times, because no new requests has been done
                    self.assertEqual(
                        mockServerApiRequester.return_value.getStats.call_count, expected_getStats_calls
                    )
                    # notifyAssign should has been called twice
                    self.assertEqual(
                        mockServerApiRequester.return_value.notifyAssign.call_count,
                        expected_notifyAssign_calls + i + 2,
                    )

                    # Server storage should be emtpy here
                    with self.manager.svrStorage() as stor:
                        self.assertEqual(len(stor), elementNumber + 1)
                        uuid_counter = stor[storage_key]
                        # uuid_counter is (uuid, assign counter)
                        self.assertEqual(uuid_counter[0], uuid)
                        self.assertEqual(uuid_counter[1], counter)

            # Now, remove all asignations..
            for elementNumber, userService in enumerate(self.user_services[:NUM_REGISTEREDSERVERS]):
                expected_getStats_calls = NUM_REGISTEREDSERVERS * (elementNumber + 1)
                expected_notifyAssign_calls = elementNumber * 33  # 32 in loop + 1 in first assign
                storage_key = self.manager.storage_key(self.registered_servers_group, userService.user)

                # # Remove it, should decrement counter
                for i in range(32, -1, -1):  # Deletes 33 times
                    res = self.manager.release(userService, self.registered_servers_group)

            with self.manager.svrStorage() as stor:
                self.assertEqual(len(stor), 0)

    def testAssignAutoLockLimit(self) -> None:
        with self.createMockApiRequester() as mockServerApiRequester:
            # Assign all user services with lock
            for userService in self.user_services[:NUM_REGISTEREDSERVERS]:
                uuid, counter = self.assign(
                    userService,
                    lockTime=datetime.timedelta(seconds=1),
                )
                # uuid shuld be one on registered servers
                self.assertTrue(uuid in self.all_uuids)
                # And only one assignment, so counter is 1
                self.assertTrue(counter, 1)
                # Server locked should not be None (that is, it should be locked)
                self.assertIsNotNone(models.RegisteredServer.objects.get(uuid=uuid).locked_until)

            # Next one should fail with an exceptions.UDSException
            with self.assertRaises(exceptions.UDSException):
                self.assign(self.user_services[NUM_REGISTEREDSERVERS], lockTime=datetime.timedelta(seconds=1))

            # Wait a second, and try again, it should work
            time.sleep(1)
            self.assign(self.user_services[NUM_REGISTEREDSERVERS], lockTime=datetime.timedelta(seconds=1))

            # notifyRelease should has been called once
            self.assertEqual(mockServerApiRequester.return_value.notifyRelease.call_count, 1)

    def testAssignReleaseMax(self) -> None:
        for assignation in range(3):
            with self.createMockApiRequester() as mockServerApiRequester:
                for elementNumber, userService in enumerate(self.user_services[:NUM_REGISTEREDSERVERS]):
                    uuid, counter = self.assign(userService)
                    # uuid shuld be one on registered servers
                    self.assertTrue(uuid in self.all_uuids)
                    # And only one assignment, so counter is 1
                    self.assertTrue(counter, 1)
                    # Server locked should be None
                    self.assertIsNone(models.RegisteredServer.objects.get(uuid=uuid).locked_until)
                    self.assertEqual(self.manager.getUnmanagedUsage(uuid), assignation + 1)

        with self.manager.svrStorage() as stor:
            self.assertEqual(len(stor), NUM_REGISTEREDSERVERS)

        with self.manager.cntStorage() as stor:
            self.assertEqual(len(stor), NUM_REGISTEREDSERVERS)

        # Now release all, 3 times
        for release in range(3):
            for elementNumber, userService in enumerate(self.user_services[:NUM_REGISTEREDSERVERS]):
                res = self.manager.release(userService, self.registered_servers_group)
                if res:
                    uuid, counter = res
                    # uuid shuld be one on registered servers
                    self.assertTrue(uuid in self.all_uuids)
                    # Number of lasting assignations should be one less than before
                    self.assertEqual(counter, 3 - release - 1)
                    # Server locked should be None
                    self.assertIsNone(models.RegisteredServer.objects.get(uuid=uuid).locked_until)
                    # 3 - release -1 because we have released it already
                    self.assertEqual(
                        self.manager.getUnmanagedUsage(uuid),
                        3 - release - 1,
                        f'Error on {elementNumber}/{release}',
                    )
        with self.manager.svrStorage() as stor:
            self.assertEqual(len(stor), 0)

        with self.manager.cntStorage() as stor:
            self.assertEqual(len(stor), 0)
