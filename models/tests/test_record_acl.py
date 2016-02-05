# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals

from sqlalchemy.exc import IntegrityError

from woodbox.db import db
from woodbox.models.record_acl_model import RecordACLModel
from woodbox.models.user_model import WBUserModel, WBRoleModel
from woodbox.models.tests.model_test_case import ModelTestCase


class TestUser(ModelTestCase):
    def test_creation(self):
        with self.app.test_request_context('/'):
            db.initialize()

            role1 = WBRoleModel(rolename='a')
            role2 = WBRoleModel(rolename='b')
            db.session.add_all([role1, role2])
            db.session.commit()

            ace1 = RecordACLModel(record_type='TestRecordType1',
                                  record_id=1, user_role_id=role1.id,
                                  permission='read')
            ace2 = RecordACLModel(record_type='TestRecordType1',
                                  record_id=1, user_role_id=role1.id,
                                  permission='update')
            ace3 = RecordACLModel(record_type='TestRecordType1',
                                  record_id=1, user_role_id=role1.id,
                                  permission='delete')
            ace4 = RecordACLModel(record_type='TestRecordType1',
                                  record_id=1, user_role_id=role2.id,
                                  permission='read')
            ace5 = RecordACLModel(record_type='TestRecordType1',
                                  record_id=1, user_role_id=role2.id,
                                  permission='update')
            ace6 = RecordACLModel(record_type='TestRecordType1',
                                  record_id=1, user_role_id=role2.id,
                                  permission='delete')
            db.session.add_all([ace1, ace2, ace3, ace4, ace5, ace6])
            db.session.commit()

            ace7 = RecordACLModel(record_type='TestRecordType1',
                                  record_id=1, user_role_id=role2.id,
                                  permission='transmogrify')
            db.session.add(ace7)
            self.assertRaises(IntegrityError, db.session.commit)

    def test_duplicate(self):
        with self.app.test_request_context('/'):
            db.initialize()

            role1 = WBRoleModel(rolename='a')
            db.session.add(role1)
            db.session.commit()

            ace1 = RecordACLModel(record_type='TestRecordType1',
                                  record_id=1, user_role_id=role1.id,
                                  permission='read')
            ace2 = RecordACLModel(record_type='TestRecordType1',
                                  record_id=1, user_role_id=role1.id,
                                  permission='read')
            db.session.add_all([ace1, ace2])
            self.assertRaises(IntegrityError, db.session.commit)
