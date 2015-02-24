from lxml import etree, html

from django.contrib.contenttypes.models import ContentType
from licensing.models import License
from rest_framework import serializers

from editorsnotes.main.models import (Note, TextNS, CitationNS, NoteReferenceNS,
                                      Document, NoteSection)
from editorsnotes.main.models.notes import NOTE_STATUS_CHOICES

from .base import (RelatedTopicSerializerMixin, CurrentProjectDefault,
                   URLField, ProjectSlugField, UpdatersField,
                   HyperlinkedProjectItemField, TopicAssignmentField)
from .auth import MinimalUserSerializer
from ..validators import UniqueToProjectValidator


__all__ = ['NoteSerializer']


class TextNSSerializer(serializers.ModelSerializer):
    section_id = serializers.ReadOnlyField(source='note_section_id')
    section_type = serializers.ReadOnlyField(source='section_type_label')
    class Meta:
        model = TextNS
        fields = ('section_id', 'section_type', 'content',)

class CitationNSSerializer(serializers.ModelSerializer):
    section_id = serializers.ReadOnlyField(source='note_section_id')
    section_type = serializers.ReadOnlyField(source='section_type_label')
    document = HyperlinkedProjectItemField(view_name='api:documents-detail',
                                           queryset=Document.objects.all())
    document_description = serializers.SerializerMethodField()
    class Meta:
        model = CitationNS
        fields = ('section_id', 'section_type',
                  'document', 'document_description', 'content',)
    def get_document_description(self, obj):
        return etree.tostring(obj.document.description)

class NoteReferenceNSSerializer(serializers.ModelSerializer):
    section_id = serializers.ReadOnlyField(source='note_section_id')
    section_type = serializers.ReadOnlyField(source='section_type_label')
    note_reference = HyperlinkedProjectItemField(view_name='api:notes-detail',
                                                 queryset=Note.objects.all())
    note_reference_title = serializers.SerializerMethodField()
    class Meta:
        model = NoteReferenceNS
        fields = ('section_id', 'section_type',
                  'note_reference', 'note_reference_title', 'content',)
    def get_note_reference_title(self, obj):
        return obj.note_reference.title

class LicenseSerializer(serializers.ModelSerializer):
    class Meta:
        model = License
        fields = ('url', 'name', 'symbols',)


def _serializer_from_section_type(section_type):
    if section_type == 'citation':
        serializer = CitationNSSerializer
    elif section_type == 'text':
        serializer = TextNSSerializer
    elif section_type == 'note_reference':
        serializer = NoteReferenceNSSerializer
    else:
        raise NotImplementedError(
            'No such note section type: {}'.format(section_type))
    return serializer

class NoteSectionField(serializers.RelatedField):
    def __init__(self, *args, **kwargs):
        kwargs['queryset'] = NoteSection.objects.all()
        super(NoteSectionField, self).__init__(*args, **kwargs)
    def to_representation(self, section):
        serializer_class = _serializer_from_section_type(section.section_type_label)
        serializer = serializer_class(section, context=self.context)
        return serializer.data
    def to_internal_value(self, data):
        section_type = data['section_type']
        serializer_class = _serializer_from_section_type(section_type)
        serializer = serializer_class(data=data, context={
            'request': self.context['request']
        })
        if serializer.is_valid():
            if 'section_id' in data:
                serializer.validated_data['section_id'] = data['section_id']
            serializer.validated_data['section_type'] = section_type
            return serializer.validated_data
        else:
            # TODO: This kind of error is unhelpfully/confusingly rendered. It
            # would be better if we could add an index somehow
            raise serializers.ValidationError(serializer.errors)

class NoteStatusField(serializers.ReadOnlyField):
    def get_attribute(self, obj):
        return obj.get_status_display().lower() if obj else 'open'
    def to_internal_value(self, data):
        status_choice = [ val for val, label in NOTE_STATUS_CHOICES
                          if label.lower() == data.lower() ]
        if not len(status_choice):
            raise serializers.ValidationError('Invalid status. Choose between '
                                              'open, closed, or hibernating.')
        return status_choice[0]

