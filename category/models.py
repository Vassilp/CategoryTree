from django.core.exceptions import ValidationError
from django.db import models, transaction


class Category(models.Model):
    class Meta:
        verbose_name = "Category"
        verbose_name_plural = "Categories"

    name = models.CharField(max_length=255, unique=True)
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to='category_images/', blank=True,
                              null=True)
    parent = models.ForeignKey('self', null=True, blank=True,
                               related_name='children',
                               on_delete=models.CASCADE)

    def clean(self):
        if self.parent == self:
            raise ValidationError("A category cannot be its own parent.")

        ancestor = self.parent
        while ancestor is not None:
            if ancestor == self:
                raise ValidationError(
                    "Setting this parent will cause circular ancestry.")
            ancestor = ancestor.parent

    # We want to force clean() on save()
    def save(self, **kwargs):
        self.clean()
        super().save(**kwargs)

    def delete(self, *args, **kwargs):
        with transaction.atomic():
            for child in self.children.all():
                child.parent = self.parent
                child.save()
            super().delete(*args, **kwargs)

    def get_depth(self):
        depth = 0
        node = self
        while node.parent:
            depth += 1
            node = node.parent
        return depth

    def __str__(self):
        return self.name


class Similarity(models.Model):
    category_a = models.ForeignKey(Category, on_delete=models.CASCADE,
                                   related_name='similar_to_a')
    category_b = models.ForeignKey(Category, on_delete=models.CASCADE,
                                   related_name='similar_to_b')

    class Meta:
        verbose_name = "Similarity"
        verbose_name_plural = "Similarities"
        constraints = [
            models.UniqueConstraint(
                fields=['category_a', 'category_b'], name='unique_similarity'),
            models.CheckConstraint(
                check=~models.Q(category_a=models.F('category_b')),
                name='no_self_similarity'
            )
        ]

    def save(self, *args, **kwargs):
        if self.category_a.id > self.category_b.id:
            self.category_a, self.category_b = self.category_b, self.category_a
        super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.category_a.name} <-> {self.category_b.name}'
