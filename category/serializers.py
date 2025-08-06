from rest_framework import serializers
from .models import Category, Similarity


class CategoryListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name', 'description', 'image', 'parent']


class CategoryTreeSerializer(serializers.ModelSerializer):
    children = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = ['id', 'name', 'description', 'image', 'parent', 'children']

    def get_children(self, obj):
        children = obj.children.all()
        return CategoryTreeSerializer(children, many=True,
                                      context=self.context).data


class SimilaritySerializer(serializers.ModelSerializer):
    class Meta:
        model = Similarity
        fields = ['id', 'category_a', 'category_b']

    def validate(self, data):
        a = data.get('category_a') or getattr(self.instance, 'category_a',
                                              None)
        b = data.get('category_b') or getattr(self.instance, 'category_b',
                                              None)
        if a == b:
            raise serializers.ValidationError(
                "A category cannot be similar to itself.")
        if a.id > b.id:
            a, b = b, a
        data['category_a'] = a
        data['category_b'] = b

        similarity_qs = Similarity.objects.filter(category_a=a, category_b=b)
        if (similarity_qs.exists() and not self.instance) or (
                self.instance and similarity_qs.exclude(
                pk=self.instance.pk).exists()):
            raise serializers.ValidationError(
                "This similarity relationship already exists.")

        return data
