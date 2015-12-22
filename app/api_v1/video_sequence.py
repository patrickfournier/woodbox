# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals

from marshmallow import pre_load, post_dump
from marshmallow_jsonapi import fields

from app.jsonapi_schema import JSONAPISchema, underscores_to_dashes, inflector
from app.record_api import RecordAPI, RecordListAPI
from app.schema_validator import is_not_empty
from app.models.video_sequence_model import NodeModel, FolderNodeModel, DocumentNodeModel

class NodeSchema(JSONAPISchema):
    node_type = fields.String(dump_only=True, attribute='type')

    @post_dump
    def adapt_node_type(self, d):
        """Transform the node type to the JSON API type."""
        type_name = inflector.plural(d['node_type'][:-6])
        d['node_type'] = underscores_to_dashes(type_name)

    parent_node_id = fields.Integer(attribute='parent_node_id')

class NodeAPI(RecordAPI):
    model_class = NodeModel
    schema_class = NodeSchema

class NodeListAPI(RecordListAPI):
    model_class = NodeModel
    schema_class = NodeSchema


class FolderNodeSchema(NodeSchema):
    parent_folder = fields.Nested('self', many=False, attribute='parent_node', exclude=('content',))

    #content = fields.Relationship(
    #    related_url='/folders/{parent_folder_id}/content',
    #    related_url_kwargs={'parent_folder_id': '<id>'},
    #    many=True, include_data=True,
    #    type_='folders'
    #)
    content = fields.Nested('NodeSchema', many=True, exclude=('parent_node',))

class FolderNodeAPI(RecordAPI):
    model_class = FolderNodeModel
    schema_class = FolderNodeSchema

class FolderNodeListAPI(RecordListAPI):
    model_class = FolderNodeModel
    schema_class = FolderNodeSchema


class DocumentNodeSchema(NodeSchema):
    parent_folder = fields.Nested('self', many=False, attribute='parent_node', exclude=('content',))
    document = fields.Nested('DocumentSchema', many=False)

class DocumentNodeAPI(RecordAPI):
    model_class = DocumentNodeModel
    schema_class = DocumentNodeSchema

class DocumentNodeListAPI(RecordListAPI):
    model_class = DocumentNodeModel
    schema_class = DocumentNodeSchema


class DocumentSchema(JSONAPISchema):
    document_type = fields.String()
    title = fields.String()
