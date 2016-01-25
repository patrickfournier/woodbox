# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals

import json

from autobahn.twisted.websocket import WebSocketServerProtocol

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
    pass
