"""
Custom fields for storing RDF primitives.

Based on http://blog.elsdoerfer.name/2008/01/08/fuzzydates-or-one-django-model-field-multiple-database-columns/
"""
from builtins import str
from past.builtins import basestring
from django.db import models
from rdflib.graph import Graph
from rdflib.term import BNode, URIRef, Literal
from future.utils import with_metaclass


class LiteralField(with_metaclass(models.SubfieldBase, models.TextField)):
    """
    Custom field for storing literals.
    """
    description = "Field for storing Literals, including their type and language"

    def to_python(self, value):
        if not value:
            return None

        if isinstance(value, Literal):
            return value

        parts = value.split('^^')
        if len(parts) != 3:
            raise ValueError("Wrong value: {0}".format(value))
        return Literal(parts[0], parts[1] or None, parts[2] or None)

    def value_to_string(self, obj):
        value = self._get_val_from_obj(obj)
        return self.get_prep_value(value)

    def get_prep_value(self, value):
        if not isinstance(value, Literal):
            raise TypeError("Value {0} has the wrong type: {1}".format(value, value.__class__))

        return str(value) + "^^" + (value.language or '') + "^^" + (value.datatype or '')


def deserialize_uri(value):
    """
    Deserialize a representation of a BNode or URIRef.
    """
    if isinstance(value, BNode):
        return value
    if isinstance(value, URIRef):
        return value
    if not value:
        return None
    if not isinstance(value, basestring):
        raise ValueError("Cannot create URI from {0} of type {1}".format(value, value.__class__))
    if value.startswith("_:"):
        return BNode(value[2:])
    return URIRef(value)


def serialize_uri(value):
    """
    Serialize a BNode or URIRef.
    """
    if isinstance(value, BNode):
        return value.n3()
    if isinstance(value, URIRef):
        return str(value)
    raise ValueError("Cannot get prepvalue for {0} of type {1}".format(value, value.__class__))


class URIField(with_metaclass(models.SubfieldBase, models.CharField)):
    """
    Custom field for storing URIRefs and BNodes.

    URIRefs are stored as themselves; BNodes are stored in their Notation3 serialization.
    """
    description = "Field for storing URIRefs and BNodes."

    def __init__(self, *args, **kwargs):
        if 'max_length' not in kwargs:
            kwargs['max_length'] = 500
        super(URIField, self).__init__(*args, **kwargs)

    def to_python(self, value):
        return deserialize_uri(value)

    def value_to_string(self, obj):
        return serialize_uri(self._get_val_from_obj(obj))

    def get_prep_value(self, value):
        return serialize_uri(value)


class GraphReferenceField(with_metaclass(models.SubfieldBase, models.CharField)):
    """
    Custom field for storing graph references.
    """
    description = "Field for storing references to Graphs"

    def to_python(self, value):
        if isinstance(value, Graph):
            return value.identifier

        return deserialize_uri(value)

    def value_to_string(self, obj):
        value = self._get_val_from_obj(obj)
        return self.get_prep_value(value)

    def get_prep_value(self, value):
        if isinstance(value, Graph):
            return serialize_uri(value.identifier)

        return serialize_uri(value)
