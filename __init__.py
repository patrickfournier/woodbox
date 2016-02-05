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

from .db import db
from .push_service import NotificationService

def create_app(config):
    app = Flask(__name__)
    app.config.from_object(config)
    config.init_app(app)
    db.init_app(app)
    return app

def init_db():
    db.initialize()

def create_server(app, port, debug=False):
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

    reactor.listenTCP(port, site)
    reactor.run()
