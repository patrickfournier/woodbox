# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals

import importlib
import re

from flask import request, url_for, g
from flask_restful import Resource, abort
from marshmallow.exceptions import ValidationError
from sqlalchemy.exc import IntegrityError

from twisted.logger import Logger
log = Logger()

from .authenticator import HMACAuthenticator
from .db import db

class RecordAPI(Resource):
    """Base class to expose a db.Model rendered by a JSONAPISchema through
    a REST API implementing GET, DELETE and PATCH.

    To create the REST API for a model, subclass the RecordAPI and
    define the following class members:

    - model_class = the class of the database model (subclass of db.Model)
    - schema_class = the class of the schema (subclass of JSONAPISchema)

    then register the resource using flask_restful Api.add_resource.

    To define the LIST and POST operations, subclass RecordListAPI.
    """

    @classmethod
    def register_resource(cls, flask_restful_api):
        flask_restful_api.add_resource(cls, '/' + cls.schema_class.Meta.type_ + '/<item_id>')

    @classmethod
    def scoped_endpoint(cls):
        return '.' + cls.endpoint

    def _get_item(self, item_id, operation, check_existence):
        query = self.model_class.query
        if self.access_control is not None:
            query = self.access_control.alter_query(operation, query,
                                                    g.user,
                                                    self.resource_name,
                                                    self.model_class)
        item = query.filter_by(id=item_id).first()

        exists = None
        if not item and check_existence:
            exists = self.model_class.query.get(item_id) != None

        return item, exists

    def get(self, item_id):
        item, exists = self._get_item(item_id, 'read', check_existence=True)

        if not item:
            if exists is None:
                abort(500)
            elif not exists:
                abort(404)
            else:
                abort(403)
        else:
            return self.schema_class().dump(item).data

    def delete(self, item_id):
        item, exists = self._get_item(item_id, 'delete', check_existence=True)

        if not item:
            if exists is None:
                abort(500)
            elif not exists:
                abort(404)
            else:
                abort(403)
        else:
            msg = item.checkDeletePrecondition()
            if msg:
                abort(400, errors=[msg])
            else:
                db.session.delete(item)
                db.session.commit()
                return '', 204

    def patch(self, item_id):
        if request.mimetype != 'application/vnd.api+json':
            return '', 415, {'Accept-Patch': 'application/vnd.api+json'}

        input_data = request.get_json(force=True) or {}
        schema = self.schema_class()

        try:
            data, _ = schema.load(input_data, partial=True)
        except ValidationError as err:
            abort(415, errors=[err.args[0]])
        except Exception as err:
            abort(422, errors=[err.args[0]])

        item, exists = self._get_item(item_id, 'update', check_existence=True)

        if not item:
            # According to RFC5789, we may create the ressource, but we do not.
            if exists is None:
                abort(500)
            elif not exists:
                abort(404)
            else:
                abort(403)
        else:
            for key in data:
                setattr(item, key, data[key])

            msg = item.checkUpdatePrecondition()
            if msg:
                abort(400, errors=[msg])
            else:
                db.session.commit()
                return '', 204, {'Content-Location': url_for(self.scoped_endpoint(), item_id=item_id)}


class RecordListAPI(Resource):
    """Base class to expose a db.Model rendered by a JSONAPISchema through
    a REST API implementing LIST and POST.

    To create the REST API, subclass the RecordListAPI and define the
    following class members:

    - model_class = the class of the database model (subclass of db.Model)
    - schema_class = the class of the schema (subclass of JSONAPISchema)
    - record_api = the class of the corresponding RecordAPI subclass.

    Register the resource using register_resource.

    To define the GET (single record), DELETE and PATCH operations,
    subclass RecordAPI.

    """

    @classmethod
    def register_resource(cls, flask_restful_api):
        flask_restful_api.add_resource(cls, '/' + cls.schema_class.Meta.type_)

    def get(self):
        query = self.model_class.query
        if self.access_control is not None:
            query = self.access_control.alter_query('read', query,
                                                    g.user,
                                                    self.resource_name,
                                                    self.model_class)

        # Filter using query parameters
        for args, value in request.args.iteritems():
            c = getattr(self.model_class, self.schema_class._declared_fields[args].attribute)
            if value == '':
                value = None
            query = query.filter(c == value)

        items = query.all()
        return self.schema_class().dump(items, many=True).data

    def post(self):
        if request.mimetype != 'application/vnd.api+json':
            return '', 415, {'Accept-Patch': 'application/vnd.api+json'}

        input_data = request.get_json(force=True) or {}
        schema = self.schema_class()

        try:
            data, _ = schema.load(input_data)
        except ValidationError as err:
            abort(415, errors=[err.args[0]])
        except Exception as err:
            abort(422, errors=[err.args[0]])

        new_item = self.model_class(**data)
        db.session.add(new_item)
        db.session.commit()

        return (self.schema_class().dump(new_item, many=False).data,
                200, {'Content-Location': url_for(self.record_api.scoped_endpoint(), item_id=new_item.id)})


def make_api(flask_restful_app, name, model_class, schema_class,
             api_authorizers=None, record_authorizer=None):
    """Helper function to build an API for a schema.

    record_authorizer: instance of a woodbox.access_control.record.RecordAccessControl.

    api_authorizers: list of decorators, for example the authorize()
    member of an woodbox.access_control.api.Acl.

    """
    # TODO: we could have a schema_class per role
    if api_authorizers is None:
        method_decorators = []
    else:
        method_decorators = api_authorizers
    method_decorators.append(HMACAuthenticator.authenticate)

    # Create a subclass of Record[List]API and register the resource with the app.
    t = type(str(name+'API'), (RecordAPI,),
             {'method_decorators': method_decorators,
              'resource_name': name,
              'model_class': model_class,
              'schema_class': schema_class,
              'access_control': record_authorizer
             })
    t.register_resource(flask_restful_app)
    t = type(str(name+'ListAPI'), (RecordListAPI,),
             {'method_decorators': method_decorators,
              'resource_name': name,
              'model_class': model_class,
              'schema_class': schema_class,
              'access_control': record_authorizer,
              'record_api': t
             })
    t.register_resource(flask_restful_app)
