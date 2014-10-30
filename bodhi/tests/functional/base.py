# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.

import os
import unittest

from datetime import datetime, timedelta
from webtest import TestApp
from sqlalchemy import create_engine
from sqlalchemy import event

from bodhi import main, log
from bodhi.tests import populate
from bodhi.models import (
    Base,
    Bug,
    Build,
    BuildrootOverride,
    Comment,
    CVE,
    DBSession,
    Group,
    Package,
    Release,
    Update,
    UpdateType,
    User,
    UpdateStatus,
    UpdateRequest,
    TestCase,
)

FAITOUT = 'http://209.132.184.152/faitout/'
DB_PATH = 'sqlite://'
DB_NAME = None
# The BUILD_ID environment variable is set by Jenkins and allows us to detect if
# we are running the tests in jenkins or not
# https://wiki.jenkins-ci.org/display/JENKINS/Building+a+software+project#Buildingasoftwareproject-below
if os.environ.get('BUILD_ID'):
    try:
        import requests
        req = requests.get('%s/new' % FAITOUT)
        if req.status_code == 200:
            DB_PATH = req.text
            DB_NAME = DB_PATH.rsplit('/', 1)[1]
            print 'Using faitout at: %s' % DB_PATH
    except:
        pass


class BaseWSGICase(unittest.TestCase):
    app_settings = {
        'sqlalchemy.url': DB_PATH,
        'mako.directories': 'bodhi:templates',
        'session.type': 'memory',
        'session.key': 'testing',
        'session.secret': 'foo',
        'dogpile.cache.backend': 'dogpile.cache.memory',
        'dogpile.cache.expiration_time': 0,
        'cache.type': 'memory',
        'cache.regions': 'default_term, second, short_term, long_term',
        'cache.second.expire': '1',
        'cache.short_term.expire': '60',
        'cache.default_term.expire': '300',
        'cache.long_term.expire': '3600',
        'acl_system': 'dummy',
        'buildsystem': 'dummy',
        'important_groups': 'proventesters provenpackager releng',
        'admin_groups': 'bodhiadmin releng',
        'admin_packager_groups': 'provenpackager',
        'mandatory_packager_groups': 'packager',
        'critpath_pkgs': 'kernel',
        'bugtracker': 'dummy',
        'stats_blacklist': 'bodhi autoqa',
        'system_users': 'bodhi autoqa',
        'max_update_length_for_ui': '70',
        'openid.provider': 'https://id.stg.fedoraproject.org',
        'test_case_base_url': 'https://fedoraproject.org/wiki/',
        'openid_template': '{username}.id.fedoraproject.org',
        'site_requirements': 'rpmlint',
    }

    def setUp(self):
        engine = create_engine(DB_PATH)
        DBSession.configure(bind=engine)
        log.debug('Creating all models for %s' % engine)
        Base.metadata.create_all(engine)
        self.db = DBSession()
        populate(self.db)
        self.app = TestApp(main({}, testing=u'guest', **self.app_settings))

        # Track sql statements in every test
        self.sql_statements = []
        def track(conn, cursor, statement, param, ctx, many):
            self.sql_statements.append(statement)

        event.listen(engine, "before_cursor_execute", track)

    def tearDown(self):
        log.debug('Removing session')
        DBSession.remove()
        if DB_NAME:
            try:
                import requests
                req = requests.get('%s/clean/%s' % (FAITOUT, DB_NAME))
            except:
                pass


    def get_update(self, builds=u'bodhi-2.0-1.fc17', stable_karma=3, unstable_karma=-3):
        if isinstance(builds, list):
            builds = u','.join(builds)
        return {
            'builds': builds,
            'bugs': u'',
            'notes': u'this is a test update',
            'type': u'bugfix',
            'stable_karma': stable_karma,
            'unstable_karma': unstable_karma,
        }
