# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals

from marshmallow_jsonapi import fields

from app.jsonapi_schema import JSONAPISchema
from app.record_api import RecordAPI, RecordListAPI
from app.schema_validator import is_not_empty
from app.models.example_note_model import ExampleNoteModel


class ExampleNoteSchema(JSONAPISchema):
    title = fields.Str(required=True, validate=is_not_empty)
    location = fields.Str()
    priority = fields.Int()
    date_taken = fields.Str(attribute='date_created')
    obsolete = fields.Bool()
    upper_name = fields.Function(lambda obj: obj.title.upper())

class ExampleNoteAPI(RecordAPI):
    model_class = ExampleNoteModel
    schema_class = ExampleNoteSchema

class ExampleNoteListAPI(RecordListAPI):
    model_class = ExampleNoteModel
    schema_class = ExampleNoteSchema
