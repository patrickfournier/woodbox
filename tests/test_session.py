# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals

import json

from datetime import datetime, timedelta
from time import sleep

from flask import request

from woodbox.db import db
from woodbox.models.session_model import WBSessionModel
from woodbox.models.user_model import WBUserModel
from woodbox.session import authenticate, validate_session, invalidate_session, add_session_management_urls
from woodbox.tests.flask_test_case import FlaskTestCase


class SessionTestCase(FlaskTestCase):
    def setUp(self):
        super(SessionTestCase, self).setUp()

        add_session_management_urls(self.app)

        with self.app.test_request_context('/'):
            db.initialize()

            # Create a user
            self.u1 = WBUserModel(username='a', password='a', roles=[])
            db.session.add(self.u1)
            db.session.commit()

            self.u1 = self.u1.id

    def test_authenticate_success(self):
        with self.app.test_client() as c:
            response = c.post('/authenticate', data={'username': 'a', 'password': 'a'})
            self.assertEqual(response.headers['content-type'], 'application/json')
            response = json.loads(response.data)
            session = WBSessionModel.query.filter_by(user_id=self.u1).first()
            self.assertIsNotNone(session)
            self.assertEqual(response['err'], 0)
            self.assertEqual(response['username'], 'a')
            self.assertEqual(response['session_id'], session.session_id)
            self.assertEqual(response['session_secret'], session.secret)

    def test_authenticate_bad_password(self):
        with self.app.test_client() as c:
            response = c.post('/authenticate', data={'username': 'a', 'password': '26537236'})
            self.assertEqual(response.headers['content-type'], 'application/json')
            response = json.loads(response.data)
            session = WBSessionModel.query.filter_by(user_id=self.u1).first()
            self.assertIsNone(session)
            self.assertEqual(response['err'], 1)

    def test_authenticate_bad_param(self):
        with self.app.test_client() as c:
            response = c.post('/authenticate', data={'username': 'a'})
            self.assertEqual(response.headers['content-type'], 'application/json')
            response = json.loads(response.data)
            session = WBSessionModel.query.filter_by(user_id=self.u1).first()
            self.assertIsNone(session)
            self.assertEqual(response['err'], 2)

    def test_validate(self):
        with self.app.test_client() as c:
            response = c.post('/authenticate', data={'username': 'a', 'password': 'a'})
            self.assertEqual(response.headers['content-type'], 'application/json')
            response = json.loads(response.data)
            sleep(2)

            response = c.post('/validate-session', data={'session_id': response['session_id']})
            self.assertEqual(response.headers['content-type'], 'application/json')
            response = json.loads(response.data)
            self.assertEqual(response['err'], 0)

            session = WBSessionModel.query.filter_by(user_id=self.u1).first()
            self.assertIsNotNone(session)
            self.assertAlmostEqual(session.accessed, datetime.utcnow(), delta=timedelta(seconds=1))

    def test_validate_bad_session(self):
        with self.app.test_client() as c:
            response = c.post('/validate-session', data={'session_id': 'garbage'})
            self.assertEqual(response.headers['content-type'], 'application/json')
            response = json.loads(response.data)
            self.assertEqual(response['err'], 3)

    def test_invalidate(self):
        with self.app.test_client() as c:
            response = c.post('/authenticate', data={'username': 'a', 'password': 'a'})
            self.assertEqual(response.headers['content-type'], 'application/json')
            response = json.loads(response.data)

            session_id = response['session_id']
            response = c.post('/invalidate-session', data={'session_id': session_id})
            self.assertEqual(response.headers['content-type'], 'application/json')
            response = json.loads(response.data)
            self.assertEqual(response['err'], 0)

            session = WBSessionModel.query.filter_by(user_id=self.u1).first()
            self.assertIsNone(session)

            response = c.post('/validate-session', data={'session_id': session_id})
            self.assertEqual(response.headers['content-type'], 'application/json')
            response = json.loads(response.data)
            self.assertEqual(response['err'], 3)

    def test_invalidate_bad_session(self):
        with self.app.test_client() as c:
            response = c.post('/invalidate-session', data={'session_id': 'garbage'})
            self.assertEqual(response.headers['content-type'], 'application/json')
            response = json.loads(response.data)
            self.assertEqual(response['err'], 0)
