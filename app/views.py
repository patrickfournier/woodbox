# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals

from . import db
from .models.example_note_model import ExampleNoteModel

def populate_db():
    db.drop_all()
    db.create_all()
    data = {'title': 'Good restaurant', 'location': 'Montreal', 'priority': 1, 'date_created':  '2015-04-23T13:38', 'obsolete': False}
    vs = ExampleNoteModel(**data)
    db.session.add(vs)
    data = {'title': 'Art gallery', 'location': 'New York', 'priority': 5, 'date_created': '2015-04-23T14:38', 'obsolete': False}
    vs = ExampleNoteModel(**data)
    db.session.add(vs)
    db.session.commit()
    return 'DB Initialization Done'
