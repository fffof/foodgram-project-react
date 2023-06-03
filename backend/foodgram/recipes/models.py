from django.contrib.auth import get_user_model
from django.db import models

User = get_user_model()


class Tag(models.Model):
    name = models.CharField(
        "Название",
        max_length=100)
    color = models.CharField(
        "Цвет",
        max_length=100)
    slug = models.SlugField(unique=True, null=False)

    class Meta:
        verbose_name = 'Tэг'
        verbose_name_plural = 'Tэги'

    def __str__(self):
        return self.slug


class Ingredients(models.Model):
    title = models.CharField(
        "Название",
        max_length=100)

    measurement_unit = models.CharField('Ед. измерения', max_length=128)

    class Meta:
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'

    def __str__(self):
        return f'{self.id}, {self.title}'


class Recipes(models.Model):
    name = models.CharField(
        "Название",
        max_length=100)
    text = models.TextField(
        'Текст поста',
        help_text='Введите текст поста'
    )
    tags = models.ManyToManyField(Tag)
    coocking_time = models.IntegerField(
        "Время приготовления"
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="recipe")
    pub_date = models.DateTimeField(
        'Дата добавления', auto_now_add=True, db_index=True
    )
    ingredients = models.ManyToManyField(
        Ingredients,
        through="RecipesIngredients")
    image = models.ImageField(
        'Картинка',
        upload_to='media/.recipes/images/',
        blank=True
    )

    class Meta:
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'
        ordering = ('-pub_date',)

    def __str__(self):
        return self.name


class RecipesIngredients(models.Model):
    recipe = models.ForeignKey(Recipes, on_delete=models.CASCADE)
    ingredients = models.ForeignKey(Ingredients, on_delete=models.CASCADE)
    amount = models.IntegerField(default=0)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['recipe', 'ingredients'],
                name='unique_ingredients_for_recipe',
            )
        ]

    def __str__(self):
        return (f'{self.recipe.name}: '
                f'{self.ingredients.name} - '
                f'{self.amount} '
                f'{self.ingredients.measurement}')


class Follow(models.Model):
    subscriber = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='follower',
        null=True
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='following',
        null=True
    )


class ShoppingCart(models.Model):
    user = models.ForeignKey(
        User,
        related_name='shoppings',
        on_delete=models.CASCADE,
        verbose_name='Пользователь',
    )
    recipe = models.ForeignKey(
        Recipes,
        related_name='shoppings',
        on_delete=models.CASCADE,
        verbose_name='Рецепт'
    )

    class Meta:
        verbose_name = 'Список покупок'
        verbose_name_plural = 'Списки покупок'
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipe'], name='unique_shopping_cart'
            )
        ]

    def __str__(self):
        return f'{self.user} - {self.recipe}'


class Favorite(models.Model):
    user = models.ForeignKey(
        User,
        related_name='favorites',
        on_delete=models.CASCADE,
        verbose_name='Пользователь',
    )
    recipe = models.ForeignKey(
        Recipes,
        related_name='favorites',
        on_delete=models.CASCADE,
        verbose_name='Рецепт'
    )

    class Meta:
        verbose_name = 'Избранное'
        verbose_name_plural = 'Избранные рецепты'
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipe'], name='unique_favorite_recipe'
            )
        ]

    def __str__(self):
        return f'{self.user} - {self.recipe}'
