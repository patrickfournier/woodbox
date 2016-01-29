# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals

from abc import ABCMeta, abstractmethod

from sqlalchemy import and_, or_, true, false, text

class RecordAccessControl(object):
    __metaclass__ = ABCMeta

    @abstractmethod
    def read(self, user, item_type, item_id):
        return true()

    def update(self, user, item_type, item_id):
        return self.read(user, item_type, item_id)

    def delete(self, user, item_type, item_id):
        return self.read(user, item_type, item_id)


class And(RecordAccessControl):
    def __init__(self, *args, **kwargs):
        for c in args:
            self.operands = args

    def read(self, user, item_type, item_id):
        return and_(*[ac.read(user, item_type, item_id) for ac in self.operands])

    def update(self, user, item_type, item_id):
        return and_(*[ac.update(user, item_type, item_id) for ac in self.operands])

    def delete(self, user, item_type, item_id):
        return and_(*[ac.delete(user, item_type, item_id) for ac in self.operands])


class Or(RecordAccessControl):
    def __init__(self, *args, **kwargs):
        for c in args:
            self.operands = args

    def read(self, user, item_type, item_id):
        return or_(*[ac.read(user, item_type, item_id) for ac in self.operands])

    def update(self, user, item_type, item_id):
        return or_(*[ac.update(user, item_type, item_id) for ac in self.operands])

    def delete(self, user, item_type, item_id):
        return or_(*[ac.delete(user, item_type, item_id) for ac in self.operands])


class Ownership(RecordAccessControl):
    def read(self, user, item_type, item_id):
        if user is None:
            return false()
        else:
            return text("owner_id="+str(user))


class User1(RecordAccessControl):
    def read(self, user, item_type, item_id):
        return text("owner_id=1")
