# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals

import os
import random
import string
import unittest

from flask import Flask
from sqlalchemy.engine.url import make_url
from sqlalchemy.exc import IntegrityError

from woodbox.db import db
from woodbox.models.user_model import UserModel, RoleModel

class TestCaseModel(unittest.TestCase):
    def setUp(self):
        self.app = Flask(__name__)
        # FIXME: find a way to configure the db to test other backends (like MySQL).
        self.app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////tmp/woodbox-testing.db'
        self.app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
        self.app.config['PASSWORD_SALT'] = 'salt'
        self.app.config['TESTING'] = True
        db.init_app(self.app)

    def tearDown(self):
        with self.app.test_request_context('/'):
            if db.engine.driver == 'pysqlite':
                url = make_url(self.app.config['SQLALCHEMY_DATABASE_URI'])
                if url.database is not None:
                    os.remove(url.database)

    @staticmethod
    def str_n(n):
        return ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(n))



class TestUser(TestCaseModel):
    def test_unique_name(self):
        """Test that we cannot add two users with the same username."""
        with self.app.test_request_context('/'):
            db.drop_all()
            db.create_all()
            db.session.add(UserModel(username='alice', password='abc', name='Alice Allard'))
            db.session.commit()

            db.session.add(UserModel(username='alice', password='def', name='Alice Allison'))
            self.assertRaises(IntegrityError, db.session.commit)
            db.session.rollback()

            db.session.add(UserModel(username='alice2', password='ghi', name='Alice Allard'))
            db.session.add(UserModel(username='alice3', password='abc', name='Alice Allard'))
            db.session.commit()

    def test_field_limits(self):
        """Test that length limits on username and name are enforced."""
        with self.app.test_request_context('/'):
            db.drop_all()
            db.create_all()

            long_username = self.str_n(51)
            long_name = self.str_n(101)
            long_password = self.str_n(1024)
            self.assertEqual(len(long_username), 51)
            self.assertEqual(len(long_name), 101)
            self.assertEqual(len(long_password), 1024)

            u1 = UserModel(username=long_username, password='def', name='Alice Allison')
            u2 = UserModel(username='alice2', password='ghi', name=long_name)
            u3 = UserModel(username='alice3', password=long_password, name='Alice Allard')
            db.session.add(u1)
            db.session.add(u2)
            db.session.add(u3)
            db.session.commit()

            users = UserModel.query.order_by(UserModel.id).all()
            if db.engine.driver != 'pysqlite':
                # sqlite ignore field length.
                self.assertEqual(users[0].username, long_username[:50])
                self.assertEqual(users[1].name, long_name[:100])
            self.assertEqual(users[2].hashed_password, UserModel.hash_password(long_password))

    def test_store_hashed_password(self):
        """Test that the password is stored encrypted."""
        with self.app.test_request_context('/'):
            hashed_password = UserModel.hash_password('abc')
            db.drop_all()
            db.create_all()
            user = UserModel(username='alice', password='abc', name='Alice Allard')
            db.session.add(user)
            db.session.commit()
            read_user = UserModel.query.get(user.id)
            self.assertEqual(read_user.id, user.id)
            self.assertEqual(read_user.hashed_password, hashed_password)


    def test_roles(self):
        """Test user role assignment."""
        with self.app.test_request_context('/'):
            db.drop_all()
            db.create_all()
            user = UserModel(username='alice', password='abc', name='Alice Allard')
            db.session.add(user)

            role_names = ['a', 'b', 'c', 'd']
            roles = []
            for r in role_names:
                role = RoleModel(rolename=r)
                db.session.add(role)
                user.roles.append(role)
                roles.append(role)
            db.session.commit()

            read_user = UserModel.query.get(user.id)
            self.assertEqual(read_user.roles, roles)

            read_user.roles.remove(roles[2])
            db.session.add(user)
            db.session.commit()
            read_user = UserModel.query.get(user.id)
            self.assertNotIn(roles[2], read_user.roles)
            self.assertIn(roles[3], read_user.roles)

            role = RoleModel(rolename='e')
            user.roles.append(role)
            db.session.add(user)
            db.session.commit()
            read_user = UserModel.query.get(user.id)
            self.assertIn(role, read_user.roles)
