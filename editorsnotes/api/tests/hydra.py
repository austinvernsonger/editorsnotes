from django.db import models

from rest_framework import serializers
from rest_framework.request import Request

from editorsnotes.auth.models import Project, User
from editorsnotes.search.utils import make_dummy_request

from ..serializers import ProjectSerializer
from ..serializers.hydra import HydraPropertySerializer

from .views import ClearContentTypesTransactionTestCase


class ExampleItem(models.Model):
    required_name = models.TextField(
        help_text='Name that is required.'
    )
    not_required_name = models.TextField(
        blank=True
    )
    read_only_name = models.TextField(
        help_text='Name that cannot be edited.',
        blank=True,
        editable=False
    )


class ExampleItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExampleItem


TEST_CONTEXT = {
    'required_name': 'http://schema.org/name',
    'not_required_name': 'http://schema.org/name',
    'read_only_name': 'http://schema.org/name'
}


class EmbeddingSerializerTestCase(ClearContentTypesTransactionTestCase):
    fixtures = ['projects.json']

    def setUp(self):
        self.project = Project(slug='egp')
        self.maxDiff = None

    def test_required_property(self):
        serializer = ExampleItemSerializer()
        field = serializer.get_fields()['required_name']

        property_serializer = HydraPropertySerializer(
            field, 'required_name', context_dict=TEST_CONTEXT)

        self.assertEqual(property_serializer.data, {
            'property': 'http://schema.org/name',
            'hydra:description': 'Name that is required.',
            'hydra:title': 'required_name',
            'hydra:required': True,
            'hydra:readonly': False,
            'hydra:writeonly': False
        })

    def test_nonrequired_property(self):
        serializer = ExampleItemSerializer()
        field = serializer.get_fields()['not_required_name']

        property_serializer = HydraPropertySerializer(
            field, 'not_required_name', context_dict=TEST_CONTEXT)

        self.assertEqual(property_serializer.data, {
            'property': 'http://schema.org/name',
            'hydra:description': None,
            'hydra:title': 'not_required_name',
            'hydra:required': False,
            'hydra:readonly': False,
            'hydra:writeonly': False
        })

    def test_read_only_property(self):
        serializer = ExampleItemSerializer()
        field = serializer.get_fields()['read_only_name']

        property_serializer = HydraPropertySerializer(
            field, 'read_only_name', context_dict=TEST_CONTEXT)

        self.assertEqual(property_serializer.data, {
            'property': 'http://schema.org/name',
            'hydra:description': 'Name that cannot be edited.',
            'hydra:title': 'read_only_name',
            'hydra:required': False,
            'hydra:readonly': True,
            'hydra:writeonly': False
        })

    def test_read_only_hyperlinked_collection_property(self):
        request = Request(make_dummy_request())
        context = {'request': request}
        serializer = ProjectSerializer(self.project, context=context)
        field = serializer.get_fields()['notes']

        property_serializer = HydraPropertySerializer(
            field, 'notes',
            'emma',
            self.project,
            context=context
        )

        serialized_property = dict(property_serializer.data.items())
        hydra_property = dict(serialized_property.pop('property').items())

        self.assertDictEqual(hydra_property, {
            '@id': 'emma:Project/notes',
            '@type': 'hydra:Link',
            'label': 'notes',
            'hydra:description': 'Notes for this project.',
            'domain': 'emma:Project',
            'range': 'hydra:Collection',
            'hydra:supportedOperation': [
                {
                    '@id': '_:project_notes_retrieve',
                    '@type': 'hydra:Operation',
                    'hydra:method': 'GET',
                    'label': 'Retrieve all notes for this project.',
                    'description': None,
                    'expects': None,
                    'returns': 'hydra:Collection',
                    'statusCodes': []
                }
            ]
        })

        self.assertDictEqual(serialized_property, {
            'hydra:description': 'Notes for this project.',
            'hydra:title': 'notes',
            'hydra:required': False,
            'hydra:readonly': True,
            'hydra:writeonly': False
        })

    def test_read_write_hyperlinked_collection_property(self):
        request = Request(make_dummy_request())
        request._user = User(username='Patrick', is_superuser=True)

        context = {'request': request}
        serializer = ProjectSerializer(self.project, context=context)

        field = serializer.get_fields()['notes']
        property_serializer = HydraPropertySerializer(
            field, 'notes',
            'emma',
            self.project,
            context=context
        )

        supported_operations = property_serializer.data\
            .get('property')\
            .get('hydra:supportedOperation')

        self.assertEqual(len(supported_operations), 2)

        create_operation, = filter(lambda op: op.get('hydra:method') == 'POST',
                                   supported_operations)

        self.assertDictEqual(dict(create_operation), {
            '@id': '_:project_note_create',
            '@type': 'hydra:CreateResourceOperation',
            'hydra:method': 'POST',
            'label': 'Create a note for this project.',
            'description': None,
            'expects': 'emma:Note',
            'returns': 'emma:Note',
            'statusCodes': []
        })
