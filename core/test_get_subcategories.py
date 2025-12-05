from django.test import TestCase
from django.urls import reverse
from core.models import Category


class GetSubcategoriesAPITest(TestCase):
    def setUp(self):
        # create a small category tree
        self.top = Category.objects.create(name='Top')
        self.child1 = Category.objects.create(name='Child1', parent=self.top)
        self.child2 = Category.objects.create(name='Child2', parent=self.top)

    def test_get_subcategories_returns_children(self):
        url = reverse('get_subcategories', args=[self.top.id])
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        # ensure we return list of dicts with id and name
        ids = {d['id'] for d in data}
        names = {d['name'] for d in data}
        self.assertIn(self.child1.id, ids)
        self.assertIn(self.child2.id, ids)
        self.assertIn(self.child1.name, names)
        self.assertIn(self.child2.name, names)
