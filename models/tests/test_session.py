# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals

from datetime import timedelta
from time import sleep

import arrow

from sqlalchemy.exc import ArgumentError, IntegrityError

from woodbox.db import db
from woodbox.models.session_model import WBSessionModel
from woodbox.models.user_model import WBUserModel
from woodbox.tests.flask_test_case import FlaskTestCase


class TestSession(FlaskTestCase):
    def test_creation(self):
        with self.app.test_request_context('/'):
            db.initialize()
            user = WBUserModel(username='alice', password='abc')
            db.session.add(user)
            db.session.commit()

            session = WBSessionModel(user.id)
            db.session.add(session)
            db.session.commit()

            read_session = WBSessionModel.query.get(session.id)
            self.assertEqual(read_session.user_id, user.id)
            self.assertEqual(len(read_session.session_id), 2*WBSessionModel.session_id_byte_length)
            self.assertEqual(len(read_session.secret), 2*WBSessionModel.secret_byte_length)
            self.assertEqual(read_session.created, read_session.accessed)
            self.assertAlmostEqual(read_session.created, arrow.utcnow(), delta=timedelta(seconds=1))

    def test_creation_invalid_user_id(self):
        with self.app.test_request_context('/'):
            db.initialize()
            self.assertRaises(ArgumentError, WBSessionModel, 42)
            db.session.rollback()

    def test_touch(self):
        with self.app.test_request_context('/'):
            db.initialize()
            user = WBUserModel(username='alice', password='abc')
            db.session.add(user)
            db.session.commit()

            WBSessionModel.session_max_idle_time = 3
            session = WBSessionModel(user.id)
            db.session.add(session)
            db.session.commit()

            sleep(1)
            self.assertTrue(session.touch())
            read_session = WBSessionModel.query.get(session.id)
            self.assertTrue(read_session)
            self.assertNotEqual(read_session.created, read_session.accessed)
            self.assertNotAlmostEqual(read_session.created, arrow.utcnow(), delta=timedelta(seconds=1))
            self.assertAlmostEqual(read_session.accessed, arrow.utcnow(), delta=timedelta(seconds=2))

            sleep(1)
            self.assertTrue(session.touch())
            read_session = WBSessionModel.query.get(session.id)
            self.assertTrue(read_session)
            self.assertNotEqual(read_session.created, read_session.accessed)
            self.assertNotAlmostEqual(read_session.created, arrow.utcnow(), delta=timedelta(seconds=1))
            self.assertAlmostEqual(read_session.accessed, arrow.utcnow(), delta=timedelta(seconds=2))

            sleep(4)
            self.assertFalse(session.touch())
            read_session = WBSessionModel.query.get(session.id)
            self.assertFalse(read_session)
