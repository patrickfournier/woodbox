# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals

from functools import wraps

import miracle

from flask import g
from flask_restful import abort


def get_roles(user):
    if user is None:
        roles = ['anonymous']
    elif user == 1:
        roles = ['admin']
    else:
        roles = ['user', 'user-' + str(user)]
    return roles


class Acl(miracle.Acl):
    def authorize(self, f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            myself = f.__self__
            funcname_to_action = {'post': 'create',
                                  'get': 'read',
                                  'patch': 'update',
                                  'delete': 'delete'}

            roles = get_roles(g.user)
            if self.check_any(roles, myself.resource_name, funcname_to_action[f.__name__]):
                return f(*args, **kwargs)
            else:
                abort(405)

        return wrapper
