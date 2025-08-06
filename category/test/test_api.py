import os
import tempfile

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse

from ..models import Category, Similarity

MEDIA_ROOT = tempfile.mkdtemp()


@override_settings(MEDIA_ROOT=MEDIA_ROOT)
class CategoryAPITests(TestCase):
    def setUp(self):
        self.url = reverse('category-list')
        self.a = Category.objects.create(name='A')
        self.b = Category.objects.create(name='B')

    def test_create_category(self):
        response = self.client.post(self.url, {
            'name': 'C',
            'description': 'Description of c',
        })
        self.assertEqual(response.status_code, 201)
        self.assertEqual(Category.objects.filter(name='C').count(), 1)

    def test_update_if_exists_by_name(self):
        response = self.client.post(self.url, {
            'name': 'A',
            'description': 'Updated description of a',
        })
        self.assertEqual(response.status_code, 200)
        self.a.refresh_from_db()
        self.assertEqual(self.a.description, 'Updated description of a')

    def test_partial_update_category(self):
        url = reverse('category-detail', args=[self.a.id])
        response = self.client.patch(
            url, {
                'description': 'New partial description'},
            content_type='application/json')
        self.assertEqual(response.status_code, 200)
        self.a.refresh_from_db()
        self.assertEqual(self.a.description, 'New partial description')

    def test_changing_parent_moves_children(self):
        parent1 = Category.objects.create(name='P1')
        parent2 = Category.objects.create(name='P2')
        child = Category.objects.create(name='Child', parent=parent1)
        url = reverse('category-detail', args=[parent1.id])
        response = self.client.patch(url, {'parent': parent2.id},
                                     content_type='application/json')
        self.assertEqual(response.status_code, 200)
        child.refresh_from_db()
        self.assertEqual(child.parent.parent, parent2)

    def test_get_by_depth(self):
        Category.objects.create(name='Child', parent=self.a)
        url = reverse('category-by-depth', args=[1])
        response = self.client.get(url)
        self.assertContains(response, 'Child')
        self.assertNotContains(response, 'A')

    def test_get_by_parent(self):
        Category.objects.create(name='Child', parent=self.a)
        url = reverse('category-by-parent', args=[self.a.id])
        response = self.client.get(url)
        self.assertContains(response, 'Child')

    def test_get_by_depth_returns_200(self):
        url = reverse('category-by-depth', args=[5])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), [])

    def test_get_by_parent_returns_200(self):
        url = reverse('category-by-parent', args=[self.b.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), [])

    def test_as_tree_returns_root(self):
        Category.objects.create(name='Child', parent=self.a)
        url = reverse('category-as-tree')
        response = self.client.get(url)
        self.assertContains(response, 'A')
        self.assertContains(response, 'B')
        self.assertContains(response, 'Child')

    def test_tree_by_depth(self):
        Category.objects.create(name='Child', parent=self.a)
        url = reverse('category-tree-by-depth', args=[1])
        response = self.client.get(url)
        self.assertContains(response, 'Child')

    def test_tree_by_depth_200(self):
        url = reverse('category-tree-by-depth', args=[3])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), [])

    def test_tree_by_parent(self):
        Category.objects.create(name='Child', parent=self.a)
        url = reverse('category-tree-by-parent', args=[self.a.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Child')

    def test_create_with_image(self):
        image_path = os.path.join(settings.BASE_DIR, 'CategoryTree',
                                  'test_files', 'test_image.png')
        with open(image_path, 'rb') as test_img:
            image_file = SimpleUploadedFile("test.png", test_img.read(),
                                            content_type="image/png")
            response = self.client.post(self.url, {
                'name': 'D',
                'description': 'Description of D',
                'image': image_file,
            })
        self.assertEqual(response.status_code, 201)
        self.assertIsNotNone(response.json().get('image'))

    def test_update_nonexistent_category_404(self):
        non_existent_id = 9999
        url = reverse('category-detail', args=[non_existent_id])
        response = self.client.patch(url, {'name': 'Ghost'},
                                     content_type='application/json')
        self.assertEqual(response.status_code, 404)

    def test_circular_parent_prevention(self):
        z = Category.objects.create(name='Z')
        y = Category.objects.create(name='Y', parent=z)
        x = Category.objects.create(name='X', parent=y)
        z.parent = x
        with self.assertRaises(ValidationError):
            z.save()

    def test_similar_view_returns_similar(self):
        Category.objects.create(name='C')
        Similarity.objects.create(category_a=self.a, category_b=self.b)
        url = reverse('category-similar', args=[self.a.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'B')

    def test_similar_view_returns_200_when_none(self):
        url = reverse('category-similar', args=[self.a.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), [])

    def test_create_category_without_name_returns_400(self):
        response = self.client.post(self.url, {'description': 'No name'})
        self.assertEqual(response.status_code, 400)

    def test_patch_category_same_parent_does_not_reparent_children(self):
        parent = Category.objects.create(name='Parent')
        child = Category.objects.create(name='Child', parent=parent)
        url = reverse('category-detail', args=[parent.id])
        response = self.client.patch(url, {'parent': None},
                                     content_type='application/json')
        self.assertEqual(response.status_code, 200)
        child.refresh_from_db()
        self.assertEqual(child.parent, parent)

    def test_create_category_with_invalid_image_type(self):
        file = SimpleUploadedFile("test.txt", b"not an image",
                                  content_type="text/plain")
        response = self.client.post(self.url, {
            'name': 'InvalidImage',
            'description': 'Invalid image type',
            'image': file,
        })
        self.assertEqual(response.status_code, 400)


class SimilarityAPITests(TestCase):
    def setUp(self):
        self.a = Category.objects.create(name='A')
        self.b = Category.objects.create(name='B')
        self.similarity_url = reverse('similarity-list')

    def test_create_similarity(self):
        response = self.client.post(self.similarity_url, {
            'category_a': self.a.id,
            'category_b': self.b.id,
        })
        self.assertEqual(response.status_code, 201)
        self.assertEqual(Similarity.objects.count(), 1)

    def test_retrieve_similarity(self):
        sim = Similarity.objects.create(category_a=self.a,
                                        category_b=self.b)
        url = reverse('similarity-detail', args=[sim.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertIn('category_a', response.json())

    def test_cannot_self_similar(self):
        response = self.client.post(self.similarity_url, {
            'category_a': self.a.id,
            'category_b': self.a.id,
        })
        self.assertEqual(response.status_code, 400)

    def test_bidirectional_enforced(self):
        Similarity.objects.create(category_a=self.a, category_b=self.b)
        response = self.client.post(self.similarity_url, {
            'category_a': self.b.id,
            'category_b': self.a.id,
        })
        self.assertEqual(response.status_code, 400)

    def test_delete_similarity(self):
        sim = Similarity.objects.create(category_a=self.a, category_b=self.b)
        url = reverse('similarity-detail', args=[sim.id])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, 204)
        self.assertEqual(Similarity.objects.count(), 0)

    def test_partial_update_similarity(self):
        sim = Similarity.objects.create(category_a=self.a, category_b=self.b)
        new_cat = Category.objects.create(name='C')
        url = reverse('similarity-detail', args=[sim.id])
        response = self.client.patch(url, {'category_b': new_cat.id},
                                     content_type='application/json')
        self.assertEqual(response.status_code, 200)
        sim.refresh_from_db()
        self.assertEqual(sim.category_b, new_cat)

    def test_patch_similarity_to_duplicate_pair_fails(self):
        Similarity.objects.create(category_a=self.a, category_b=self.b)
        c = Category.objects.create(name='C')
        sim2 = Similarity.objects.create(category_a=self.a, category_b=c)
        url = reverse('similarity-detail', args=[sim2.id])
        response = self.client.patch(url, {'category_b': self.b.id},
                                     content_type='application/json')
        self.assertEqual(response.status_code, 400)

    def test_patch_similarity_with_one_field(self):
        sim = Similarity.objects.create(category_a=self.a, category_b=self.b)
        url = reverse('similarity-detail', args=[sim.id])
        response = self.client.patch(url, {'category_a': self.a.id},
                                     content_type='application/json')
        self.assertEqual(response.status_code, 200)
