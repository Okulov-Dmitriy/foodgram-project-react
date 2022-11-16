from django.contrib.auth import get_user_model
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from djoser.views import UserViewSet
from rest_framework.permissions import (AllowAny, IsAuthenticatedOrReadOnly,
                                        IsAuthenticated, SAFE_METHODS)
from .serializers import (CustomUserCreateSerializer, CustomUserSerializer,
                          TagSerializer, IngredientSerializer,
                          SubscriptionSerializer, RecipeGetSerializer,
                          RecipeCreateUpdateSerializer, RecipeShortSerializer)
from recipes.models import (Tag, Ingredient, Recipe, FavoriteRecipe,
                            ShoppingCart)
from users.models import Subscribe
from .permissions import AuthorOrReadOnly
from .paginators import PageLimitPagination
from .filters import IngredientFilter, RecipeFilter
from .services import download_cart

User = get_user_model()  # Нужно для того чтобы взять модель юзера


class CustomUserViewSet(UserViewSet):
    queryset = User.objects.all()
    serializer_class = CustomUserSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    # поле для поиска объекта в экземлпяре модели
    lookup_field = 'id'
    # ключевой урл для поиска объекта
    lookup_url_kwarg = 'id'

    def get_serializer_class(self):
        if self.action in ('create', 'update', 'partial_update'):
            return CustomUserCreateSerializer
        return CustomUserSerializer

    @action(
        detail=True,
        permission_classes=(IsAuthenticated,),
        methods=['post', 'delete']
    )
    def subscribe(self, request, **kwargs):
        user = request.user
        author_id = kwargs.get('id')
        author = get_object_or_404(User, id=author_id)
        subscription = Subscribe.objects.filter(
            user=user,
            author=author
        )
        if request.method == 'POST':
            if user == author:
                return Response(
                    {'errors': 'Запрещено подписываться на себя'},
                    status=status.HHTP_400_BAD_REQUEST
                )
            if subscription.exists():
                return Response(
                    {'erros': 'Вы уже подписаны на пользователя'},
                    status=status.HHTP_400_BAD_REQUEST
                )
            serializer = SubscriptionSerializer(
                author,
                context={'request': request},
            )
            Subscribe.objects.create(
                user=user, author=author
            )
            return Response(
                serializer.data, status=status.HTTP_201_CREATED
            )
        if not subscription.exists():
            return Response(
                {'errors': 'Вы не подписаны на пользователя'},
                status=status.HTTP_400_BAD_REQUEST
            )
        subscription.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=False,
        permission_classes=[IsAuthenticated],
        methods=['get']
    )
    def subscriptions(self, request):
        queryset = User.objects.filter(
            author__user=request.user
        )
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = SubscriptionSerializer(
                page, many=True, context={'request': request}
            )
            return self.get_paginated_response(serializer.data)
        serializer = SubscriptionSerializer(
            queryset, many=True
        )
        return Response(serializer.data, status=status.HTTP_200_OK)


class TagsViewSet(viewsets.ModelViewSet):
    queryset = Tag.objects.all().order_by('name')
    serializer_class = TagSerializer
    permission_classes = [AllowAny]
    # Отключивает пагинацию для этого класса
    pagination_class = None


class RecipesViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all().order_by('-pub_date')
    permission_classes = (AuthorOrReadOnly,)
    pagination_class = PageLimitPagination
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter

    def get_serializer_class(self):
        if self.request.method in SAFE_METHODS:
            return RecipeGetSerializer
        return RecipeCreateUpdateSerializer

    @staticmethod
    def add_or_delete_object(model, recipe, request):
        current_object = model.objects.filter(
            user=request.user, recipe=recipe
        )
        if request.method == 'POST':
            if current_object.exists():
                return Response(
                    {'errors': 'Этот рецепт уже добавлен'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            model.objects.create(user=request.user, recipe=recipe)
            serializer = RecipeShortSerializer(recipe)
            return Response(
                serializer.data, status=status.HTTP_201_CREATED
            )
        if request.method == 'DELETE':
            if current_object.exists():
                current_object.delete()
                return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(
            {'errors': 'Не добавлено'},
            status=status.HTTP_400_BAD_REQUEST
        )

    @action(
        detail=True,
        permission_classes=(IsAuthenticated,),
        methods=['post', 'delete']
    )
    def favorite(self, request, pk):
        recipe = get_object_or_404(Recipe, id=pk)
        return self.add_or_delete_object(
            FavoriteRecipe, recipe=recipe, request=request
        )

    @action(
        detail=True,
        permission_classes=(IsAuthenticated,),
        methods=['post', 'get', 'delete'],
        pagination_class=None
    )
    def shopping_cart(self, request, pk):
        recipe = get_object_or_404(Recipe, id=pk)
        return self.add_or_delete_object(
            ShoppingCart, recipe=recipe, request=request
        )

    @action(detail=False, permission_classes=(IsAuthenticated,))
    def download_shopping_cart(self, request):
        user = request.user
        return download_cart(user=user)


class IngredientsViewSet(viewsets.ModelViewSet):
    queryset = Ingredient.objects.all().order_by('name')
    serializer_class = IngredientSerializer
    permission_classes = [AllowAny]
    pagination_class = None
    search_fields = ('name',)
    filter_backends = (IngredientFilter,)
