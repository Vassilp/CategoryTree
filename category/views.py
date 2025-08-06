from django.db.models import Q
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import Category, Similarity
from .serializers import CategoryListSerializer, SimilaritySerializer, \
    CategoryTreeSerializer


@extend_schema_view(
    list=extend_schema(
        summary="List all categories",
        description="Retrieves all categories in the system.",
        tags=["Category"],
    ),
    create=extend_schema(
        summary="Create a category (or update if exists)",
        description="Creates a new category. If a category with the "
                    "same name exists, updates it instead.",
        tags=["Category"],
    ),
    retrieve=extend_schema(
        summary="Get a specific category",
        description="Retrieves the category by ID.",
        tags=["Category"],
    ),
    # After more than an hour of deliberation on the topic of whether when
    # moving a category we want to move its children with it, or leave them
    # connected to the parent of the original category, I believe that because
    # the children are related to their original parent, they should move
    # with their original parent. This can be easily overwritten as is
    # the delete on model level.
    partial_update=extend_schema(
        summary="Update a category",
        description="Allows updating any or all fields of a category. "
                    "If parent is changed will move its children with it.",
        tags=["Category"],
    ),
    destroy=extend_schema(
        summary="Delete a category",
        description="Deletes the category, connecting its child "
                    "categories to its parent.",
        tags=["Category"],
    )
)
class CategoryViewSet(viewsets.ModelViewSet):
    http_method_names = ['get', 'post', 'patch', 'delete']
    # Thought about using prefetch_related('children') here, however it
    # behaves weirdly when deleting an element from a tree.
    queryset = Category.objects.all()
    serializer_class = CategoryListSerializer

    @extend_schema(
        summary="Get categories by depth",
        description="Returns a list of categories at a specific tree depth.",
        tags=["Category"],
    )
    @action(detail=False, url_path='by-depth/(?P<depth>[0-9]+)')
    def by_depth(self, request, depth=None):
        depth = int(depth)
        categories = [cat for cat in self.queryset if cat.get_depth() == depth]
        if not categories:
            return Response([])
        return Response(self.get_serializer(categories, many=True).data)

    @extend_schema(
        summary="Get categories by parent",
        description="Returns a list of child categories of a specific parent.",
        tags=["Category"],
    )
    @action(detail=False, url_path='by-parent/(?P<parent_id>[0-9]+)')
    def by_parent(self, request, parent_id=None):
        categories = self.queryset.filter(parent_id=parent_id)
        if not categories.exists():
            return Response([])
        return Response(self.get_serializer(categories, many=True).data)

    @extend_schema(
        summary="Get categories as a tree",
        description="Returns a tree of all categories.",
        tags=["Category"],
    )
    @action(detail=False, url_path='tree')
    def as_tree(self, request):
        self.serializer_class = CategoryTreeSerializer
        categories = [cat for cat in self.queryset if cat.get_depth() == 0]
        if not categories:
            return Response([])
        return Response(self.get_serializer(categories, many=True).data)

    @extend_schema(
        summary="Get category tree by depth",
        description="Returns a list of categories and their children "
                    "from a specific tree depth.",
        tags=["Category"],
    )
    @action(detail=False, url_path='tree/(?P<depth>[0-9]+)')
    def tree_by_depth(self, request, depth=None):
        self.serializer_class = CategoryTreeSerializer
        depth = int(depth) if depth is not None else 0
        categories = [cat for cat in self.queryset if cat.get_depth() == depth]
        if not categories:
            return Response([])
        return Response(self.get_serializer(categories, many=True).data)

    @extend_schema(
        summary="Get category tree by category",
        description="Returns a category and it's children in a tree structure",
        tags=["Category"],
    )
    @action(detail=False, url_path='tree/by-category/(?P<pk>[0-9]+)')
    def tree_by_parent(self, request, pk=None):
        self.serializer_class = CategoryTreeSerializer
        category = self.get_object()
        return Response(self.get_serializer(category).data)

    @extend_schema(
        summary="List similar categories",
        description="Returns a list of categories that are similar "
                    "to the given category.",
        tags=["Category"],
    )
    @action(detail=True, methods=["get"], url_path="similar")
    def similar(self, request, pk=None):
        category = self.get_object()

        similar_ids = Similarity.objects.filter(
            Q(category_a=category) | Q(category_b=category)
        ).values_list('category_a_id', flat=True).union(
            Similarity.objects.filter(
                Q(category_a=category) | Q(category_b=category)
            ).values_list('category_b_id', flat=True)
        )

        similar_ids = set(similar_ids) - {category.id}

        similar_categories = Category.objects.filter(id__in=similar_ids)
        if not similar_categories.exists():
            return Response([])
        serializer = self.get_serializer(similar_categories, many=True,
                                         context={"request": request})
        return Response(serializer.data)

    def create(self, request, *args, **kwargs):
        name = request.data.get('name')
        if not name:
            return Response({'detail': 'Name is required.'},
                            status=status.HTTP_400_BAD_REQUEST)

        try:
            existing = Category.objects.get(name=name)
            serializer = self.get_serializer(existing, data=request.data,
                                             partial=True)
            serializer.is_valid(raise_exception=True)
            self.perform_update(serializer)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Category.DoesNotExist:
            return super().create(request, *args, **kwargs)


@extend_schema_view(
    list=extend_schema(
        summary="List all similarity relationships",
        description="Returns a list of all bidirectional similarities.",
        tags=["Similarity"],
    ),
    create=extend_schema(
        summary="Create a similarity",
        description="Creates a bidirectional similarity between two "
                    "categories. If A is similar to B, "
                    "B is considered similar to A.",
        tags=["Similarity"],
    ),
    retrieve=extend_schema(
        summary="Get a similarity",
        description="Returns a specific similarity relationship by ID.",
        tags=["Similarity"],
    ),
    partial_update=extend_schema(
        summary="Update a similarity",
        description="Update the categories in a similarity relationship.",
        tags=["Similarity"],
    ),
    destroy=extend_schema(
        summary="Delete a similarity",
        description="Removes the similarity relationship between "
                    "two categories.",
        tags=["Similarity"]
    )
)
class SimilarityViewSet(viewsets.ModelViewSet):
    http_method_names = ['get', 'post', 'patch', 'delete']
    queryset = Similarity.objects.all()
    serializer_class = SimilaritySerializer
