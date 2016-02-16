# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals

import json

from flask import g
from flask_restful import Api
from marshmallow.validate import Length
from marshmallow_jsonapi import fields

from woodbox.access_control.api import Acl
from woodbox.access_control.record import IsOwner
from woodbox.authenticator import HMACAuthenticator
from woodbox.db import db
from woodbox.jsonapi_schema import JSONAPISchema
from woodbox.models.user_model import WBRoleModel, WBUserModel
from woodbox.record_api import make_api
from woodbox.session import add_session_management_urls
from woodbox.tests.flask_test_case import FlaskTestCase

class MyTestModel(db.Model):
    id = db.Column(db.Integer, db.Sequence('my_test_model_id_seq'), primary_key=True)
    owner_id = db.Column(db.Integer, db.ForeignKey('wb_user_model.id'), nullable=False)
    owner = db.relationship('WBUserModel', foreign_keys='MyTestModel.owner_id')
    title = db.Column(db.String(256), unique=False, nullable=True)
    author = db.Column(db.String(256), unique=False, nullable=True)

class UserSchema(JSONAPISchema):
    username = fields.String(attribute='username')

class MyTestSchema(JSONAPISchema):
    title = fields.String(attribute='title', validate=Length(10, 100))
    author = fields.String(attribute='author', required=True)
    owner = fields.Nested('UserSchema', many=False)
    owner_id = fields.Integer(attribute='owner_id')

my_test_acl = Acl()
my_test_acl.grants({
    'admin': {
        'Test': ['create', 'read', 'update', 'delete'],
    },
    'manager': {
        'Test': ['read'],
    },
})


