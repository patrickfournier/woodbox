# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals

import json
import uuid
import sys

from twisted.python import log
from twisted.logger import Logger
from twisted.internet import reactor
from twisted.web.server import Site
from twisted.web.wsgi import WSGIResource

from flask import Flask

from autobahn.twisted.websocket import WebSocketServerFactory
from autobahn.twisted.resource import WebSocketResource, WSGIRootResource

from kafka.common import NodeNotReadyError

from kleverklog import KafkaLogService

from .db import db
from .push_service import NotificationService

logger = Logger()

def create_app(config):
    app = Flask(__name__)
    app.config.from_object(config)

    log.startLogging(sys.stdout)

    if config.KAFKA_LOG_ENABLE:
        try:
            KafkaLogService.activate(getattr(config, 'KAFKA_LOG_HOST', 'localhost:9092'))
        except NodeNotReadyError:
            logger.warn("Kafka is not ready and will not be used to write log messages.")

    config.init_app(app)
    db.init_app(app)

    return app

def init_db():
    db.initialize()

def create_server(app, port):
    ##
    # create a Twisted Web resource for our WebSocket server
    ##
    ws_factory = WebSocketServerFactory(u"ws://127.0.0.1:5000",
                                        debug=app.debug,
                                        debugCodePaths=app.debug)
    ws_factory.protocol = NotificationService
    ws_resource = WebSocketResource(ws_factory)

    ##
    # create a Twisted Web WSGI resource for our Flask server
    ##
    wsgi_resource = WSGIResource(reactor, reactor.getThreadPool(), app)

    ##
    # create a root resource serving everything via WSGI/Flask, but
    # the path "/ws" served by our WebSocket stuff
    ##
    root_resource = WSGIRootResource(wsgi_resource, {'notification-service': ws_resource})

    ##
    # create a Twisted Web Site and run everything
    ##
    site = Site(root_resource)

    reactor.listenTCP(port, site)
    reactor.run()
