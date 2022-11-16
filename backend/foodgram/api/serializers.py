from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from users.models import Subscribe
from djoser.serializers import UserSerializer, UserCreateSerializer
from rest_framework import serializers
from recipes.models import (Tag, Ingredient, Recipe, RecipeIngredient,
                            FavoriteRecipe, ShoppingCart, RecipeTag)
from drf_extra_fields.fields import Base64ImageField

User = get_user_model()


class CustomUserCreateSerializer(UserCreateSerializer):

    class Meta:
        model = User
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'password',
        )
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        user = User(**validated_data)
        user.set_password(validated_data['password'])
        user.save()
        return user

    def validate_username(self, value):
        if value == 'me':
            raise serializers.ValidationError(
                '"me" - недопустимое значение'
            )
        return value


class CustomUserSerializer(UserSerializer):
    is_subscribed = serializers.SerializerMethodField()
    id = serializers.IntegerField()

    class Meta:
        model = User
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'is_subscribed',
        )

    def get_is_subscribed(self, obj):
        user = self.context.get('request').user
        if user.is_anonymos or user == obj:
            return False
        return Subscribe.objects.filter(
            user=user, author=obj
        ).exists()


class TagSerializer(serializers.ModelSerializer):

    class Meta:
        model = Tag
        fields = ('id', 'name', 'color', 'slug')
        read_only_fields = '__all__',


class IngredientSerializer(serializers.ModelSerializer):

    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')
        read_only_fields = '__all__',


class IngredientToRecipeSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField()

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'amount')


class RecipeIngredientGetSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(source='ingredients.id')
    name = serializers.CharField(source='ingredients.name')
    measurement_unit = serializers.CharField(
        source='ingredients.measurement_unit'
    )

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'name', 'measurement_unit', 'amount')


class RecipeGetSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField()
    image = Base64ImageField()
    ingredients = RecipeIngredientGetSerializer(
        source='recipe_amount', many=True
    )
    tags = TagSerializer(many=True)
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()
    author = CustomUserSerializer(read_only=True)

    class Meta:
        model = Recipe
        fields = (
            'id', 'author', 'name', 'image', 'text', 'tags',
            'ingredients', 'cooking_time', 'is_favorited',
            'is_in_shopping_cart'
        )

    def get_is_favorited(self, obj):
        user = self.context.get('request').user
        if user.is_anonymous:
            return False
        return FavoriteRecipe.objects.filter(
            user=user, recipe__id=obj.id
        ).exists()

    def get_is_in_shopping_cart(self, obj):
        user = self.context.get('request').user
        if user.is_anonymous:
            return False
        return ShoppingCart.objects.filter(
            user=user, recipe__id=obj.id
        ).exists()


class RecipeShortSerializer(serializers.ModelSerializer):
    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')
        read_only_fields = '__all__',


class RecipeCreateUpdateSerializer(serializers.ModelSerializer):
    image = Base64ImageField()
    ingredients = IngredientToRecipeSerializer(many=True)
    tags = serializers.ListField(
        child=serializers.SlugRelatedField(
            slug_field='id',
            queryset=Tag.objects.all()
        ),
        allow_empty=False
    )

    class Meta:
        model = Recipe
        fields = (
            'id', 'name', 'image', 'text',
            'tags', 'ingredients', 'cooking_time'
        )

    def validate(self, data):
        if data['name'] == data['text']:
            raise serializers.ValidationError(
                'Значания полей "name" и "text" не могут совпадать'
            )
        if not data['tags']:
            raise serializers.ValidationError(
                'Поле "Tag" должно быть заполнено'
            )
        tags_in_recipe = []
        for tag in data['tags']:
            if tag in tags_in_recipe:
                raise serializers.ValidationError(
                    f'Повторяющиеся значения: {tag}'
                )
            tags_in_recipe.append(tag)
        if not data['ingredients']:
            raise serializers.ValidationError(
                'Поле "Ingredients" должно быть заполнено'
            )
        ing_in_recipe = []
        for ing in data['ingredients']:
            if int(ing['amount']) <= 0:
                raise serializers.ValidationError(
                    'Значение должно быть больше нуля'
                )
            ingredient = get_object_or_404(Ingredient, id=ing['id'])
            if ingredient in ing_in_recipe:
                raise serializers.ValidationError(
                    f'Повторяющиеся значения: {ingredient}'
                )
            ing_in_recipe.append(ingredient)
        return data

    @classmethod
    def recipe_ingredient_create(cls, recipe, ingredients):
        recipe_list = [RecipeIngredient(
            recipe=recipe,
            ingredients=get_object_or_404(Ingredient, id=ingredient['id']),
            amount=ingredient['amount']
        ) for ingredient in ingredients]
        RecipeIngredient.objects.bulk_create(recipe_list)

    def to_representation(self, value):
        return RecipeGetSerializer(value, context=self.context).data

    def create(self, validated_data):
        ingredients = validated_data.pop('ingredients')
        tags = validated_data.pop('tags')
        recipe = Recipe.objects.create(
            author=self.context.get('request').user,
            **validated_data
        )
        self.recipe_ingredient_create(
            recipe=recipe,
            ingredients=ingredients
        )
        recipe.tags.set(tags)
        return recipe

    def update(self, instance, validated_data):
        ingredients = self.context['request'].data['ingredients']
        tags = self.context['request'].data['tags']
        instance.name = validated_data.get('name', instance.name)
        instance.image = validated_data.get('image', instance.image)
        instance.text = validated_data.get('text', instance.text)
        instance.cooking_time = validated_data.get(
            'cooking_time', instance.cooking_time
        )
        instance.save()
        if tags:
            RecipeTag.objects.filter(recipe=instance).delete()
            instance.tags.clear()
            instance.tags.set(tags)
        if ingredients:
            RecipeIngredient.objects.filter(recipe=instance).delete()
            instance.ingredients.clear()
            self.recipe_ingredient_create(
                recipe=instance,
                ingredients=ingredients
            )
        return instance


class SubscriptionSerializer(serializers.ModelSerializer):
    recipes = RecipeShortSerializer(many=True, read_only=True)
    recipes_count = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'is_subscribed',
            'recipes',
            'recipes_count',
        )

    def get_recipes_count(self, obj):
        return obj.recipes.count()
