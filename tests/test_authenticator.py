# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals

import json

from datetime import datetime
from hashlib import sha256, sha1
from hmac import new as hmac_new

import pytz

from flask import g, request

from woodbox.authenticator import HMACAuthenticator
from woodbox.db import db
from woodbox.models.session_model import WBSessionModel
from woodbox.models.user_model import WBUserModel
from woodbox.session import add_session_management_urls
from woodbox.tests.flask_test_case import FlaskTestCase

auth = HMACAuthenticator()

@auth.authenticate
def needs_authenticated_user_function():
    if g.user:
        return str(g.user)
    else:
        return 'anonymous'


class SessionTestCase(FlaskTestCase):
    def setUp(self):
        super(SessionTestCase, self).setUp()

        add_session_management_urls(self.app)
        self.app.add_url_rule('/test', 'test', needs_authenticated_user_function, methods=['GET'])

        with self.app.test_request_context('/'):
            db.initialize()

            # Create a user
            self.u1 = WBUserModel(username='a', password='a', roles=[])
            db.session.add(self.u1)
            db.session.commit()

            self.u1 = self.u1.id

    def test_authenticator_anonymous(self):
        with self.app.test_client() as c:
            response = c.post('/authenticate', data={'username': 'a', 'password': 'a'})
            self.assertEqual(response.headers['content-type'], 'application/json', response.data)

            response = c.get('/test')
            self.assertEqual(response.data, 'anonymous')

    def test_authenticator_user1(self):
        with self.app.test_client() as c:
            response = c.post('/authenticate', data={'username': 'a', 'password': 'a'})
            self.assertEqual(response.headers['content-type'], 'application/json', response.data)
            response = json.loads(response.data)
            session_id = response['session_id']
            secret = response['session_secret']

            payload_hash = sha256('').hexdigest()
            now = datetime.utcnow().replace(tzinfo=pytz.utc).strftime("%Y%m%dT%H%M%S")

            headers = {
                'content-type': '',
                'host': 'localhost',
                'x-woodbox-content-sha256': payload_hash,
                'x-woodbox-timestamp': now
            }

            signed_headers = sorted(['content-type', 'host','x-woodbox-content-sha256','x-woodbox-timestamp'])

            canonical_headers = []
            for h in signed_headers:
                canonical_headers.append(h+':'+headers[h])
            canonical_headers = '\n'.join(canonical_headers).encode('utf-8')
            signed_headers = ';'.join(signed_headers)
            canonical_request = '\n'.join(['GET', '/test', 'a=2&b=1',
                                           canonical_headers,
                                           signed_headers,
                                           payload_hash])

            string_to_sign = '\n'.join(['WOODBOX-HMAC-SHA256', now, sha256(canonical_request).hexdigest()])
            signing_key = secret.encode('utf-8')
            signature = hmac_new(signing_key, string_to_sign, sha256).hexdigest()

            auth = {
                'Credential': session_id,
                'SignedHeaders': signed_headers,
                'Signature': signature
            }
            auth = [k+'='+v for k,v in auth.iteritems()]
            auth = ','.join(auth)
            auth_str = ' '.join(['Woodbox-HMAC-SHA256', auth]);

            request_headers = {
                'Authorization': auth_str,
                'x-woodbox-content-sha256': payload_hash,
                'x-woodbox-timestamp': now
            }
            response = c.get('/test?b=1&a=2', headers=request_headers)
            self.assertEqual(g.user_reason, 'Authenticated')
            self.assertEqual(response.data, '1', g.user_reason)

    def test_authenticator_unsorted_query_string(self):
        with self.app.test_client() as c:
            response = c.post('/authenticate', data={'username': 'a', 'password': 'a'})
            self.assertEqual(response.headers['content-type'], 'application/json', response.data)
            response = json.loads(response.data)
            session_id = response['session_id']
            secret = response['session_secret']

            payload_hash = sha256('').hexdigest()
            now = datetime.utcnow().replace(tzinfo=pytz.utc).strftime("%Y%m%dT%H%M%S")

            headers = {
                'content-type': '',
                'host': 'localhost',
                'x-woodbox-content-sha256': payload_hash,
                'x-woodbox-timestamp': now
            }

            signed_headers = sorted(['content-type', 'host','x-woodbox-content-sha256','x-woodbox-timestamp'])

            canonical_headers = []
            for h in signed_headers:
                canonical_headers.append(h+':'+headers[h])
            canonical_headers = '\n'.join(canonical_headers).encode('utf-8')
            signed_headers = ';'.join(signed_headers)
            canonical_request = '\n'.join(['GET', '/test', 'b=1&a=2',
                                           canonical_headers,
                                           signed_headers,
                                           payload_hash])

            string_to_sign = '\n'.join(['WOODBOX-HMAC-SHA256', now, sha256(canonical_request).hexdigest()])
            signing_key = secret.encode('utf-8')
            signature = hmac_new(signing_key, string_to_sign, sha256).hexdigest()

            auth = {
                'Credential': session_id,
                'SignedHeaders': signed_headers,
                'Signature': signature
            }
            auth = [k+'='+v for k,v in auth.iteritems()]
            auth = ','.join(auth)
            auth_str = ' '.join(['Woodbox-HMAC-SHA256', auth]);

            request_headers = {
                'Authorization': auth_str,
                'x-woodbox-content-sha256': payload_hash,
                'x-woodbox-timestamp': now
            }
            response = c.get('/test?b=1&a=2', headers=request_headers)
            self.assertEqual(g.user_reason, 'Signature do not match')
            self.assertEqual(response.data, 'anonymous', g.user_reason)

    def test_authenticator_invalid_session(self):
        with self.app.test_client() as c:
            response = c.post('/authenticate', data={'username': 'a', 'password': 'a'})
            response = json.loads(response.data)
            session_id = response['session_id']
            secret = response['session_secret']

            c.post('/invalidate-session', data={'session_id': session_id})

            payload_hash = sha256('').hexdigest()
            now = datetime.utcnow().replace(tzinfo=pytz.utc).strftime("%Y%m%dT%H%M%S")

            headers = {
                'content-type': '',
                'host': 'localhost',
                'x-woodbox-content-sha256': payload_hash,
                'x-woodbox-timestamp': now
            }

            signed_headers = sorted(['content-type', 'host','x-woodbox-content-sha256','x-woodbox-timestamp'])

            canonical_headers = []
            for h in signed_headers:
                canonical_headers.append(h+':'+headers[h])
            canonical_headers = '\n'.join(canonical_headers).encode('utf-8')
            signed_headers = ';'.join(signed_headers)
            canonical_request = '\n'.join(['GET', '/test', '',
                                           canonical_headers,
                                           signed_headers,
                                           payload_hash])

            string_to_sign = '\n'.join(['WOODBOX-HMAC-SHA256', now, sha256(canonical_request).hexdigest()])
            signing_key = secret.encode('utf-8')
            signature = hmac_new(signing_key, string_to_sign, sha256).hexdigest()

            auth = {
                'Credential': session_id,
                'SignedHeaders': signed_headers,
                'Signature': signature
            }
            auth = [k+'='+v for k,v in auth.iteritems()]
            auth = ','.join(auth)
            auth_str = ' '.join(['Woodbox-HMAC-SHA256', auth]);

            request_headers = {
                'Authorization': auth_str,
                'x-woodbox-content-sha256': payload_hash,
                'x-woodbox-timestamp': now
            }
            response = c.get('/test', headers=request_headers)
            self.assertEqual(g.user_reason, 'Invalid credential.')
            self.assertEqual(response.data, 'anonymous', g.user_reason)

    def test_authenticator_invalid_method(self):
        with self.app.test_client() as c:
            response = c.post('/authenticate', data={'username': 'a', 'password': 'a'})
            response = json.loads(response.data)
            session_id = response['session_id']
            secret = response['session_secret']

            c.post('/invalidate-session', data={'session_id': session_id})

            payload_hash = sha256('').hexdigest()
            now = datetime.utcnow().replace(tzinfo=pytz.utc).strftime("%Y%m%dT%H%M%S")

            headers = {
                'content-type': '',
                'host': 'localhost',
                'x-woodbox-content-sha256': payload_hash,
                'x-woodbox-timestamp': now
            }

            signed_headers = sorted(['content-type', 'host','x-woodbox-content-sha256','x-woodbox-timestamp'])

            canonical_headers = []
            for h in signed_headers:
                canonical_headers.append(h+':'+headers[h])
            canonical_headers = '\n'.join(canonical_headers).encode('utf-8')
            signed_headers = ';'.join(signed_headers)
            canonical_request = '\n'.join(['GET', '/test', '',
                                           canonical_headers,
                                           signed_headers,
                                           payload_hash])

            string_to_sign = '\n'.join(['WOODBOX-HMAC-SHA1', now, sha1(canonical_request).hexdigest()])
            signing_key = secret.encode('utf-8')
            signature = hmac_new(signing_key, string_to_sign, sha256).hexdigest()

            auth = {
                'Credential': session_id,
                'SignedHeaders': signed_headers,
                'Signature': signature
            }
            auth = [k+'='+v for k,v in auth.iteritems()]
            auth = ','.join(auth)
            auth_str = ' '.join(['Woodbox-HMAC-SHA1', auth]);

            request_headers = {
                'Authorization': auth_str,
                'x-woodbox-content-sha256': payload_hash,
                'x-woodbox-timestamp': now
            }
            response = c.get('/test', headers=request_headers)
            self.assertEqual(g.user_reason, 'Unknown authentication method: hmac-sha1')
            self.assertEqual(response.data, 'anonymous', g.user_reason)

    def test_authenticator_unsorted_headers(self):
        with self.app.test_client() as c:
            response = c.post('/authenticate', data={'username': 'a', 'password': 'a'})
            response = json.loads(response.data)
            session_id = response['session_id']
            secret = response['session_secret']

            c.post('/invalidate-session', data={'session_id': session_id})

            payload_hash = sha256('').hexdigest()
            now = datetime.utcnow().replace(tzinfo=pytz.utc).strftime("%Y%m%dT%H%M%S")

            headers = {
                'content-type': '',
                'host': 'localhost',
                'x-woodbox-content-sha256': payload_hash,
                'x-woodbox-timestamp': now
            }

            signed_headers = ['x-woodbox-content-sha256', 'content-type', 'host', 'x-woodbox-timestamp']

            canonical_headers = []
            for h in signed_headers:
                canonical_headers.append(h+':'+headers[h])
            canonical_headers = '\n'.join(canonical_headers).encode('utf-8')
            signed_headers = ';'.join(signed_headers)
            canonical_request = '\n'.join(['GET', '/test', '',
                                           canonical_headers,
                                           signed_headers,
                                           payload_hash])

            string_to_sign = '\n'.join(['WOODBOX-HMAC-SHA256', now, sha256(canonical_request).hexdigest()])
            signing_key = secret.encode('utf-8')
            signature = hmac_new(signing_key, string_to_sign, sha256).hexdigest()

            auth = {
                'Credential': session_id,
                'SignedHeaders': signed_headers,
                'Signature': signature
            }
            auth = [k+'='+v for k,v in auth.iteritems()]
            auth = ','.join(auth)
            auth_str = ' '.join(['Woodbox-HMAC-SHA256', auth]);

            request_headers = {
                'Authorization': auth_str,
                'x-woodbox-content-sha256': payload_hash,
                'x-woodbox-timestamp': now
            }
            response = c.get('/test', headers=request_headers)
            self.assertEqual(g.user_reason, 'Invalid credential.')
            self.assertEqual(response.data, 'anonymous', g.user_reason)

    def test_authenticator_missing_header_value(self):
        with self.app.test_client() as c:
            response = c.post('/authenticate', data={'username': 'a', 'password': 'a'})
            response = json.loads(response.data)
            session_id = response['session_id']
            secret = response['session_secret']

            c.post('/invalidate-session', data={'session_id': session_id})

            payload_hash = sha256('').hexdigest()
            now = datetime.utcnow().replace(tzinfo=pytz.utc).strftime("%Y%m%dT%H%M%S")

            headers = {
                'content-type': '',
                'host': 'localhost',
                'x-woodbox-content-sha256': payload_hash,
                'x-woodbox-timestamp': now,
                'x-this-value-is-missing': 'missing-in-request'
            }

            signed_headers = sorted(['x-woodbox-content-sha256', 'content-type', 'host', 'x-woodbox-timestamp', 'x-this-value-is-missing'])

            canonical_headers = []
            for h in signed_headers:
                canonical_headers.append(h+':'+headers[h])
            canonical_headers = '\n'.join(canonical_headers).encode('utf-8')
            signed_headers = ';'.join(signed_headers)
            canonical_request = '\n'.join(['GET', '/test', '',
                                           canonical_headers,
                                           signed_headers,
                                           payload_hash])

            string_to_sign = '\n'.join(['WOODBOX-HMAC-SHA256', now, sha256(canonical_request).hexdigest()])
            signing_key = secret.encode('utf-8')
            signature = hmac_new(signing_key, string_to_sign, sha256).hexdigest()

            auth = {
                'Credential': session_id,
                'SignedHeaders': signed_headers,
                'Signature': signature
            }
            auth = [k+'='+v for k,v in auth.iteritems()]
            auth = ','.join(auth)
            auth_str = ' '.join(['Woodbox-HMAC-SHA256', auth]);

            request_headers = {
                'Authorization': auth_str,
                'x-woodbox-content-sha256': payload_hash,
                'x-woodbox-timestamp': now
            }
            response = c.get('/test', headers=request_headers)
            self.assertEqual(g.user_reason, 'Missing headers: x-this-value-is-missing')
            self.assertEqual(response.data, 'anonymous', g.user_reason)

    def test_authenticator_missing_required_headers(self):
        with self.app.test_client() as c:
            response = c.post('/authenticate', data={'username': 'a', 'password': 'a'})
            response = json.loads(response.data)
            session_id = response['session_id']
            secret = response['session_secret']

            c.post('/invalidate-session', data={'session_id': session_id})

            payload_hash = sha256('').hexdigest()
            now = datetime.utcnow().replace(tzinfo=pytz.utc).strftime("%Y%m%dT%H%M%S")

            headers = {
                'content-type': '',
                'host': 'localhost',
                'x-woodbox-content-sha256': payload_hash,
                'x-woodbox-timestamp': now
            }

            signed_headers = sorted(['content-type', 'host', 'x-woodbox-timestamp'])

            canonical_headers = []
            for h in signed_headers:
                canonical_headers.append(h+':'+headers[h])
            canonical_headers = '\n'.join(canonical_headers).encode('utf-8')
            signed_headers = ';'.join(signed_headers)
            canonical_request = '\n'.join(['GET', '/test', '',
                                           canonical_headers,
                                           signed_headers,
                                           payload_hash])

            string_to_sign = '\n'.join(['WOODBOX-HMAC-SHA256', now, sha256(canonical_request).hexdigest()])
            signing_key = secret.encode('utf-8')
            signature = hmac_new(signing_key, string_to_sign, sha256).hexdigest()

            auth = {
                'Credential': session_id,
                'SignedHeaders': signed_headers,
                'Signature': signature
            }
            auth = [k+'='+v for k,v in auth.iteritems()]
            auth = ','.join(auth)
            auth_str = ' '.join(['Woodbox-HMAC-SHA256', auth]);

            request_headers = {
                'Authorization': auth_str,
                'x-woodbox-content-sha256': payload_hash,
                'x-woodbox-timestamp': now
            }
            response = c.get('/test', headers=request_headers)
            self.assertEqual(g.user_reason, 'Some required headers were not signed: x-woodbox-content-sha256')
            self.assertEqual(response.data, 'anonymous', g.user_reason)

    def test_authenticator_missing_auth_param(self):
        with self.app.test_client() as c:
            response = c.post('/authenticate', data={'username': 'a', 'password': 'a'})
            self.assertEqual(response.headers['content-type'], 'application/json', response.data)
            response = json.loads(response.data)
            session_id = response['session_id']
            secret = response['session_secret']

            payload_hash = sha256('').hexdigest()
            now = datetime.utcnow().replace(tzinfo=pytz.utc).strftime("%Y%m%dT%H%M%S")

            headers = {
                'content-type': '',
                'host': 'localhost',
                'x-woodbox-content-sha256': payload_hash,
                'x-woodbox-timestamp': now
            }

            signed_headers = sorted(['content-type', 'host','x-woodbox-content-sha256','x-woodbox-timestamp'])

            canonical_headers = []
            for h in signed_headers:
                canonical_headers.append(h+':'+headers[h])
            canonical_headers = '\n'.join(canonical_headers).encode('utf-8')
            signed_headers = ';'.join(signed_headers)
            canonical_request = '\n'.join(['GET', '/test', '',
                                           canonical_headers,
                                           signed_headers,
                                           payload_hash])

            string_to_sign = '\n'.join(['WOODBOX-HMAC-SHA256', now, sha256(canonical_request).hexdigest()])
            signing_key = secret.encode('utf-8')
            signature = hmac_new(signing_key, string_to_sign, sha256).hexdigest()

            auth = {
                'Credential': session_id,
                'Signature': signature
            }
            auth = [k+'='+v for k,v in auth.iteritems()]
            auth = ','.join(auth)
            auth_str = ' '.join(['Woodbox-HMAC-SHA256', auth]);

            request_headers = {
                'Authorization': auth_str,
                'x-woodbox-content-sha256': payload_hash,
                'x-woodbox-timestamp': now
            }
            response = c.get('/test', headers=request_headers)
            self.assertEqual(g.user_reason, 'Missing parameter: signedheaders')
            self.assertEqual(response.data, 'anonymous', g.user_reason)

    def test_authenticator_request_too_old(self):
        with self.app.test_client() as c:
            response = c.post('/authenticate', data={'username': 'a', 'password': 'a'})
            self.assertEqual(response.headers['content-type'], 'application/json', response.data)
            response = json.loads(response.data)
            session_id = response['session_id']
            secret = response['session_secret']

            payload_hash = sha256('').hexdigest()
            now = "20150101T123456"

            headers = {
                'content-type': '',
                'host': 'localhost',
                'x-woodbox-content-sha256': payload_hash,
                'x-woodbox-timestamp': now
            }

            signed_headers = sorted(['content-type', 'host','x-woodbox-content-sha256','x-woodbox-timestamp'])

            canonical_headers = []
            for h in signed_headers:
                canonical_headers.append(h+':'+headers[h])
            canonical_headers = '\n'.join(canonical_headers).encode('utf-8')
            signed_headers = ';'.join(signed_headers)
            canonical_request = '\n'.join(['GET', '/test', '',
                                           canonical_headers,
                                           signed_headers,
                                           payload_hash])

            string_to_sign = '\n'.join(['WOODBOX-HMAC-SHA256', now, sha256(canonical_request).hexdigest()])
            signing_key = secret.encode('utf-8')
            signature = hmac_new(signing_key, string_to_sign, sha256).hexdigest()

            auth = {
                'Credential': session_id,
                'SignedHeaders': signed_headers,
                'Signature': signature
            }
            auth = [k+'='+v for k,v in auth.iteritems()]
            auth = ','.join(auth)
            auth_str = ' '.join(['Woodbox-HMAC-SHA256', auth]);

            request_headers = {
                'Authorization': auth_str,
                'x-woodbox-content-sha256': payload_hash,
                'x-woodbox-timestamp': now
            }
            response = c.get('/test', headers=request_headers)
            self.assertEqual(g.user_reason, 'Request is too old.')
            self.assertEqual(response.data, 'anonymous', g.user_reason)

    def test_authenticator_content_hash_mismatch(self):
        with self.app.test_client() as c:
            response = c.post('/authenticate', data={'username': 'a', 'password': 'a'})
            self.assertEqual(response.headers['content-type'], 'application/json', response.data)
            response = json.loads(response.data)
            session_id = response['session_id']
            secret = response['session_secret']

            payload_hash = sha256('bad').hexdigest()
            now = datetime.utcnow().replace(tzinfo=pytz.utc).strftime("%Y%m%dT%H%M%S")

            headers = {
                'content-type': '',
                'host': 'localhost',
                'x-woodbox-content-sha256': payload_hash,
                'x-woodbox-timestamp': now
            }

            signed_headers = sorted(['content-type', 'host','x-woodbox-content-sha256','x-woodbox-timestamp'])

            canonical_headers = []
            for h in signed_headers:
                canonical_headers.append(h+':'+headers[h])
            canonical_headers = '\n'.join(canonical_headers).encode('utf-8')
            signed_headers = ';'.join(signed_headers)
            canonical_request = '\n'.join(['GET', '/test', '',
                                           canonical_headers,
                                           signed_headers,
                                           payload_hash])

            string_to_sign = '\n'.join(['WOODBOX-HMAC-SHA256', now, sha256(canonical_request).hexdigest()])
            signing_key = secret.encode('utf-8')
            signature = hmac_new(signing_key, string_to_sign, sha256).hexdigest()

            auth = {
                'Credential': session_id,
                'SignedHeaders': signed_headers,
                'Signature': signature
            }
            auth = [k+'='+v for k,v in auth.iteritems()]
            auth = ','.join(auth)
            auth_str = ' '.join(['Woodbox-HMAC-SHA256', auth]);

            request_headers = {
                'Authorization': auth_str,
                'x-woodbox-content-sha256': payload_hash,
                'x-woodbox-timestamp': now
            }
            response = c.get('/test', headers=request_headers)
            self.assertEqual(g.user_reason, 'Content hash does not match.')
            self.assertEqual(response.data, 'anonymous', g.user_reason)
