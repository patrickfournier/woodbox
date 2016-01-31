# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals

from abc import ABCMeta, abstractmethod

from sqlalchemy import and_, or_, true, false, text

from ..models.user_model import UserModel
from ..models.record_acl_model import RecordACLModel

class RecordAccessControl(object):
    __metaclass__ = ABCMeta

    def alter_query_for_read(self, query, user, item_type, model_class):
        alter = self.read_alter(user, item_type, model_class)
        print (alter)
        for j in alter['outerjoin']:
            query = query.outerjoin(j['table'], j['on'])

        return query.filter(alter['filter'])

    def alter_query_for_update(self, query, user, item_type, model_class):
        alter = self.update_alter(user, item_type, model_class)

        for j in alter['outerjoin']:
            query = query.outerjoin(j['table'], j['on'])

        return query.filter(alter['filter'])

    def alter_query_for_delete(self, query, user, item_type, model_class):
        alter = self.delete_alter(user, item_type, model_class)

        for j in alter['outerjoin']:
            query = query.outerjoin(j['table'], j['on'])

        return query.filter(alter['filter'])

    @abstractmethod
    def read_alter(self, user, item_type, model_class):
        return {'outerjoin': [], 'filter': true()}

    def update_alter(self, user, item_type, model_class):
        return self.read(user, item_type, model_class)

    def delete_alter(self, user, item_type, model_class):
        return self.read(user, item_type, model_class)


class And(RecordAccessControl):
    def __init__(self, *args, **kwargs):
        for c in args:
            self.operands = args

    def read_alter(self, user, item_type, model_class):
        outerjoins = []
        filters = []
        for ac in self.operands:
            alter = ac.read_alter(user, item_type, model_class)
            outerjoins += alter['outerjoin']
            filters.append(alter['filter'])
        return {'outerjoin': outerjoins, 'filter': and_(*filters)}

    def update_alter(self, user, item_type, model_class):
        outerjoins = []
        filters = []
        for ac in self.operands:
            alter = ac.update_alter(user, item_type, model_class)
            outerjoins += alter['outerjoin']
            filters.append(alter['filter'])
        return {'outerjoin': outerjoins, 'filter': and_(*filters)}

    def delete_alter(self, user, item_type, model_class):
        outerjoins = []
        filters = []
        for ac in self.operands:
            alter = ac.delete_alter(user, item_type, model_class)
            outerjoins += alter['outerjoin']
            filters.append(alter['filter'])
        return {'outerjoin': outerjoins, 'filter': and_(*filters)}


class Or(RecordAccessControl):
    def __init__(self, *args, **kwargs):
        for c in args:
            self.operands = args

    def read_alter(self, user, item_type, model_class):
        outerjoins = []
        filters = []
        for ac in self.operands:
            alter = ac.read_alter(user, item_type, model_class)
            outerjoins += alter['outerjoin']
            filters.append(alter['filter'])
        return {'outerjoin': outerjoins, 'filter': or_(*filters)}

    def update_alter(self, user, item_type, model_class):
        outerjoins = []
        filters = []
        for ac in self.operands:
            alter = ac.update_alter(user, item_type, model_class)
            outerjoins += alter['outerjoin']
            filters.append(alter['filter'])
        return {'outerjoin': outerjoins, 'filter': or_(*filters)}

    def delete_alter(self, user, item_type, model_class):
        outerjoins = []
        filters = []
        for ac in self.operands:
            alter = ac.delete_alter(user, item_type, model_class)
            outerjoins += alter['outerjoin']
            filters.append(alter['filter'])
        return {'outerjoin': outerjoins, 'filter': or_(*filters)}


class IsOwner(RecordAccessControl):
    def __init__(self, owner_id_column="owner_id"):
        self.owner_id_column = owner_id_column

    def read_alter(self, user, item_type, model_class):
        if user is None:
            return {'outerjoin': [], 'filter': false()}
        else:
            return {'outerjoin': [], 'filter': text(self.owner_id_column + "==" + str(user))}


class IsUser1(RecordAccessControl):
    def read_alter(self, user, item_type, model_class):
        if user == 1:
            return {'outerjoin': [], 'filter': true()}
        else:
            return {'outerjoin': [], 'filter': false()}


class HasRole(RecordAccessControl):
    def __init__(self, roles):
        assert hasattr(roles, '__iter__')
        self.roles = set(roles)

    def read_alter(self, user, item_type, model_class):
        if user is None:
            roles = set(['__anonymous'])
        else:
            user = UserModel.query.get(user)
            roles = set([r.rolename for r in user.roles])

        if roles & self.roles:
            return {'outerjoin': [], 'filter': true()}
        else:
            return {'outerjoin': [], 'filter': false()}


class InRecordACL(RecordAccessControl):
    def read_alter(self, user, item_type, model_class):
        return self._alter('read', user, item_type, model_class)

    def update_alter(self, user, item_type, model_class):
        return self._alter('update', user, item_type, model_class)

    def delete_alter(self, user, item_type, model_class):
        return self._alter('delete', user, item_type, model_class)

    def _alter(self, permission, user, item_type, model_class):
        if user is None:
            user_roles = set(['__anonymous'])
        else:
            user = UserModel.query.get(user)
            user_roles = set([r.rolename for r in user.roles])

        return {
            'outerjoin': [{
                'table': RecordACLModel,
                'on': RecordACLModel.record_id == model_class.id
            }],
            'filter' : and_(RecordACLModel.user_role.in_(user_roles),
                            RecordACLModel.record_type == item_type,
                            RecordACLModel.permission == permission)
        }
