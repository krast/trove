# Copyright 2012 OpenStack LLC.
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

import logging

from novaclient import exceptions as nova_exceptions

from reddwarf.common import exception

from reddwarf.common import wsgi
from reddwarf.common.remote import create_nova_client
from reddwarf.extensions.account import views
from reddwarf.extensions.mgmt.instances.models import MgmtInstances
from reddwarf.instance.models import DBInstance


LOG = logging.getLogger(__name__)


class AccountController(wsgi.Controller):
    """Controller for account functionality"""

    def show(self, req, tenant_id, id):
        """Return a account and instances associated with a single account."""
        LOG.info(_("req : '%s'\n\n") % req)
        LOG.info(_("Showing account information for '%s' to '%s'")
                  % (id, tenant_id))

        context = req.environ[wsgi.CONTEXT_KEY]
        try:
            client = create_nova_client(context)
            account = client.accounts.get_instances(id)
            db_infos = DBInstance.find_all(tenant_id=id, deleted=False)
            servers = _convert_server_objects(account.servers)
            instances = MgmtInstances.load_status_from_existing(context,
                                                             db_infos, servers)
        except nova_exceptions.ClientException, e:
            LOG.error(e)
            return wsgi.Result(str(e), 403)
        return wsgi.Result(views.AccountView(account, instances).data(), 200)

def _convert_server_objects(servers):
    server_objs = []
    for server in servers:
        server_objs.append(Server(server))
    return server_objs


class Server(object):

    def __init__(self, server):
        self.id = server['id']
        self.status = server['status']
        self.name = server['name']
        self.host = server['host']