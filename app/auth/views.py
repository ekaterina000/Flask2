from flask import render_template, redirect, request, flash, url_for
from flask_mail import Message
from . import auth
from .forms import LoginForm, RegistrationForm
from .. import db, mail
from ..models import User, Role
from flask_login import login_user, login_required, logout_user, current_user
from threading import Thread


'''Функция, выполняемая перед каждым запросом.
   Проверяет, авторизован ли пользователь, и если да, обновляет время его последней активности.
   Если пользователь не подтвердил свою учетную запись и запрос не относится к авторизации или статическим файлам, 
   перенаправляет его на страницу подтверждения'''


@auth.before_app_request
def before_request():
    if current_user.is_authenticated:
        current_user.ping()
        if (
                not current_user.confirmed
                and request.blueprint != 'auth'
                and request.endpoint != 'static'
                and request.endpoint != 'auth.confirm'
        ):
            return redirect(url_for('auth.unconfirmed'))


'''Обрабатывает вход пользователя.
   Создает форму входа, проверяет введенные данные и, если они верны, авторизует пользователя.
   Если следующая страница указана в параметрах запроса, перенаправляет туда,
   иначе - на главную страницу'''


@auth.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user is not None and user.password_verify(form.password.data):
            login_user(user)
            next_page = request.args.get("next")
            if next_page is None or not next_page.startswith('/'):
                next_page = url_for('main.index')
            return redirect(next_page)
        flash('Invalid email or password')
    return render_template("auth/login.html", form=form)


'''Обрабатывает регистрацию нового пользователя.
   Создает форму регистрации, проверяет введенные данные и, если все в порядке,
   сохраняет пользователя в базе данных, генерирует токен подтверждения и отправляет письмо пользователю.
   После этого перенаправляет пользователя на страницу входа.'''


@auth.route("/register", methods=["GET", "POST"])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(
            email=form.email.data,
            username=form.username.data,
            role=Role.query.get(form.role.data)
        )
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        token = user.generate_confirmation_token()
        send_confirm(user, token)
        flash('Вам отправлено письмо для подтверждения аккаунта.')
        return redirect(url_for('auth.login'))
    return render_template("auth/registration.html", form=form)


'''Обрабатывает выход пользователя из системы.
# Выполняет выход пользователя и перенаправляет его на главную страницу.'''


@auth.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You have been logged out.")
    return redirect(url_for('main.index'))


'''Обрабатывает подтверждение учетной записи пользователя.
   Если пользователь уже подтвержден, перенаправляет его на главную страницу.
   Если токен подтверждения верный, подтверждает учетную запись пользователя и перенаправляет его на страницу входа.
   Если токен недействителен, выводит сообщение об ошибке и перенаправляет на главную страницу.'''


@auth.route('/confirm/<token>')
@login_required
def confirm(token):
    if current_user.confirmed:
        return redirect(url_for('main.index'))
    if current_user.confirm(token):
        db.session.commit()
        flash("Подтверждено")
        return redirect(url_for('auth.login'))
    else:
        flash("Ссылка не работает")
    return redirect(url_for('main.index'))


'''Обрабатывает запрос на страницу, где пользователю предлагается подтвердить учетную запись.
   Если пользователь уже авторизован и подтвержден, перенаправляет его на главную страницу.
   Иначе, отображает страницу с предложением подтвердить учетную запись.'''


@auth.route('/unconfirmed')
def unconfirmed():
    if current_user.is_anonymous or current_user.confirmed:
        return redirect(url_for('main.index'))
    return render_template('auth/unconfirmed.html')


'''Отправляет письмо пользователю для подтверждения учетной записи.
   Принимает объект пользователя и сгенерированный токен подтверждения, 
   создает URL-адрес для подтверждения и отправляет письмо пользователю.'''


def send_confirm(user, token):
    confirm_url = url_for('auth.confirm', token=token, _external=True)
    send_mail(user.email, 'Подтвердите свою учетную запись', 'auth/confirm', user=user, confirm_url=confirm_url)


'''Вспомогательная функция для отправки электронной почты.
   Принимает адрес электронной почты получателя, тему письма, имя шаблона и дополнительные параметры для шаблона.
   Создает экземпляр объекта сообщения, пытается отобразить HTML-версию сообщения, 
   а если это не удается, отображает простой текстовый вариант.
   Затем отправляет сообщение асинхронно в отдельном потоке.'''


def send_mail(to, subject, template, **kwargs):
    msg = Message(subject, sender="k27112999@gmail.com", recipients=[to])
    try:
        msg.html = render_template(template + ".html", **kwargs)
    except:
        msg.body = render_template(template + ".txt", **kwargs)
    from app_file import flask_app
    thread = Thread(target=send_async_email, args=[flask_app, msg])
    thread.start()
    return thread


'''Вспомогательная функция для асинхронной отправки электронной почты.
   Принимает экземпляр Flask-приложения и объект сообщения, 
   и отправляет сообщение в контексте приложения.'''


def send_async_email(app, msg):
    with app.app_context():
        mail.send(msg)
