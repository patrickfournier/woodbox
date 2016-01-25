# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals

import json
import uuid
import sys

from twisted.python import log
from twisted.internet import reactor
from twisted.web.server import Site
from twisted.web.wsgi import WSGIResource


from flask import Flask, make_response, jsonify

from autobahn.twisted.websocket import WebSocketServerFactory
from autobahn.twisted.resource import WebSocketResource, WSGIRootResource

from config import config

from .db import db
from .push_service import NotificationService
from .session import authenticate, validate_session, invalidate_session

def create_app(config_name):
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    config[config_name].init_app(app)

    db.init_app(app)

    from .api_v1 import blueprint as api_v1_blueprint
    app.register_blueprint(api_v1_blueprint, url_prefix='/api/v1')

    app.add_url_rule('/authenticate', 'authenticate', authenticate, methods=['POST'])
    app.add_url_rule('/validate-session', 'validate_session', validate_session, methods=['POST'])
    app.add_url_rule('/invalidate-session', 'invalidate_session', invalidate_session, methods=['POST'])

    return app


def init_db():
    db.drop_all()
    db.create_all()

def create_server(app, debug=False):
    app.debug = debug

    if debug:
        log.startLogging(sys.stdout) # FIXME: use config file

    ##
    # create a Twisted Web resource for our WebSocket server
    ##
    wsFactory = WebSocketServerFactory(u"ws://127.0.0.1:5000",
                                       debug=debug,
                                       debugCodePaths=debug)
    wsFactory.protocol = NotificationService
    wsResource = WebSocketResource(wsFactory)

    ##
    # create a Twisted Web WSGI resource for our Flask server
    ##
    wsgiResource = WSGIResource(reactor, reactor.getThreadPool(), app)

    ##
    # create a root resource serving everything via WSGI/Flask, but
    # the path "/ws" served by our WebSocket stuff
    ##
    rootResource = WSGIRootResource(wsgiResource, {'notification-service': wsResource})

    ##
    # create a Twisted Web Site and run everything
    ##
    site = Site(rootResource)

    reactor.listenTCP(5000, site)
    reactor.run()
