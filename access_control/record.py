# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals

from abc import ABCMeta, abstractmethod

from sqlalchemy import and_, or_, true, false, text

from ..models.user_model import WBUserModel, WBRoleModel
from ..models.record_acl_model import RecordACLModel

class RecordAccessControl(object):
    __metaclass__ = ABCMeta

    def __init__(self, *args, **kwargs):
        pass

    def _alter_query(self, query, alter):
        for j in alter['outerjoin']:
            query = query.outerjoin(j['table'], j['on'])
        return query.filter(alter['filter'])

    def alter_query(self, op, query, user, item_type, model_class):
        alter = self._get_alteration(op, user, item_type, model_class)
        return self._alter_query(query, alter)

    @abstractmethod
    def _get_alteration(self, op, user, item_type, model_class):
        return {'outerjoin': [], 'filter': true()}


class And(RecordAccessControl):
    def __init__(self, *args, **kwargs):
        for c in args:
            self.operands = args
        super(And, self).__init__(*args, **kwargs);

    def _get_alteration(self, op, user, item_type, model_class):
        outerjoins = []
        filters = []
        for ac in self.operands:
            alter = ac._get_alteration(op, user, item_type, model_class)
            outerjoins += alter['outerjoin']
            filters.append(alter['filter'])
        return {'outerjoin': outerjoins, 'filter': and_(*filters)}


class Or(RecordAccessControl):
    def __init__(self, *args, **kwargs):
        for c in args:
            self.operands = args
        super(Or, self).__init__(*args, **kwargs);

    def _get_alteration(self, op, user, item_type, model_class):
        outerjoins = []
        filters = []
        for ac in self.operands:
            alter = ac._get_alteration(op, user, item_type, model_class)
            outerjoins += alter['outerjoin']
            filters.append(alter['filter'])
        return {'outerjoin': outerjoins, 'filter': or_(*filters)}


class IsOwner(RecordAccessControl):
    def __init__(self, owner_id_column="owner_id"):
        self.owner_id_column = owner_id_column

    def _get_alteration(self, op, user, item_type, model_class):
        if user is None:
            return {'outerjoin': [], 'filter': false()}
        else:
            return {'outerjoin': [], 'filter': text(self.owner_id_column + "==" + str(user))}


class IsUser1(RecordAccessControl):
    def _get_alteration(self, op, user, item_type, model_class):
        if user == 1:
            return {'outerjoin': [], 'filter': true()}
        else:
            return {'outerjoin': [], 'filter': false()}


class HasRole(RecordAccessControl):
    def __init__(self, roles, *args, **kwargs):
        assert hasattr(roles, '__iter__')
        self.roles = set(roles)
        super(HasRole, self).__init__(*args, **kwargs)

    def _get_alteration(self, op, user, item_type, model_class):
        if user is None:
            roles = (WBRoleModel.anonymous_role_name,)
        else:
            user = WBUserModel.query.get(user)
            roles = {r.rolename for r in user.roles}

        if roles & self.roles:
            return {'outerjoin': [], 'filter': true()}
        else:
            return {'outerjoin': [], 'filter': false()}


class InRecordACL(RecordAccessControl):
    def _get_alteration(self, op, user, item_type, model_class):
        if user is None:
            anonymous_role_id = WBRoleModel.get_anonymous_role_id()
            user_roles = (anonymous_role_id,)
        else:
            user = WBUserModel.query.get(user)
            user_roles = {r.id for r in user.roles}

        return {
            'outerjoin': [{
                'table': RecordACLModel,
                'on': RecordACLModel.record_id == model_class.id
            }],
            'filter' : and_(RecordACLModel.user_role_id.in_(user_roles),
                            RecordACLModel.record_type == item_type,
                            RecordACLModel.permission == op)
        }