class RecordAPITestCase(FlaskTestCase):
    def setUp(self):
        super(RecordAPITestCase, self).setUp()
        self.api = Api(self.app)

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
            self.u1 = WBUserModel(username='Alice', password='a', roles=[self.r1])
            db.session.add(self.u1)
            self.u2 = WBUserModel(username='Bob', password='a', roles=[self.r2])
            db.session.add(self.u2)
            self.u3 = WBUserModel(username='Charlie', password='a', roles=[self.r3])
            db.session.add(self.u3)
            db.session.commit()

            self.u1 = self.u1.id
            self.u2 = self.u2.id
            self.u3 = self.u3.id

            # Create some data
            self.d1 = MyTestModel(title='Alice in Wonderland', author='Lewis Caroll', owner_id=self.u1)
            db.session.add(self.d1)
            self.d2 = MyTestModel(title='SpongeBob', author='Stephen Hillenburg', owner_id=self.u2)
            db.session.add(self.d2)
            self.d3 = MyTestModel(title='Où est Charlie?', author='Martin Handford', owner_id=self.u3)
            db.session.add(self.d3)
            db.session.commit()

            self.d1 = self.d1.id
            self.d2 = self.d2.id
            self.d3 = self.d3.id

    def test_record_api(self):
        make_api(self.api, 'Test', MyTestModel, MyTestSchema)

        with self.app.test_client() as c:
            # get all
            response = c.get('/my-tests')
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.data, '{"data": [{"attributes": {"owner": {"data": {"attributes": {"username": "Alice"}, "type": "users", "id": "1"}}, "owner-id": 1, "author": "Lewis Caroll", "title": "Alice in Wonderland"}, "type": "my-tests", "id": "1"}, {"attributes": {"owner": {"data": {"attributes": {"username": "Bob"}, "type": "users", "id": "2"}}, "owner-id": 2, "author": "Stephen Hillenburg", "title": "SpongeBob"}, "type": "my-tests", "id": "2"}, {"attributes": {"owner": {"data": {"attributes": {"username": "Charlie"}, "type": "users", "id": "3"}}, "owner-id": 3, "author": "Martin Handford", "title": "O\\u00f9 est Charlie?"}, "type": "my-tests", "id": "3"}]}\n')

            # get one
            response = c.get('/my-tests/{}'.format(self.d1))
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.data, '{"data": {"attributes": {"owner": {"data": {"attributes": {"username": "Alice"}, "type": "users", "id": "1"}}, "owner-id": 1, "author": "Lewis Caroll", "title": "Alice in Wonderland"}, "type": "my-tests", "id": "1"}}\n')

            # patch
            patch_data = {"data":
                          {"attributes":
                           {"title": "Alice's Adventures in Wonderland"},
                           "type": "my-tests"}}
            response = c.patch('/my-tests/{}'.format(self.d1),
                               data=json.dumps(patch_data),
                               headers={'Content-Type': 'application/vnd.api+json'})
            self.assertEqual(response.status_code, 204)
            self.assertEqual(response.headers['Content-Location'], '/my-tests/{}'.format(self.d1))

            # check if patch was successful
            response = c.get('/my-tests/{}'.format(self.d1))
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.data, '{"data": {"attributes": {"owner": {"data": {"attributes": {"username": "Alice"}, "type": "users", "id": "1"}}, "owner-id": 1, "author": "Lewis Caroll", "title": "Alice\'s Adventures in Wonderland"}, "type": "my-tests", "id": "1"}}\n')

            # delete
            response = c.delete('/my-tests/{}'.format(self.d1))
            self.assertEqual(response.status_code, 204)
            self.assertEqual(response.data, '')

            # get non existing item / check if delete was successful
            response = c.get('/my-tests/{}'.format(self.d1))
            self.assertEqual(response.status_code, 404)

            # post
            post_data = {"data":
                         {"attributes":
                          {"title": "Dennis the Menace",
                           "author": "Hank Ketcham",
                           "owner_id": "2",
                          },
                          "type": "my-tests"}}
            response = c.post('/my-tests',
                               data=json.dumps(post_data),
                               headers={'Content-Type': 'application/vnd.api+json'})
            self.assertEqual(response.status_code, 204)
            self.assertEqual(response.headers['Content-Location'], '/my-tests/4')

            # check if post was successful
            response = c.get(response.headers['Content-Location'])
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.data, '{"data": {"attributes": {"owner": {"data": {"attributes": {"username": "Bob"}, "type": "users", "id": "2"}}, "owner-id": 2, "author": "Hank Ketcham", "title": "Dennis the Menace"}, "type": "my-tests", "id": "4"}}\n')


    def test_record_api_delete_fail(self):
        make_api(self.api, 'Test', MyTestModel, MyTestSchema)

        with self.app.test_client() as c:
            # delete non existing item
            response = c.delete('/my-tests/199')
            self.assertEqual(response.status_code, 404)


    def test_record_api_patch_fail(self):
        make_api(self.api, 'Test', MyTestModel, MyTestSchema)

        with self.app.test_client() as c:
            # wrong content type
            patch_data = {"data":
                          {"attributes":
                           {"title": "Alice's Adventures in Wonderland"},
                           "type": "my-tests"}}
            response = c.patch('/my-tests/{}'.format(self.d1),
                               data=json.dumps(patch_data),
                               headers={'Content-Type': 'application/json'})
            self.assertEqual(response.status_code, 415)
            self.assertEqual(response.headers['Accept-Patch'], 'application/vnd.api+json')

            # non validating patch
            patch_data = {"data":
                          {"attributes":
                           {"title": "Too short"},
                           "type": "my-tests"}}
            response = c.patch('/my-tests/{}'.format(self.d1),
                               data=json.dumps(patch_data),
                               headers={'Content-Type': 'application/vnd.api+json'})
            self.assertEqual(response.status_code, 415)

            # patch non existing item
            patch_data = {"data":
                          {"attributes":
                           {"title": "Long enough"},
                           "type": "my-tests"}}
            response = c.patch('/my-tests/199',
                               data=json.dumps(patch_data),
                               headers={'Content-Type': 'application/vnd.api+json'})
            self.assertEqual(response.status_code, 404)


    def test_record_api_post_fail(self):
        make_api(self.api, 'Test', MyTestModel, MyTestSchema)

        with self.app.test_client() as c:
            # wrong content type
            post_data = {"data":
                         {"attributes":
                          {"title": "Dennis the Menace",
                           "author": "Hank Ketcham",
                           "owner_id": "2",
                          },
                          "type": "my-tests"}}
            response = c.post('/my-tests',
                               data=json.dumps(post_data),
                               headers={'Content-Type': 'application/json'})
            self.assertEqual(response.status_code, 415)
            self.assertEqual(response.headers['Accept-Patch'], 'application/vnd.api+json')

            # non validating content
            post_data = {"data":
                         {"attributes":
                          {"title": "Too short",
                           "owner_id": "2",
                          },
                          "type": "my-tests"}}
            response = c.post('/my-tests',
                               data=json.dumps(post_data),
                               headers={'Content-Type': 'application/vnd.api+json'})
            self.assertEqual(response.status_code, 415)


    def test_record_api_with_acl_user_1(self):
        add_session_management_urls(self.app)

        make_api(self.api, 'Test', MyTestModel, MyTestSchema,
                 record_authorizer=IsOwner(),
                 api_authorizers=[my_test_acl.authorize])

        with self.app.test_client() as c:
            response = c.post('/authenticate', data={'username': 'Alice', 'password': 'a'})
            response = json.loads(response.data)
            session_id = response['session_id']
            secret = response['session_secret']

            # get all Alice's records
            headers = HMACAuthenticator.get_authorization_headers(session_id, secret, '/my-tests')
            response = c.get('/my-tests', headers=headers)
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.data, '{"data": [{"attributes": {"owner": {"data": {"attributes": {"username": "Alice"}, "type": "users", "id": "1"}}, "owner-id": 1, "author": "Lewis Caroll", "title": "Alice in Wonderland"}, "type": "my-tests", "id": "1"}]}\n')

            # get one allowed record
            headers = HMACAuthenticator.get_authorization_headers(session_id, secret, '/my-tests/{}'.format(self.d1))
            response = c.get('/my-tests/{}'.format(self.d1), headers=headers)
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.data, '{"data": {"attributes": {"owner": {"data": {"attributes": {"username": "Alice"}, "type": "users", "id": "1"}}, "owner-id": 1, "author": "Lewis Caroll", "title": "Alice in Wonderland"}, "type": "my-tests", "id": "1"}}\n')

            # get a forbidden record
            headers = HMACAuthenticator.get_authorization_headers(session_id, secret, '/my-tests/{}'.format(self.d2))
            response = c.get('/my-tests/{}'.format(self.d2), headers=headers)
            self.assertEqual(response.status_code, 404)

            # patch Alice's records
            patch_data = json.dumps({"data":
                                     {"attributes":
                                      {"title": "Alice's Adventures in Wonderland"},
                                      "type": "my-tests"}})
            headers = HMACAuthenticator.get_authorization_headers(session_id,
                                                                  secret,
                                                                  '/my-tests/{}'.format(self.d1),
                                                                  method='PATCH',
                                                                  content_type='application/vnd.api+json',
                                                                  body=patch_data)
            headers['Content-Type'] = 'application/vnd.api+json'
            response = c.patch('/my-tests/{}'.format(self.d1),
                               data=patch_data, headers=headers)
            self.assertEqual(response.status_code, 204)
            self.assertEqual(response.headers['Content-Location'], '/my-tests/{}'.format(self.d1))

            # patch someone else's record: this is forbidden (because not owner)
            patch_data = json.dumps({"data":
                                     {"attributes":
                                      {"title": "SpongeBob SquarePants"},
                                      "type": "my-tests"}})
            headers = HMACAuthenticator.get_authorization_headers(session_id,
                                                                  secret,
                                                                  '/my-tests/{}'.format(self.d2),
                                                                  method='PATCH',
                                                                  content_type='application/vnd.api+json',
                                                                  body=patch_data)
            headers['Content-Type'] = 'application/vnd.api+json'
            response = c.patch('/my-tests/{}'.format(self.d2),
                               data=patch_data, headers=headers)
            self.assertEqual(response.status_code, 404, response.data)


            # delete own file
            headers = HMACAuthenticator.get_authorization_headers(session_id,
                                                                  secret,
                                                                  '/my-tests/{}'.format(self.d1),
                                                                  method='DELETE')
            response = c.delete('/my-tests/{}'.format(self.d1), headers=headers)
            self.assertEqual(response.status_code, 204)
            self.assertEqual(response.data, '')

            # delete someone else file
            headers = HMACAuthenticator.get_authorization_headers(session_id,
                                                                  secret,
                                                                  '/my-tests/{}'.format(self.d2),
                                                                  method='DELETE')
            response = c.delete('/my-tests/{}'.format(self.d2), headers=headers)
            self.assertEqual(response.status_code, 404)


            # post
            post_data = json.dumps({"data":
                                    {"attributes":
                                     {"title": "Dennis the Menace",
                                      "author": "Hank Ketcham",
                                      "owner_id": "2",
                                     },
                                     "type": "my-tests"}})
            headers = HMACAuthenticator.get_authorization_headers(session_id,
                                                                  secret,
                                                                  '/my-tests',
                                                                  method='POST',
                                                                  content_type='application/vnd.api+json',
                                                                  body=post_data)
            headers['Content-Type'] = 'application/vnd.api+json'
            response = c.post('/my-tests', data=post_data, headers=headers)
            self.assertEqual(response.status_code, 204)
            self.assertEqual(response.headers['Content-Location'], '/my-tests/4')


    def test_record_api_with_acl_user_2(self):
        add_session_management_urls(self.app)

        make_api(self.api, 'Test', MyTestModel, MyTestSchema,
                 record_authorizer=IsOwner(),
                 api_authorizers=[my_test_acl.authorize])

        with self.app.test_client() as c:
            response = c.post('/authenticate', data={'username': 'Bob', 'password': 'a'})
            response = json.loads(response.data)
            session_id = response['session_id']
            secret = response['session_secret']

            # get all Bob's records
            headers = HMACAuthenticator.get_authorization_headers(session_id, secret, '/my-tests')
            response = c.get('/my-tests', headers=headers)
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.data, '{"data": [{"attributes": {"owner": {"data": {"attributes": {"username": "Bob"}, "type": "users", "id": "2"}}, "owner-id": 2, "author": "Stephen Hillenburg", "title": "SpongeBob"}, "type": "my-tests", "id": "2"}]}\n')

            # get one allowed record
            headers = HMACAuthenticator.get_authorization_headers(session_id, secret, '/my-tests/{}'.format(self.d2))
            response = c.get('/my-tests/{}'.format(self.d2), headers=headers)
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.data, '{"data": {"attributes": {"owner": {"data": {"attributes": {"username": "Bob"}, "type": "users", "id": "2"}}, "owner-id": 2, "author": "Stephen Hillenburg", "title": "SpongeBob"}, "type": "my-tests", "id": "2"}}\n')

            # patch records
            patch_data = json.dumps({"data":
                                     {"attributes":
                                      {"title": "SpongeBob SquarePants"},
                                      "type": "my-tests"}})
            headers = HMACAuthenticator.get_authorization_headers(session_id,
                                                                  secret,
                                                                  '/my-tests/{}'.format(self.d2),
                                                                  method='PATCH',
                                                                  content_type='application/vnd.api+json',
                                                                  body=patch_data)
            headers['Content-Type'] = 'application/vnd.api+json'
            response = c.patch('/my-tests/{}'.format(self.d2),
                               data=patch_data, headers=headers)
            self.assertEqual(response.status_code, 405)

            # delete own file
            headers = HMACAuthenticator.get_authorization_headers(session_id,
                                                                  secret,
                                                                  '/my-tests/{}'.format(self.d2),
                                                                  method='DELETE')
            response = c.delete('/my-tests/{}'.format(self.d2), headers=headers)
            self.assertEqual(response.status_code, 405)

            # post
            post_data = json.dumps({"data":
                                    {"attributes":
                                     {"title": "Dennis the Menace",
                                      "author": "Hank Ketcham",
                                      "owner_id": "2",
                                     },
                                     "type": "my-tests"}})
            headers = HMACAuthenticator.get_authorization_headers(session_id,
                                                                  secret,
                                                                  '/my-tests',
                                                                  method='POST',
                                                                  content_type='application/vnd.api+json',
                                                                  body=post_data)
            headers['Content-Type'] = 'application/vnd.api+json'
            response = c.post('/my-tests', data=post_data, headers=headers)
            self.assertEqual(response.status_code, 405)
