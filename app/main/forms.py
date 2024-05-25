from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SelectField, SubmitField
from wtforms.validators import InputRequired

class UserForm(FlaskForm):
    username = StringField('Имя пользователя')
    email = StringField('Email', validators=[InputRequired()])
    password = PasswordField("Пароль")
    confirm_password = PasswordField('Подтвердите пароль', validators=[InputRequired()])
    gender = SelectField('Пол', choices=[('M', 'Мужской'), ('F', 'Женский')])

