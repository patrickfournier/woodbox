# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals

import json

from autobahn.twisted.websocket import WebSocketServerProtocol

from sqlalchemy.event import listen

from twisted.internet import reactor

class PushServiceMetaclass(type):
    """Add a connection list to each PushService subclass."""
    def __new__(mcl, name, bases, nmspc):
        nmspc['connections'] = list()
        return super(PushServiceMetaclass, mcl).__new__(mcl, name, bases, nmspc)


class PushService(WebSocketServerProtocol):
    __metaclass__ = PushServiceMetaclass

    def onConnect(self, request):
        self.connections.append(self)

    def onMessage(self, payload, isBinary):
        pass
        #if isBinary:
        #    print("Received binary message")
        #else:
        #    m = payload.decode('utf8')
        #    print(m)

        ## echo back message verbatim
        #self.sendMessage(payload, isBinary)

    def onClose(self, wasClean, code, reason):
        self.connections.remove(self)

    @classmethod
    def broadcast_message(cls, data):
        payload = json.dumps(data, ensure_ascii = False).encode('utf8')
        for c in set(cls.connections):
            reactor.callFromThread(cls.sendMessage, c, payload)



class NotificationService(PushService):
    @staticmethod
    def notify_insert(mapper, connection, target):
        NotificationService.broadcast_message({'event': 'created',
                                               'type': target.__class__.__name__,
                                               'id': target.id})

    @staticmethod
    def notify_update(mapper, connection, target):
        NotificationService.broadcast_message({'event': 'updated',
                                               'type': target.__class__.__name__,
                                               'id': target.id})

    @staticmethod
    def notify_delete(mapper, connection, target):
        NotificationService.broadcast_message({'event': 'deleted',
                                               'type': target.__class__.__name__,
                                               'id': target.id})

    @classmethod
    def register_model(cls, model_class, insert=True, update=True, delete=True):
        if insert:
            listen(model_class, 'after_insert', cls.notify_insert)
        if update:
            listen(model_class, 'after_update', cls.notify_update)
        if delete:
            listen(model_class, 'after_delete', cls.notify_delete)
