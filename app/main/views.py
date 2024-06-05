import os
from . import main
from .. import db
from app.main.forms import RecipeForm, ReviewForm
from flask import render_template, session, redirect, url_for, request, current_app
from app.models import Permission, Review, Recipe, User
from ..decorators import admin_required, permission_required
from werkzeug.utils import secure_filename
from flask_login import login_required, current_user
from sqlalchemy import func


@main.route("/user_info")
def info():
    '''
    Обрабатывает запрос на страницу с информацией о пользователе.
    Получает IP-адрес и информацию о браузере пользователя и отображает их.

    Returns:
        Возвращает HTML-страницу с информацией о пользователе.
    '''
    user_ip = request.remote_addr
    user_agent = request.headers.get('User-Agent')
    return '<h2>Your IP address is {}/</h2><h2>Your browser is {}</h2>'.format(user_ip, user_agent)


@main.route("/")
def index():
    '''
    Обрабатывает запрос на главную страницу.
    Если в сессии есть текст, отображает шаблон index.html.
    Если в сессии нет текста, также отображает шаблон index.html.

    Returns:
        Возвращает HTML-страницу index.html.
    '''
    session_text = session.get('text')
    if session_text is not None or session_text != '':
        return render_template('index.html')
    else:
        return render_template('index.html')


@main.route('/admin')
@login_required
@admin_required
def for_admin():
    '''
    Обрабатывает запрос на страницу, доступную только для администраторов.

    Returns:
        Возвращает текст "For admin".
    '''
    return "For admin"


@main.route('/moderate')
@login_required
@permission_required(Permission.MODERATE)
def for_moderator():
    '''
    Обрабатывает запрос на страницу, доступную только для модераторов.

    Returns:
        Возвращает текст "For moderator".
    '''
    return "For moderator"


@main.route('/secret')
@login_required
def secret():
    '''
    Обрабатывает запрос на секретную страницу.

    Returns:
        Возвращает текст "Only for auth".
    '''
    return "Only for auth"


@main.route("/testConfirm")
def testConfirm():
    '''
    Обрабатывает запрос на тестирование функции подтверждения учетной записи.
    Получает первого пользователя из базы данных, генерирует для него токен подтверждения и подтверждает его.

    Returns:
        Эта функция не возвращает значение, она просто проводит тестирование подтверждения учетной записи.
    '''
    user = User.query.filter_by().first()
    tmp = user.generate_confirmation_token()
    user.confirm(tmp)


@main.route('/profile')
@login_required
def profile():
    '''
    Обрабатывает запрос на страницу профиля.

    Returns:
        Возвращает HTML-страницу profile.html.
    '''
    return render_template('profile.html')


@main.route('/recipes')
def recipes():
    '''
    Обрабатывает запрос на страницу со списком рецептов.
    Получает все рецепты из базы данных и отображает шаблон recipes.html с передачей списка рецептов.

    Returns:
        Возвращает HTML-страницу recipes.html с передачей списка рецептов.
    '''
    recipes = Recipe.query.all()
    return render_template('recipes.html', recipes=recipes)


@main.route('/create_recipe', methods=['GET', 'POST'])
@admin_required
def create_recipe():
    '''
    Обрабатывает запросы на создание нового рецепта.
    Если пользователь не является администратором, перенаправляет его на страницу со списком рецептов.
    Создает форму для добавления нового рецепта, сохраняет рецепт в базе данных и перенаправляет на главную страницу.

    Returns:

    Возвращает HTML-страницу с формой создания нового рецепта или перенаправляет на страницу со списком рецептов.
    '''
    if not current_user.is_admin:
        return redirect(url_for('main.recipes'))