# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals

from sqlalchemy.exc import IntegrityError

from woodbox.db import db
from woodbox.models.user_model import WBUserModel, WBRoleModel
from woodbox.models.tests.model_test_case import ModelTestCase


class TestUser(ModelTestCase):
    def test_unique_name(self):
        """Test that we cannot add two users with the same username."""
        with self.app.test_request_context('/'):
            db.drop_all()
            db.create_all()
            db.session.add(WBUserModel(username='alice', password='abc'))
            db.session.commit()

            db.session.add(WBUserModel(username='alice', password='def'))
            self.assertRaises(IntegrityError, db.session.commit)
            db.session.rollback()

            # Check that duplicate password do not raise an exception.
            db.session.add(WBUserModel(username='alice2', password='abc'))
            db.session.commit()

    def test_field_limits(self):
        """Test that length limit on username is enforced."""
        with self.app.test_request_context('/'):
            db.drop_all()
            db.create_all()

            long_username = self.str_n(51)
            self.assertEqual(len(long_username), 51)

            user = WBUserModel(username=long_username, password='abc')
            db.session.add(user)
            db.session.commit()

            users = WBUserModel.query.order_by(WBUserModel.id).all()
            if db.engine.driver != 'pysqlite':
                self.assertEqual(users[0].username, long_username[:50])
            else:
                # sqlite ignore field length.
                self.assertEqual(users[0].username, long_username)

    def test_store_hashed_password(self):
        """Test that the password is stored as a hash."""
        with self.app.test_request_context('/'):
            password = self.str_n(1024)
            self.assertEqual(len(password), 1024)

            hashed_password = WBUserModel.hash_password(password)
            self.assertEqual(len(hashed_password), 64)

            db.drop_all()
            db.create_all()
            user = WBUserModel(username='alice', password=password)
            db.session.add(user)
            db.session.commit()
            read_user = WBUserModel.query.get(user.id)
            self.assertEqual(read_user.id, user.id)
            self.assertEqual(read_user.hashed_password, hashed_password)


    def test_roles(self):
        """Test user role assignment."""
        with self.app.test_request_context('/'):
            db.drop_all()
            db.create_all()
            user = WBUserModel(username='alice', password='abc')
            db.session.add(user)

            role_names = ['a', 'b', 'c', 'd']
            roles = []
            for r in role_names:
                role = WBRoleModel(rolename=r)
                db.session.add(role)
                user.roles.append(role)
                roles.append(role)
            db.session.commit()

            read_user = WBUserModel.query.get(user.id)
            self.assertEqual(read_user.roles, roles)

            read_user.roles.remove(roles[2])
            db.session.add(user)
            db.session.commit()
            read_user = WBUserModel.query.get(user.id)
            self.assertNotIn(roles[2], read_user.roles)
            self.assertIn(roles[3], read_user.roles)

            role = WBRoleModel(rolename='e')
            user.roles.append(role)
            db.session.add(user)
            db.session.commit()
            read_user = WBUserModel.query.get(user.id)
            self.assertIn(role, read_user.roles)
