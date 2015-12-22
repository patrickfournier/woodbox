# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals

from sqlalchemy.ext.declarative import declared_attr

from app import db

class NodeModel(db.Model):
    id = db.Column(db.Integer, db.Sequence('node_model_id_seq'), primary_key=True)
    type = db.Column(db.String(50))

    # owner, group, permissions?

    parent_node_id = db.Column(db.Integer, db.ForeignKey('folder_node_model.id'), nullable=True)
    parent_node = db.relationship('FolderNodeModel', foreign_keys='FolderNodeModel.parent_node_id')

    __mapper_args__ = {
        'polymorphic_identity': 'node_model',
        'polymorphic_on': type
    }


class FolderNodeModel(NodeModel):
    id = db.Column(db.Integer, db.ForeignKey('node_model.id'), primary_key=True)

    title = db.Column(db.String(256), unique=False, nullable=True)

    content = db.relationship('NodeModel',
                              foreign_keys='NodeModel.parent_node_id',
                              back_populates='parent_node',
                              remote_side='NodeModel.parent_node_id')

    __mapper_args__ = {
        'polymorphic_identity': 'folder_node_model',
        'inherit_condition': (id == NodeModel.id),
    }


class DocumentNodeModel(NodeModel):
    id = db.Column(db.Integer, db.ForeignKey('node_model.id'), primary_key=True)

    document_id = db.Column(db.Integer, db.ForeignKey('document_model.id'), nullable=False)
    document = db.relationship('DocumentModel', foreign_keys='DocumentNodeModel.document_id')

    __mapper_args__ = {
        'polymorphic_identity': 'document_node_model',
        'inherit_condition': (id == NodeModel.id),
    }

class DocumentModel(db.Model):
    id = db.Column(db.Integer, db.Sequence('document_model_id_seq'), primary_key=True)
    document_type = db.Column(db.String(50))

    title = db.Column(db.String(256), unique=False, nullable=False)

    # date created, date modified

    __mapper_args__ = {
        'polymorphic_identity': 'document_model',
        'polymorphic_on': document_type
    }


class VideoSequenceModel(DocumentModel):
    id = db.Column(db.Integer, db.ForeignKey('document_model.id'), primary_key=True)

    __mapper_args__ = {
        'polymorphic_identity': 'video-sequence-model',
    }

    # Basic information
    location = db.Column(db.String(256))
    sequence_number = db.Column(db.Integer, default=1)

    # Sequence date
    date_recorded = db.Column(db.DateTime)
    date_unknown = db.Column(db.Boolean, nullable=False)

    #attendees = db.relationship('ActorModel', backref='video_sequence', lazy='dynamic')

class ActorModel(db.Model):
    id = db.Column(db.Integer, db.Sequence('actor_model_id_seq'), primary_key=True)
    name = db.Column(db.String(256), nullable=False)

#   @declared_attr
#    def video_sequence_id(cls):
#        return db.Column(db.Integer, db.ForeignKey('video_sequence.id'))




class CERFAVideoSequenceModel(VideoSequenceModel):
    # Environment
    environment = db.Column(db.Enum(*['classroom', 'family', 'workplace', 'community_activity', 'other'], name='environments'))
    environment_details = db.Column(db.String(256))

    # Classroom
    school_name = db.Column(db.String(256))
    teacher_name = db.Column(db.String(256))
