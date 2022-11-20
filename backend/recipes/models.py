from django.contrib.auth import get_user_model
from django.db import models
from django.core.validators import MinValueValidator

User = get_user_model()


class Ingredient(models.Model):
    name = models.CharField(
        max_length=200,
        blank=False,
        verbose_name='Название'
    )
    measurement_unit = models.CharField(
        max_length=200,
        blank=False,
        verbose_name='Единицы измерения'
    )

    class Meta:
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'
        ordering = ['name']

    def __str__(self):
        return f'{self.name}, {self.measurement_unit}'


class Tag(models.Model):
    name = models.CharField(
        max_length=200,
        unique=True,
        blank=False,
        verbose_name='Название'
    )
    color = models.CharField(
        max_length=7,
        null=True,
        blank=False,
        unique=True,
        verbose_name='Цвет в HEX'
    )
    slug = models.SlugField(
        max_length=200,
        null=True,
        blank=False,
        unique=True,
        verbose_name='Уникальный слаг'
    )

    class Meta:
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'
        ordering = ['name']

    def __str__(self):
        return self.name


class Recipe(models.Model):
    author = models.ForeignKey(
        User,
        blank=False,
        on_delete=models.CASCADE,
        related_name='recipes'
    )
    name = models.CharField(
        max_length=200,
        blank=False,
        verbose_name='Название',
        help_text='Название рецепта'
    )
    image = models.ImageField(
        verbose_name='Картинка, закодированная в Base64',
        blank=True,
        upload_to='recipes/'
    )
    text = models.TextField(verbose_name='Описание')
    ingredients = models.ManyToManyField(
        Ingredient,
        through='RecipeIngredient',
        related_name='recipes',
        verbose_name='Ingredients'
    )
    tags = models.ManyToManyField(
        Tag,
        through='RecipeTag',
        blank=False,
        related_name='recipes',
        verbose_name='Tags'
    )
    cooking_time = models.PositiveIntegerField(
        verbose_name='Время приготовления в минутах',
        blank=False,
        validators=(MinValueValidator(1),)
    )
    pub_date = models.DateTimeField(
        verbose_name='Дата публикации',
        blank=False,
        auto_now_add=True
    )

    class Meta:
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'
        ordering = ('-pub_date',)

    def __str__(self):
        return f'{self.author}, {self.name}'


class RecipeIngredient(models.Model):
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='recipe_amount',
        blank=False
    )
    ingredients = models.ForeignKey(
        Ingredient,
        related_name='ingredients_amount',
        blank=False,
        on_delete=models.CASCADE
    )
    amount = models.PositiveIntegerField(
        verbose_name='Количество',
        blank=False,
        validators=(MinValueValidator(1),)
    )

    def __str__(self):
        return f'{self.recipe} {self.ingredients}'

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['ingredients', 'recipe'],
                name='ingredient_constraints'
            )
        ]


class RecipeTag(models.Model):
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        blank=False
    )
    tag = models.ForeignKey(
        Tag,
        on_delete=models.CASCADE,
        blank=False
    )

    def __str__(self):
        return f'{self.recipe} {self.tag}'

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['tag', 'recipe'],
                name='tag_constraints'
            )
        ]


class ShoppingCart(models.Model):
    user = models.ForeignKey(
        User,
        verbose_name='Пользователь',
        on_delete=models.CASCADE,
        related_name='is_in_shopping_cart'
    )
    recipe = models.ForeignKey(
        Recipe,
        verbose_name='Покупка',
        on_delete=models.CASCADE,
        related_name='is_in_shopping_cart'
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipe'],
                name='shopping_cart_constraints'
            )
        ]


class FavoriteRecipe(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Пользователь',
        related_name='is_favorited'
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name='Избраное',
        related_name='is_favorited'
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipe'],
                name='favorite_constraints'
            )
        ]
