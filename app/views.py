# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals

from .db import db
from .models.video_sequence_model import FolderNodeModel, DocumentNodeModel, VideoSequenceModel
from .models.user_model import UserModel

def populate_db():
    db.drop_all()
    db.create_all()

    data = {'title': 'root', 'parent_node_id': None}
    vs = FolderNodeModel(**data)
    db.session.add(vs)
    db.session.commit()
    root_id = vs.id

    data = {'title': 'usr', 'parent_node_id': root_id}
    vs = FolderNodeModel(**data)
    db.session.add(vs)

    data = {'title': 'var', 'parent_node_id': root_id}
    vs = FolderNodeModel(**data)
    db.session.add(vs)

    data = {'title': 'home', 'parent_node_id': root_id}
    vs = FolderNodeModel(**data)
    db.session.add(vs)
    db.session.commit()
    root_id = vs.id

    data = {'title': 'MyDocument', 'date_unknown': True}
    vs = VideoSequenceModel(**data)
    db.session.add(vs)
    db.session.commit()

    data = {'document_id': vs.id, 'parent_node_id': root_id}
    doc = DocumentNodeModel(**data)
    db.session.add(doc)

    db.session.commit()

    data = {'username': "patrick", 'password': '123qwe', 'name': "Patrick Fournier"}
    doc = UserModel(**data)
    db.session.add(doc)

    db.session.commit()
    return 'DB Initialization Done'
