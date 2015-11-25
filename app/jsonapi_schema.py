# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals

import re

import inflect
from marshmallow_jsonapi import Schema, fields

# EmberJS uses pluralized type names, so shall we do.
# The inflector is responsible for the pluralization of type name.
# You can customize plural forms with:
# inflector.defnoun("Strata", "Stratum")  # SINGULAR => PLURAL
inflector = inflect.engine()

_underscorer1 = re.compile(r'(.)([A-Z][a-z]+)')
_underscorer2 = re.compile('([a-z0-9])([A-Z])')

def camel_to_dashes(text):
    subbed = _underscorer1.sub(r'\1-\2', text)
    return _underscorer2.sub(r'\1-\2', subbed).lower()

def underscores_to_dashes(text):
    return text.replace('_', '-')

class JSONAPISchemaMetaclass(Schema.__class__):
    def __new__(mcl, name, bases, nmspc):
        nmspc['id'] = fields.Str(dump_only=True)

        # Convert class name to type name:
        # - remove the Schema suffix
        # - pluralize
        # - convert from camel case to dashes
        type_name = inflector.plural(name[:-6])
        dasherized_name = camel_to_dashes(type_name)
        nmspc['Meta'] = type(str('Meta'), (object,),
                             dict(strict=True, inflect=underscores_to_dashes, type_=dasherized_name))
        return super(JSONAPISchemaMetaclass, mcl).__new__(mcl, name, bases, nmspc)


class JSONAPISchema(Schema):
    """Base schema to output JSON API compliant data.

    Subclasses will automatically have an id member and a nested Meta
    class defining the JSONAPI type. This type is the dasherized
    version of the subclass name, minus the "Schema" suffix.

    Subclass names should end with Schema (eg BlogPostSchema).

    """
    __metaclass__ = JSONAPISchemaMetaclass
