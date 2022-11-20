![workflow](https://github.com/Okulov-Dmitriy/foodgram-project-react/actions/workflows/main.yml/badge.svg)

# О проекте

Cайт Foodgram, «Продуктовый помощник». На этом сервисе пользователи могут:
* публиковать рецепты,
* подписываться на публикации других пользователей,
* добавлять понравившиеся рецепты в список «Избранное»,
* скачивать сводный список продуктов, необходимых для приготовления одного или нескольких выбранных блюд. 

Проект доступен по [адресу](http://158.160.19.115/)

# Технологии

Backend:

* Python
* Django
* Djnago REST framework
* Docker/Docker-compose
* Nginx
* Gunicorn

Frontend:

* JavaScript
* React

# Описание команд для запуска проекта


Клонировать репозиторий и перейти в него в командной строке:

```
git clone git@github.com:Okulov-Dmitriy/foodgram-project-react.git
```

```
cd foodgram-project-react
```
Перейти в директорию 'infra':

```
cd infra
```

Соберать контейнеры:

```
docker-compose up -d
```

Выполнить миграции

```
docker-compose exec web python manage.py migrate
```

Создать суперпользователя:

```
docker-compose exec web python manage.py createsuperuser
```

Собрать статику:

```
docker-compose exec web python manage.py collectstatic --no-input
```

Для загрузки тестовой базы данных выполните команду и подтвердите отчистку базы данных:

```
docker-compose exec web python manage.py щload_ingredients data/ingredients.csv
```

Данные для входа в админку:

```
email: admin@admin.ru
password: admin
```

>>>>>>> 871bf58f235cd3b5c5534b557112f01bc9083e55
## Автор

Окулов Дмитрий
