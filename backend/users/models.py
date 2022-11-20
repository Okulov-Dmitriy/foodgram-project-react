from django.contrib.auth.models import AbstractUser
from django.db import models
from api.validators import OnlyLettersValidator

from .managers import CustomUserManager


class User(AbstractUser):
    objects = CustomUserManager()
    email = models.EmailField(
        verbose_name='Адрес электронной почты',
        max_length=254,
        unique=True,
        blank=False
    )
    username = models.CharField(
        verbose_name='Уникальный юзернейм',
        max_length=150,
        unique=True,
        blank=False
    )
    first_name = models.CharField(
        verbose_name='Имя',
        max_length=150,
        blank=False,
        validators=[OnlyLettersValidator]
    )
    last_name = models.CharField(
        verbose_name='Фамилия',
        max_length=150,
        blank=False,
        validators=[OnlyLettersValidator]
    )
    password = models.CharField(
        verbose_name='Пароль',
        max_length=150,
        blank=False
    )
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name', 'password']

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
        ordering = ('username',)

    def __str__(self):
        return self.username


class Subscription(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        null=True,
        related_name='subscriber'
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        null=True,
        related_name='author'
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'author'],
                name='subscribe_constraints'
            )
        ]

    def __str__(self):
        return '{user} is subscribed to {author}'.format(
            user=self.user,
            author=self.author
        )
