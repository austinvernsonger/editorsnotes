# -*- coding: utf-8 -*-

from django.test import TestCase
from django.contrib.auth.models import User
from django.forms.formsets import formset_factory
from models import Term
import utils

class UtilsTestCase(TestCase):
    def test_truncate(self):
        self.assertEquals(utils.truncate(u'xxxxxxxxxx', 4), u'xx... xx')

class AddTermTestCase(TestCase):
    fixtures = [ 'test' ]
    def setUp(self):
        self.user = User.objects.get(username='testuser')
    def testDuplicateSlug(self):
        Term.objects.create(preferred_name=u'Doe, John', creator=self.user)
        self.client.login(username='testuser', password='testuser')
        response = self.client.post('/admin/main/term/add/', 
                                     { 'preferred_name': u'Doe, John',
                                       'aliases-TOTAL_FORMS': 0,
                                       'aliases-INITIAL_FORMS': 0,
                                       'aliases-MAX_NUM_FORMS': 0 })
        self.assertEquals(len(response.context['errors']), 1)
        self.assertEquals(response.context['errors'][0][0], 
                          u'Term with this Preferred name already exists.')
        response = self.client.post('/admin/main/term/add/', 
                                     { 'preferred_name': u'Doe John',
                                       'aliases-TOTAL_FORMS': 0,
                                       'aliases-INITIAL_FORMS': 0,
                                       'aliases-MAX_NUM_FORMS': 0 })
        self.assertEquals(response.context['errors'][0][0], 
                          u'Term with a very similar Preferred name already exists.')
