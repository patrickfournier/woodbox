# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals

from marshmallow import pre_load, post_dump
from marshmallow_jsonapi import fields

from app.jsonapi_schema import JSONAPISchema, underscores_to_dashes, inflector
from app.models.video_sequence_model import FolderNodeModel, DocumentNodeModel

class NodeSchema(JSONAPISchema):
    node_type = fields.String(dump_only=True, attribute='type')

    @post_dump
    def adapt_node_type(self, d):
        """Transform the node type to the JSON API type."""
        type_name = inflector.plural(d['node_type'][:-6])
        d['node_type'] = underscores_to_dashes(type_name)

    parent_node_id = fields.Integer(attribute='parent_node_id')


class FolderNodeSchema(NodeSchema):
    parent_folder = fields.Nested('self', many=False, attribute='parent_node', exclude=('content',))
    title = fields.String()

    #content = fields.Relationship(
    #    related_url='/folders/{parent_folder_id}/content',
    #    related_url_kwargs={'parent_folder_id': '<id>'},
    #    many=True, include_data=True,
    #    type_='folders'
    #)
    content = fields.Nested('NodeSchema', many=True, exclude=('parent_node',))

class DocumentNodeSchema(NodeSchema):
    parent_folder = fields.Nested('self', many=False, attribute='parent_node', exclude=('content',))
    document = fields.Nested('DocumentSchema', many=False)

class DocumentSchema(JSONAPISchema):
    document_type = fields.String()
    title = fields.String()


class ContentNodeSchema(JSONAPISchema):
    title = fields.Method('get_title')
    node_type = fields.Method('get_type')

    def get_title(self, obj):
        if isinstance(obj, FolderNodeModel):
            return obj.title
        elif isinstance(obj, DocumentNodeModel):
            return obj.document.title
        return ''

    def get_type(self, obj):
        type_name = obj.type[:-6]
        return underscores_to_dashes(type_name)
