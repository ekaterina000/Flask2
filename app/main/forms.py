from wtforms import PasswordField, SelectField
from wtforms.validators import InputRequired
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, TextAreaField, IntegerField, SubmitField
from wtforms.validators import DataRequired


class UserForm(FlaskForm):
    username = StringField('Имя пользователя')
    email = StringField('Email', validators=[InputRequired()])
    password = PasswordField("Пароль")
    confirm_password = PasswordField('Подтвердите пароль', validators=[InputRequired()])
    gender = SelectField('Пол', choices=[('M', 'Мужской'), ('F', 'Женский')])


class RecipeForm(FlaskForm):
    title = StringField('Название', validators=[DataRequired()])
    description = TextAreaField('Описание', validators=[DataRequired()])
    ingredients = TextAreaField('Ингредиенты', validators=[DataRequired()])
    prep_time = IntegerField('Время приготовления (в минутах)', validators=[DataRequired()])
    category = SelectField('Категория', choices=['Основное меню', 'Гарниры', 'Десерты', 'Снеки'],
                           validators=[DataRequired()])
    submit = SubmitField('Добавить')
    image = FileField('Фото', validators=[FileAllowed(['jpg', 'png'], 'Только изображения JPG и PNG')])


class ReviewForm(FlaskForm):
    text = TextAreaField('Отзыв', validators=[DataRequired()])
    rating = IntegerField('Оценка', validators=[DataRequired()])
    submit = SubmitField('Отправить')