# TODO: change license, fuller repr of updaters
class NoteSerializer(RelatedTopicSerializerMixin,
                     serializers.ModelSerializer):
    _permissions = serializers.SerializerMethodField('get_permissions')
    url = URLField()
    project = ProjectSlugField(default=CurrentProjectDefault())
    license = LicenseSerializer(read_only=True, source='get_license')
    updaters = MinimalUserSerializer(read_only=True, many=True,
                                     source='get_all_updaters')
    status = NoteStatusField()
    related_topics = TopicAssignmentField()
    sections = NoteSectionField(many=True, source='get_sections_with_subclasses')
    class Meta:
        model = Note
        fields = ('_permissions', 'id', 'title', 'url', 'project', 'license', 'is_private', 'last_updated',
                  'updaters', 'related_topics', 'content', 'status', 'sections',)
        validators = [
            UniqueToProjectValidator('title')
        ]
    def get_permissions(self, obj):
        user = getattr(self.context['request'], 'user', None)
        if not user or not user.is_authenticated():
            return []
        project = self.context['request'].project
        role = project.get_role_for(user)
        if not role:
            return []
        note_ct = ContentType.objects.get_for_model(Note)
        note_section_ct = ContentType.objects.get_for_model(NoteSection)
        perms = role.get_permissions().filter(content_type__in=[note_ct, note_section_ct])
        return [perm.codename for perm in perms]
    # TODO Make sure all section IDs are valid?
    def _create_note_section(self, note, data):
        section_type = data.pop('section_type')
        section_klass = _serializer_from_section_type(section_type).Meta.model
        section = section_klass.objects.create(
            note=note,
            creator=self.context['request'].user,
            last_updater=self.context['request'].user,
            **data)
        return section
    def create(self, validated_data):
        sections_data = validated_data.pop('get_sections_with_subclasses')
        note = super(NoteSerializer, self).create(validated_data)
        for idx, section_data in enumerate(sections_data, 1):
            section_data['ordering'] = idx
            self._create_note_section(note, section_data)
        return note
    def update(self, instance, validated_data):
        sections_data = validated_data.pop('get_sections_with_subclasses')
        note = super(NoteSerializer, self).update(instance, validated_data)

        # Maybe do this over? It's not perty.
        # Go through every section in the update and save an instance if
        # necessary.
        existing_sections = note.get_sections_with_subclasses()
        existing_sections_by_id = {
            section.note_section_id: section
            for section in existing_sections
        }

        existing_order = tuple(ns.id for ns in existing_sections)
        new_order = []
        in_update = []

        for section in sections_data:

            section_id = section.pop('section_id', None)
            if section_id is None:
                # New section; create it and add it to the note
                new_section = self._create_note_section(note, section)
                new_order.append(new_section.id)
                continue

            del section['section_type']

            # TODO: Make sure no changing of section types
            existing_section = existing_sections_by_id[section_id]
            in_update.append(section_id)
            new_order.append(existing_section.id)
            changed = False

            for field, value in section.items():
                old_value = getattr(existing_section, field)
                setattr(existing_section, field, value)
                if changed: continue

                if isinstance(value, html.HtmlElement):
                    changed = etree.tostring(value) != etree.tostring(old_value)
                else:
                    changed = value != old_value

            if changed:
                existing_section.last_updater = self.context['request'].user
                existing_section.save()

        # Delete sections no longer in the note
        to_delete = (section for section in existing_sections
                     if section.note_section_id not in in_update)
        for section in to_delete:
            section.delete()

        if len(new_order) and existing_order != tuple(new_order):
            positions_dict = {v: k for k, v in enumerate(new_order)}
            note.sections.bulk_update_order('ordering', positions_dict)

        return note
