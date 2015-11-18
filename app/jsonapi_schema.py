# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals

from marshmallow_jsonapi import Schema, fields

import re

def underscores_to_dashes(text):
    return text.replace('_', '-')

_underscorer1 = re.compile(r'(.)([A-Z][a-z]+)')
_underscorer2 = re.compile('([a-z0-9])([A-Z])')

def camel_to_dashes(text):
    subbed = _underscorer1.sub(r'\1-\2', text)
    return _underscorer2.sub(r'\1-\2', subbed).lower()

class JSONAPISchemaMetaclass(Schema.__class__):
    def __new__(mcl, name, bases, nmspc):
        nmspc['id'] = fields.Str(dump_only=True)
         # Convert class name from camel case to dashes and remove "-schema" at the end.
        dasherized_name = camel_to_dashes(name)[:-7]
        nmspc['Meta'] = type(str('Meta'), (object,),
                             dict(strict=True, inflect=underscores_to_dashes, type_=dasherized_name))
        return super(JSONAPISchemaMetaclass, mcl).__new__(mcl, name, bases, nmspc)

class JSONAPISchema(Schema):
    """Base schema to output JSON API compliant data.

    Subclasses will automatically have an id member and a nested Meta
    class defining the JSONAPI type.

    Subclass names should end with Schema (eg VideoSequenceSchema).

    """
    __metaclass__ = JSONAPISchemaMetaclass
