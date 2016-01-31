# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals

import importlib
import re

from flask import request, url_for, g
from flask_restful import Resource, abort
from marshmallow.exceptions import ValidationError
from sqlalchemy.exc import IntegrityError

from .db import db
from .push_service import NotificationService

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

    def get(self, item_id):
        try:
            query = self.model_class.query
            if self.access_control is not None:
                query = self.access_control.alter_query_for_read(query,
                                                                 g.user,
                                                                 self.resource_name,
                                                                 self.model_class)
            item = query.filter_by(id=item_id).first()
        except IntegrityError:
            abort(404, message="{} {} doesn't exist.".format(self.schema_class.Meta.type_, item_id))

        if not item:
            abort(404, message="{} {} doesn't exist or you do not have permission to view it.".format(self.schema_class.Meta.type_, item_id))
        else:
            return self.schema_class().dump(item).data

    def delete(self, item_id):
        query = self.model_class.query
        if self.access_control is not None:
            query = self.access_control.alter_query_for_delete(query,
                                                               g.user,
                                                               self.resource_name,
                                                               self.model_class)
        count = query.filter_by(id=item_id).delete()
        if count > 0:
            db.session.commit()
            NotificationService.broadcast_message({'event': 'deleted',
                                                   'type': self.schema_class.Meta.type_,
                                                   'id': item_id})
            return '', 204
        else:
            abort(404, message="{} {} doesn't exist or you do not have permission to delete it.".format(self.schema_class.Meta.type_, item_id))

    def patch(self, item_id):
        schema = self.schema_class()
        if request.mimetype == 'application/vnd.api+json':
            input_data = request.get_json(force=True) or {}
        else:
            return '', 415, {'Accept-Patch': 'application/vnd.api+json'}

        try:
            data, errors = schema.load(input_data)
        except ValidationError as err:
            return {'message': err.message}, 415
        except Exception as err:
            return {'message': err.message}, 422

        query = self.model_class.query
        if self.access_control is not None:
            query = self.access_control.alter_query_for_update(query,
                                                               g.user,
                                                               self.resource_name,
                                                               self.model_class)
        item = query.filter_by(id=item_id).first()
        if not item:
            # According to RFC5789, we may create the ressource, but we do not.
            abort(404, message="{} {} doesn't exist or you do not have permission to modify it.".format(self.schema_class.Meta.type_, item_id))

        for key in data:
            setattr(item, key, data[key])
        db.session.commit()
        NotificationService.broadcast_message({'event': 'updated',
                                               'type': self.schema_class.Meta.type_,
                                               'id': item_id})
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
            query = self.access_control.alter_query_for_read(query,
                                                             g.user,
                                                             self.resource_name,
                                                             self.model_class)
        items = query.all()
        return self.schema_class().dump(items, many=True).data

    def post(self):
        schema = self.schema_class()
        if request.mimetype == 'application/vnd.api+json':
            input_data = request.get_json(force=True) or {}
        else:
            return '', 415, {'Accept-Patch': 'application/vnd.api+json'}
        try:
            data, errors = schema.load(input_data)
        except ValidationError as err:
            return {'message': err.message}, 415
        except Exception as err:
            return {'message': err.message}, 422

        new_item = self.model_class(**data)
        db.session.add(new_item)
        db.session.commit()
        NotificationService.broadcast_message({'event': 'created',
                                               'type': self.schema_class.Meta.type_,
                                               'id': new_item.id})
        return '', 204, {'Content-Location': url_for(self.record_api.scoped_endpoint(),
                                                     item_id=new_item.id)}


def make_api(flask_restful_app, name, model_class, schema_class,
             api_authorizers=None, record_authorizer=None):
    # TODO: we could have a schema_class per role
    if api_authorizers is None:
        method_decorators = []
    else:
        method_decorators = api_authorizers
    method_decorators.append(flask_restful_app.authenticator.authenticate)

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
