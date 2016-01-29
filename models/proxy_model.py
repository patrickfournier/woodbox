# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals

# This is not useful right now but the idea could be extended to group many models under one ProxyModel.

class ProxyQuery:
    def __init__(self, proxy_for):
        self.proxy_for = proxy_for

    def get(self, id):
        return self.proxy_for.query.get(id)

    def filter_by(self, id):
        return self.proxy_for.query.filter_by(id)

    def all(self):
        return self.proxy_for.query.all()

class ProxyModelMetaclass(type):
    def __new__(mcl, name, bases, nmspc):
        if 'proxy_for' in nmspc:
            nmspc['query'] = ProxyQuery(nmspc['proxy_for'])
        return super(ProxyModelMetaclass, mcl).__new__(mcl, name, bases, nmspc)

class ProxyModel:
    """A proxy model acts like a db.Model, but sends all queries to a
    db.Model subclass.

    To define a ProxyModel, subclass ProxyModel and define proxy_for:

        class ContentNodeProxyModel(ProxyModel):
            proxy_for = NodeModel

    This can be useful if NodeModel is the base of a class hierarchy
    and you want your marshmallow schema to act differently on each
    derived class.

    """
    __metaclass__ = ProxyModelMetaclass
