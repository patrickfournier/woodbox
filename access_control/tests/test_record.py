# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals

import unittest

from sqlalchemy.exc import IntegrityError

from woodbox.access_control.record import And, Or, IsOwner, IsUser1, HasRole, InRecordACL
from woodbox.db import db
from woodbox.models.record_acl_model import RecordACLModel, make_record_acl
from woodbox.models.user_model import WBRoleModel, WBUserModel
from woodbox.tests.flask_test_case import FlaskTestCase

class MyModel(db.Model):
    id = db.Column(db.Integer, db.Sequence('my_model_id_seq'), primary_key=True)
    owner_id = db.Column(db.Integer, db.ForeignKey('wb_user_model.id'), nullable=False)
    owner = db.relationship('WBUserModel', foreign_keys='MyModel.owner_id')
    title = db.Column(db.String(256), unique=False, nullable=True)


class RecordAccessTestCase(FlaskTestCase):
    def setUp(self):
        super(RecordAccessTestCase, self).setUp()
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

            # Create some data
            self.d1 = MyModel(title='a', owner_id=self.u1)
            db.session.add(self.d1)
            self.d2 = MyModel(title='a', owner_id=self.u1)
            db.session.add(self.d2)
            self.d3 = MyModel(title='a', owner_id=self.u2)
            db.session.add(self.d3)
            self.d4 = MyModel(title='a', owner_id=self.u3)
            db.session.add(self.d4)
            db.session.commit()

            self.d1 = self.d1.id
            self.d2 = self.d2.id
            self.d3 = self.d3.id
            self.d4 = self.d4.id

            # Add some access control records
            anon = WBRoleModel.get_anonymous_role_id()

            db.session.add_all(make_record_acl(record_types=['My'],
                                               record_ids=[self.d1, self.d2, self.d3, self.d4],
                                               user_role_ids=[self.r1],
                                               permissions=['read', 'update', 'delete']))

            db.session.add_all(make_record_acl(record_types=['My'],
                                               record_ids=[self.d1, self.d2, self.d3, self.d4],
                                               user_role_ids=[self.r2],
                                               permissions=['read']))

            db.session.add_all(make_record_acl(record_types=['My'],
                                               record_ids=[self.d3, self.d4],
                                               user_role_ids=[self.r2],
                                               permissions=['update', 'delete']))

            db.session.add_all(make_record_acl(record_types=['My'],
                                               record_ids=[self.d1, self.d2, self.d3, self.d4],
                                               user_role_ids=[self.r3],
                                               permissions=['read']))

            db.session.add_all(make_record_acl(record_types=['My'],
                                               record_ids=[self.d3, self.d4],
                                               user_role_ids=[anon],
                                               permissions=['read']))
            db.session.commit()


    def tearDown(self):
        pass

    def test_is_owner_1(self):
        with self.app.test_request_context('/'):
            query = MyModel.query
            ac = IsOwner()
            query = ac.alter_query('read', query, self.u1, 'My', MyModel)
            items = query.values(MyModel.id)
            ids = [i[0] for i in items]
            self.assertIn(self.d1, ids)
            self.assertIn(self.d2, ids)
            self.assertNotIn(self.d3, ids)
            self.assertNotIn(self.d4, ids)

    def test_is_owner_3(self):
        with self.app.test_request_context('/'):
            query = MyModel.query
            ac = IsOwner()
            query = ac.alter_query('read', query, self.u3, 'My', MyModel)
            items = query.values(MyModel.id)
            ids = [i[0] for i in items]
            self.assertNotIn(self.d1, ids)
            self.assertNotIn(self.d2, ids)
            self.assertNotIn(self.d3, ids)
            self.assertIn(self.d4, ids)

    def test_is_user1(self):
        with self.app.test_request_context('/'):
            query = MyModel.query
            ac = IsUser1()
            query = ac.alter_query('read', query, self.u1, 'My', MyModel)
            items = query.values(MyModel.id)
            ids = [i[0] for i in items]
            self.assertIn(self.d1, ids)
            self.assertIn(self.d2, ids)
            self.assertIn(self.d3, ids)
            self.assertIn(self.d4, ids)

    def test_not_is_user1(self):
        with self.app.test_request_context('/'):
            query = MyModel.query
            ac = IsUser1()
            query = ac.alter_query('read', query, self.u2, 'My', MyModel)
            items = query.values(MyModel.id)
            ids = [i[0] for i in items]
            self.assertNotIn(self.d1, ids)
            self.assertNotIn(self.d2, ids)
            self.assertNotIn(self.d3, ids)
            self.assertNotIn(self.d4, ids)

    def test_is_owner_or_is_user1_1(self):
        with self.app.test_request_context('/'):
            query = MyModel.query
            ac = Or(IsOwner(), IsUser1())
            query = ac.alter_query('read', query, self.u1, 'My', MyModel)
            items = query.values(MyModel.id)
            ids = [i[0] for i in items]
            self.assertIn(self.d1, ids)
            self.assertIn(self.d2, ids)
            self.assertIn(self.d3, ids)
            self.assertIn(self.d4, ids)

    def test_is_owner_or_is_user1_2(self):
        with self.app.test_request_context('/'):
            query = MyModel.query
            ac = Or(IsOwner(), IsUser1())
            query = ac.alter_query('read', query, self.u2, 'My', MyModel)
            items = query.values(MyModel.id)
            ids = [i[0] for i in items]
            self.assertNotIn(self.d1, ids)
            self.assertNotIn(self.d2, ids)
            self.assertIn(self.d3, ids)
            self.assertNotIn(self.d4, ids)

    def test_is_owner_or_is_user1_3(self):
        with self.app.test_request_context('/'):
            query = MyModel.query
            ac = Or(IsOwner(), IsUser1())
            query = ac.alter_query('read', query, self.u3, 'My', MyModel)
            items = query.values(MyModel.id)
            ids = [i[0] for i in items]
            self.assertNotIn(self.d1, ids)
            self.assertNotIn(self.d2, ids)
            self.assertNotIn(self.d3, ids)
            self.assertIn(self.d4, ids)

    def test_is_owner_and_is_user1_1(self):
        with self.app.test_request_context('/'):
            query = MyModel.query
            ac = And(IsOwner(), IsUser1())
            query = ac.alter_query('read', query, self.u1, 'My', MyModel)
            items = query.values(MyModel.id)
            ids = [i[0] for i in items]
            self.assertIn(self.d1, ids)
            self.assertIn(self.d2, ids)
            self.assertNotIn(self.d3, ids)
            self.assertNotIn(self.d4, ids)

    def test_is_owner_and_is_user1_2(self):
        with self.app.test_request_context('/'):
            query = MyModel.query
            ac = And(IsOwner(), IsUser1())
            query = ac.alter_query('read', query, self.u2, 'My', MyModel)
            items = query.values(MyModel.id)
            ids = [i[0] for i in items]
            self.assertNotIn(self.d1, ids)
            self.assertNotIn(self.d2, ids)
            self.assertNotIn(self.d3, ids)
            self.assertNotIn(self.d4, ids)

    def test_is_owner_and_is_user1_3(self):
        with self.app.test_request_context('/'):
            query = MyModel.query
            ac = And(IsOwner(), IsUser1())
            query = ac.alter_query('read', query, self.u3, 'My', MyModel)
            items = query.values(MyModel.id)
            ids = [i[0] for i in items]
            self.assertNotIn(self.d1, ids)
            self.assertNotIn(self.d2, ids)
            self.assertNotIn(self.d3, ids)
            self.assertNotIn(self.d4, ids)

    def test_has_role_anonymous(self):
        with self.app.test_request_context('/'):
            query = MyModel.query
            ac = HasRole([WBRoleModel.anonymous_role_name])
            query = ac.alter_query('read', query, None, 'My', MyModel)
            items = query.values(MyModel.id)
            ids = [i[0] for i in items]
            self.assertIn(self.d1, ids)
            self.assertIn(self.d2, ids)
            self.assertIn(self.d3, ids)
            self.assertIn(self.d4, ids)

    def test_has_role_admin(self):
        with self.app.test_request_context('/'):
            query = MyModel.query
            ac = HasRole(['admin'])
            query = ac.alter_query('read', query, self.u1, 'My', MyModel)
            items = query.values(MyModel.id)
            ids = [i[0] for i in items]
            self.assertIn(self.d1, ids)
            self.assertIn(self.d2, ids)
            self.assertIn(self.d3, ids)
            self.assertIn(self.d4, ids)

    def test_not_has_role_admin(self):
        with self.app.test_request_context('/'):
            query = MyModel.query
            ac = HasRole(['admin'])
            query = ac.alter_query('read', query, self.u2, 'My', MyModel)
            items = query.values(MyModel.id)
            ids = [i[0] for i in items]
            self.assertNotIn(self.d1, ids)
            self.assertNotIn(self.d2, ids)
            self.assertNotIn(self.d3, ids)
            self.assertNotIn(self.d4, ids)

    def test_in_record_acl_1(self):
        with self.app.test_request_context('/'):
            query = MyModel.query
            ac = InRecordACL()
            query = ac.alter_query('read', query, self.u1, 'My', MyModel)
            items = query.values(MyModel.id)
            ids = [i[0] for i in items]
            self.assertIn(self.d1, ids)
            self.assertIn(self.d2, ids)
            self.assertIn(self.d3, ids)
            self.assertIn(self.d4, ids)

            query = MyModel.query
            ac = InRecordACL()
            query = ac.alter_query('update', query, self.u1, 'My', MyModel)
            items = query.values(MyModel.id)
            ids = [i[0] for i in items]
            self.assertIn(self.d1, ids)
            self.assertIn(self.d2, ids)
            self.assertIn(self.d3, ids)
            self.assertIn(self.d4, ids)

            query = MyModel.query
            ac = InRecordACL()
            query = ac.alter_query('delete', query, self.u1, 'My', MyModel)
            items = query.values(MyModel.id)
            ids = [i[0] for i in items]
            self.assertIn(self.d1, ids)
            self.assertIn(self.d2, ids)
            self.assertIn(self.d3, ids)
            self.assertIn(self.d4, ids)


    def test_in_record_acl_2(self):
        with self.app.test_request_context('/'):
            query = MyModel.query
            ac = InRecordACL()
            query = ac.alter_query('read', query, self.u2, 'My', MyModel)
            items = query.values(MyModel.id)
            ids = [i[0] for i in items]
            self.assertIn(self.d1, ids)
            self.assertIn(self.d2, ids)
            self.assertIn(self.d3, ids)
            self.assertIn(self.d4, ids)

            query = MyModel.query
            ac = InRecordACL()
            query = ac.alter_query('update', query, self.u2, 'My', MyModel)
            items = query.values(MyModel.id)
            ids = [i[0] for i in items]
            self.assertNotIn(self.d1, ids)
            self.assertNotIn(self.d2, ids)
            self.assertIn(self.d3, ids)
            self.assertIn(self.d4, ids)

            query = MyModel.query
            ac = InRecordACL()
            query = ac.alter_query('delete', query, self.u2, 'My', MyModel)
            items = query.values(MyModel.id)
            ids = [i[0] for i in items]
            self.assertNotIn(self.d1, ids)
            self.assertNotIn(self.d2, ids)
            self.assertIn(self.d3, ids)
            self.assertIn(self.d4, ids)

    def test_in_record_acl_3(self):
        with self.app.test_request_context('/'):
            query = MyModel.query
            ac = InRecordACL()
            query = ac.alter_query('read', query, self.u3, 'My', MyModel)
            items = query.values(MyModel.id)
            ids = [i[0] for i in items]
            self.assertIn(self.d1, ids)
            self.assertIn(self.d2, ids)
            self.assertIn(self.d3, ids)
            self.assertIn(self.d4, ids)

            query = MyModel.query
            ac = InRecordACL()
            query = ac.alter_query('update', query, self.u3, 'My', MyModel)
            items = query.values(MyModel.id)
            ids = [i[0] for i in items]
            self.assertNotIn(self.d1, ids)
            self.assertNotIn(self.d2, ids)
            self.assertNotIn(self.d3, ids)
            self.assertNotIn(self.d4, ids)

            query = MyModel.query
            ac = InRecordACL()
            query = ac.alter_query('delete', query, self.u3, 'My', MyModel)
            items = query.values(MyModel.id)
            ids = [i[0] for i in items]
            self.assertNotIn(self.d1, ids)
            self.assertNotIn(self.d2, ids)
            self.assertNotIn(self.d3, ids)
            self.assertNotIn(self.d4, ids)

    def test_in_record_acl_none(self):
        with self.app.test_request_context('/'):
            query = MyModel.query
            ac = InRecordACL()
            query = ac.alter_query('read', query, None, 'My', MyModel)
            items = query.values(MyModel.id)
            ids = [i[0] for i in items]
            self.assertNotIn(self.d1, ids)
            self.assertNotIn(self.d2, ids)
            self.assertIn(self.d3, ids)
            self.assertIn(self.d4, ids)

            query = MyModel.query
            ac = InRecordACL()
            query = ac.alter_query('update', query, None, 'My', MyModel)
            items = query.values(MyModel.id)
            ids = [i[0] for i in items]
            self.assertNotIn(self.d1, ids)
            self.assertNotIn(self.d2, ids)
            self.assertNotIn(self.d3, ids)
            self.assertNotIn(self.d4, ids)

            query = MyModel.query
            ac = InRecordACL()
            query = ac.alter_query('delete', query, None, 'My', MyModel)
            items = query.values(MyModel.id)
            ids = [i[0] for i in items]
            self.assertNotIn(self.d1, ids)
            self.assertNotIn(self.d2, ids)
            self.assertNotIn(self.d3, ids)
            self.assertNotIn(self.d4, ids)
