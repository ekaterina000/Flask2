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
    '''
    user_ip = request.remote_addr
    user_agent = request.headers.get ('User-Agent')
    return '<h2>Your IP address is {}/</h2><h2>Your browser is {}</h2>'. format(user_ip, user_agent)


@main.route("/")
def index():
    '''Обрабатывает запрос на главную страницу.
    Если в сессии есть текст, отображает шаблон index.html.
    Если в сессии нет текста, также отображает шаблон index.html.
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
    Возвращает текст "For admin".
    '''
    return "For admin"


@main.route('/moderate')
@login_required
@permission_required(Permission.MODERATE)
def for_moderator():
    '''
    Обрабатывает запрос на страницу, доступную только для модераторов.
    Возвращает текст "For moderator".
    '''
    return "For moderator"


@main.route('/secret')
@login_required
def secret():
    '''
    Обрабатывает запрос на секретную страницу.
    Возвращает текст "Only for auth".
    '''
    return "Only for auth"


@main.route("/testConfirm")
def testConfirm():
    '''
    Обрабатывает запрос на тестирование функции подтверждения учетной записи.
    Получает первого пользователя из базы данных, генерирует для него токен подтверждения и подтверждает его.
    '''
    user = User.query.filter_by().first()
    tmp = user.generate_confirmation_token()
    user.confirm(tmp)


@main.route('/profile')
@login_required
def profile():
    '''
    Обрабатывает запрос на страницу профиля.
    Отображает шаблон profile.html.
    '''
    return render_template('profile.html')


@main.route('/recipes')
def recipes():
    '''
    Обрабатывает запрос на страницу со списком рецептов.
    Получает все рецепты из базы данных и отображает шаблон recipes.html с передачей списка рецептов.
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
    '''
    if not current_user.is_admin:
        return redirect(url_for('main.recipes'))

    form = RecipeForm()
    if form.validate_on_submit():
        recipe = Recipe(
            title=form.title.data,
            description=form.description.data,
            ingredients=form.ingredients.data,
            prep_time=form.prep_time.data,
            category=form.category.data,
            author=current_user
        )
        if form.image.data:
            filename = secure_filename(form.image.data.filename)
            image_path = os.path.join(current_app.root_path, 'static', 'images', filename)
            form.image.data.save(image_path)
            recipe.image_path = f'/static/images/{filename}'
        db.session.add(recipe)
        db.session.commit()
        return redirect(url_for('main.index'))
    return render_template('create_recipe.html', form=form)


@main.route('/recipe/<int:recipe_id>', methods=['GET', 'POST'])
@login_required

def recipe_detail(recipe_id):
    '''
    Обрабатывает запросы на страницу подробной информации о рецепте.
    Получает рецепт по указанному id, создает форму для добавления нового отзыва,
    сохраняет отзыв в базе данных и отображает шаблон recipe_detail.html с информацией о рецепте и отзывами.
    '''
    recipe = Recipe.query.get_or_404(recipe_id)
    form = ReviewForm()
    if form.validate_on_submit():
        review = Review(
            text=form.text.data,
            rating=form.rating.data,
            user_id=current_user.id,
            recipe_id=recipe.id
        )
        db.session.add(review)
        db.session.commit()
        return redirect(url_for('main.recipe_detail', recipe_id=recipe.id))
    reviews = recipe.reviews.all()
    avg_rating = db.session.query(func.avg(Review.rating)).filter_by(recipe_id=recipe.id).scalar()
    recipe.avg_rating = avg_rating if avg_rating else 0
    return render_template('recipe_detail.html', recipe=recipe, form=form, reviews=reviews)
