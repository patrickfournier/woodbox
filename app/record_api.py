# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals

import importlib
import re

from flask import request, url_for
from flask_restful import Resource, abort
from marshmallow.exceptions import ValidationError
from sqlalchemy.exc import IntegrityError

from . import db


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
    def scoped_endpoint(cls):
        return '.' + cls.endpoint

    def get(self, item_id):
        try:
            item = self.model_class.query.get(item_id)
        except IntegrityError:
            abort(404, message="{} {} doesn't exist".format(self.schema_class.Meta.type_, item_id))

        if not item:
            abort(404, message="{} {} doesn't exist".format(self.schema_class.Meta.type_, item_id))
        else:
            return self.schema_class().dump(item).data


    def delete(self, item_id):
        count = self.model_class.query.filter_by(id=item_id).delete()
        if count > 0:
            db.session.commit()
            return '', 204
        else:
            abort(404, message="{} {} doesn't exist".format(self.schema_class.Meta.type_, item_id))


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

        item = self.model_class.query.get(item_id)
        if not item:
            # According to RFC5789, we may create the ressource.
            abort(404, message="{} {} doesn't exist".format(self.schema_class.Meta.type_, item_id))

        for key in data:
            setattr(item, key, data[key])
        db.session.commit()
        return '', 204, {'Content-Location': url_for(self.scoped_endpoint(), item_id=item_id)}


class RecordListAPIMetaclass(Resource.__class__):
    def __new__(mcl, name, bases, nmspc):
        record_api_class_name = re.sub(r'^(.+)ListAPI$', r'\1API', name)
        m = importlib.import_module(nmspc['__module__'])
        record_api_class = getattr(m, record_api_class_name)
        nmspc['record_api'] = record_api_class
        return super(RecordListAPIMetaclass, mcl).__new__(mcl, name, bases, nmspc)


class RecordListAPI(Resource):
    """Base class to expose a db.Model rendered by a JSONAPISchema through
    a REST API implementing LIST and POST.

    To create the REST API, subclass the RecordListAPI and define the
    following class members:

    - model_class = the class of the database model (subclass of db.Model)
    - schema_class = the class of the schema (subclass of JSONAPISchema)

    You can optionnaly define the member record_api to the class of
    the corresponding RecordAPI subclass. If you do not define the
    record_api member, it will default to the class named the same as
    this class, minus the "List".

    Register the resource using flask_restful Api.add_resource.

    To define the GET, DELETE and PATCH operations, subclass RecordAPI.

    """

    __metaclass__ = RecordListAPIMetaclass

    def get(self):
        items = self.model_class.query.all()
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
        except:
            return {'message': err.message}, 422

        new_item = self.model_class(**data)
        db.session.add(new_item)
        db.session.commit()
        return '', 204, {'Content-Location': url_for(self.record_api.scoped_endpoint(),
                                                     item_id=new_item.id)}
