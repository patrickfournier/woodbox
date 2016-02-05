# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals

from functools import wraps

import miracle

from flask import g
from flask_restful import abort

from ..models.user_model import WBUserModel, WBRoleModel

class Acl(miracle.Acl):
    def authorize(self, f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            myself = f.__self__
            funcname_to_action = {'post': 'create',
                                  'get': 'read',
                                  'patch': 'update',
                                  'delete': 'delete'}

            if g.user is None:
                roles = [WBRoleModel.anonymous_role_name]
            else:
                user = WBUserModel.query.get(g.user)
                roles = [r.rolename for r in user.roles]

            if self.check_any(roles, myself.resource_name, funcname_to_action[f.__name__]):
                return f(*args, **kwargs)
            else:
                abort(405)

        return wrapper
