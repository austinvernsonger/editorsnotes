from django.http import Http404
from rest_framework import status
from rest_framework.response import Response
import reversion

from editorsnotes.main.models import Note, NoteSection
from editorsnotes.main.models.auth import RevisionProject

from .base import (BaseListAPIView, BaseDetailView, ElasticSearchRetrieveMixin,
                   ElasticSearchListMixin)
from ..serializers.notes import (
    MinimalNoteSerializer, NoteSerializer, _serializer_from_section_type)

class NoteList(ElasticSearchListMixin, BaseListAPIView):
    model = Note
    serializer_class = MinimalNoteSerializer

class NoteDetail(ElasticSearchRetrieveMixin, BaseDetailView):
    model = Note
    serializer_class = NoteSerializer
    def post(self, request, *args, **kwargs):
        """Add a new note section"""
        section_type = request.DATA.get('section_type', None)
        if section_type is None:
            raise Exception('need a section type')

        sec_serializer = _serializer_from_section_type(section_type)
        serializer = sec_serializer(
            data=request.DATA, context={
                'request': request,
                'create_revision': True
            })
        if serializer.is_valid():
            serializer.object.note = self.get_object()
            serializer.object.creator = request.user
            serializer.object.last_updater = request.user
            with reversion.create_revision():
                serializer.save()
                reversion.set_user(request.user)
                reversion.add_meta(RevisionProject, project=request.project)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        return Response(serializer.data, status=status.HTTP_400_BAD_REQUEST)


class NoteSectionDetail(BaseDetailView):
    model = NoteSection
    def get_object(self, queryset=None):
        queryset = self.get_queryset()
        obj = queryset.get()
        self.check_object_permissions(self.request, obj)
        return obj
    def get_queryset(self):
        note_id = self.kwargs.get('note_id')
        section_id = self.kwargs.get('section_id')
        note = Note.objects.get(id=note_id)
        qs = note.sections.select_subclasses()\
                .filter(note_section_id=section_id)
        if qs.count() != 1:
            raise Http404()
        self.model = qs[0].__class__
        return qs
    def get_serializer_class(self):
        section_type = getattr(self.object, 'section_type_label')
        return _serializer_from_section_type(section_type)
