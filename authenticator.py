# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals

import urllib
import urlparse

from datetime import datetime, timedelta
from functools import wraps
from hashlib import sha256
from hmac import new as hmac_new

import six
import pytz

from flask import request, g
from flask_restful import abort

from .models.session_model import WBSessionModel
from .utils.time import strptime_iso8601


try:
    from hmac import compare_digest
except ImportError:
    def compare_digest(a, b):
        l = min(len(a), len(b))

        result = True
        for i in range(0, l):
            result = result and (a[i] == b[i]);

        if len(a) != len(b):
            result = False

        return result


class HMACAuthenticator(object):
    """Analyze a request and find from which user it originates."""

    @staticmethod
    def get_authorization_headers(session_id, secret, path,
                                  query_string=None, method='GET',
                                  content_type='', body='',
                                  host='localhost'):

        canonical_uri = urllib.quote(path.strip())
        if query_string is not None:
            canonical_query_string = urlparse.parse_qsl(query_string, True, True)
            canonical_query_string.sort() # will sort by name, then by value
            canonical_query_string = urllib.urlencode(canonical_query_string)
        else:
            canonical_query_string = ''

        payload_hash = sha256(body).hexdigest()
        now = datetime.utcnow().replace(tzinfo=pytz.utc).strftime("%Y%m%dT%H%M%S")

        headers = {
            'content-type': content_type,
            'host': host,
            'x-woodbox-content-sha256': payload_hash,
            'x-woodbox-timestamp': now
        }

        signed_headers = sorted(['content-type', 'host','x-woodbox-content-sha256','x-woodbox-timestamp'])

        canonical_headers = []
        for h in signed_headers:
            canonical_headers.append(h+':'+headers[h])
        canonical_headers = '\n'.join(canonical_headers).encode('utf-8')
        signed_headers = ';'.join(signed_headers)
        canonical_request = '\n'.join([method, path,
                                       canonical_query_string,
                                       canonical_headers,
                                       signed_headers, payload_hash])

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

        auth_headers = {
            'Authorization': auth_str,
            'x-woodbox-content-sha256': payload_hash,
            'x-woodbox-timestamp': now
        }

        return auth_headers

    @staticmethod
    def parse_authorization_header(header):
        method, _, args = header.partition(' ')
        method = method.strip()
        args = args.split(',')
        args_dict = dict()
        for arg in args:
            name, _, value = arg.partition('=')
            args_dict[name.strip().lower()] = value.strip()
        return (method, args_dict)

    @staticmethod
    def verify(algo, auth, headers):
        """
        Expected headers:

        Content-Type: application/vnd.api+json
        Authorization: Woodbox-HMAC-SHA256 Credential=2a241ea1e4672ee91f2ef8051e00eb52f03e39c97404a487,SignedHeaders=host;x-woodbox-content-sha256;x-woodbox-timestamp,Signature=422a358ac3e9e27b00838b6aa4192d74788a0d1634b418a13e0a18aaf7ca65f8
        x-woodbox-content-sha256: e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855
        x-woodbox-timestamp: 20160122T211203Z
        """
        # Check that we know the authentication algorithm.
        if algo.lower() not in frozenset(['hmac-sha256']):
            g.user = None
            g.user_reason = 'Unknown authentication method: ' + algo
            return False

        # Check that we have all the required authentication parameters.
        try:
            # Values were stripped in parse_authorization_header().
            credential = auth['credential'] # session_id
            signed_headers = sorted(auth['signedheaders'].lower().split(';'))
            signature = auth['signature']
        except KeyError as e:
            g.user = None
            g.user_reason = 'Missing parameter: {}'.format(e.args[0])
            return False

        # Required headers are the headers that MUST be included in the canonical headers.
        required_headers = set(['host', 'x-woodbox-content-sha256', 'x-woodbox-timestamp'])
        for h in six.iterkeys(headers):
            if h[:10] == 'x-woodbox-':
                required_headers.add(h)
            elif h == 'content-type':
                required_headers.add(h)

        # Check that all required headers were signed.
        if required_headers > set(signed_headers):
            g.user = None
            missing = (required_headers - set(signed_headers))
            g.user_reason = 'Some required headers were not signed: ' + ', '.join(missing)
            return False

        # Check that all signed headers are part of the request.
        missing_headers = set(signed_headers) - set(six.iterkeys(headers))
        if missing_headers:
            g.user = None
            g.user_reason = 'Missing headers: ' + ', '.join(missing_headers)
            return False

        # Check the age of the request. It must not be older than 5 minutes.
        request_time = strptime_iso8601(headers['x-woodbox-timestamp'])
        now = datetime.utcnow().replace(tzinfo=pytz.utc)
        max_age = timedelta(minutes=5)
        if abs(request_time - now) > max_age:
            g.user = None
            g.user_reason = 'Request is too old.'
            return False

        # FIXME Implement a nonce to prevent replay attacks.

        # Check the content hash.
        payload_hash = sha256(request.data).hexdigest()
        if payload_hash != headers['x-woodbox-content-sha256']:
            g.user = None
            g.user_reason = 'Content hash does not match.'
            return False

        # Load the session
        session = WBSessionModel.query.filter_by(session_id=credential).first()
        if not session:
            g.user = None
            g.user_reason = 'Invalid credential.'
            return False

        method = request.method.strip()
        canonical_uri = urllib.quote(request.path.strip())

        # Build the canonical query string
        canonical_query_string = []
        args = request.args.items(multi=True)
        args.sort()
        canonical_query_string = urllib.urlencode(args)

        # Build the canonical headers string.
        canonical_headers = []
        for h in signed_headers:
            canonical_headers.append(h+':'+headers[h])
        canonical_headers = '\n'.join(canonical_headers).encode('utf-8')

        signed_headers = ';'.join(signed_headers)
        canonical_request = '\n'.join([method, canonical_uri,
                                       canonical_query_string, canonical_headers, signed_headers,
                                       payload_hash])

        timestamp = headers['x-woodbox-timestamp']

        string_to_sign = '\n'.join(['WOODBOX-HMAC-SHA256', timestamp, sha256(canonical_request).hexdigest()])
        signing_key = session.secret.encode('utf-8')
        computed_signature = hmac_new(signing_key, string_to_sign, sha256).hexdigest()

        # Compare our signature with the signature in the request.
        if compare_digest(signature.encode('ascii', 'ignore'), computed_signature.encode('ascii', 'ignore')):
            g.user = session.user_id
            g.user_reason = 'Authenticated'
            return True
        else:
            g.user = None
            g.user_reason = 'Signature do not match'
            return False

    @staticmethod
    def authenticate(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            headers = dict()
            for h in six.iterkeys(request.headers):
                headers[h.lower().strip()] = request.headers[h].strip()

            g.user = None
            g.user_reason = "No valid authorization header."

            if 'authorization' in headers:
                method, auth = HMACAuthenticator.parse_authorization_header(headers['authorization'])
                if method[:8].lower() == 'woodbox-':
                    HMACAuthenticator.verify(method[8:].lower(), auth, headers)

            return f(*args, **kwargs)

        return wrapper
