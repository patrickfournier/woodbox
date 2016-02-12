# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals

import unittest

from flask import g
from werkzeug.exceptions import HTTPException

from woodbox.access_control.api import Acl
from woodbox.db import db
from woodbox.models.user_model import WBRoleModel, WBUserModel
from woodbox.tests.flask_test_case import FlaskTestCase

acl = Acl()
acl.grants({
    'admin': {
        'TestResource': ['create', 'read', 'update', 'delete'],
    },
    'manager': {
        'TestResource': ['create', 'read'],
    },
    'user': {
        'TestResource': ['read'],
    },
})


class ApiAccessTestCase(FlaskTestCase):
    def setUp(self):
        self.resource_name = 'TestResource'

        super(ApiAccessTestCase, self).setUp()

        with self.app.test_request_context('/'):
            db.initialize()
            # Create some roles
            self.r1 = WBRoleModel(rolename='admin')
            db.session.add(self.r1)
            self.r2 = WBRoleModel(rolename='manager')
            db.session.add(self.r2)
            self.r3 = WBRoleModel(rolename='user')
            db.session.add(self.r3)
            db.session.commit()

            # Create some users
            self.u1 = WBUserModel(username='a', password='a', roles=[self.r1])
            db.session.add(self.u1)
            self.u2 = WBUserModel(username='b', password='a', roles=[self.r2])
            db.session.add(self.u2)
            self.u3 = WBUserModel(username='c', password='a', roles=[self.r3])
            db.session.add(self.u3)
            db.session.commit()

            self.u1 = self.u1.id
            self.u2 = self.u2.id
            self.u3 = self.u3.id

            self.r1 = self.r1.id
            self.r2 = self.r2.id
            self.r3 = self.r3.id

    def post(self):
        return True

    def get(self):
        return True

    def patch(self):
        return True

    def delete(self):
        return True

    def test_admin(self):
        with self.app.test_request_context('/'):
            g.user = self.u1
            for action in ['post', 'get', 'patch', 'delete']:
                meth = getattr(self, action, None)
                meth = acl.authorize(meth)
                self.assertTrue(meth)

    def test_manager(self):
        with self.app.test_request_context('/'):
            g.user = self.u2
            for action in ['post', 'get']:
                meth = getattr(self, action, None)
                meth = acl.authorize(meth)
                self.assertTrue(meth)
            for action in ['patch', 'delete']:
                meth = getattr(self, action, None)
                meth = acl.authorize(meth)
                self.assertRaises(HTTPException, meth)

    def test_user(self):
        with self.app.test_request_context('/'):
            g.user = self.u3
            for action in ['get']:
                meth = getattr(self, action, None)
                meth = acl.authorize(meth)
                self.assertTrue(meth)
            for action in ['post', 'patch', 'delete']:
                meth = getattr(self, action, None)
                meth = acl.authorize(meth)
                self.assertRaises(HTTPException, meth)

    def test_anonymous(self):
        with self.app.test_request_context('/'):
            g.user = None
            for action in ['post', 'get', 'patch', 'delete']:
                meth = getattr(self, action, None)
                meth = acl.authorize(meth)
                self.assertRaises(HTTPException, meth)
