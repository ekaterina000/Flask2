from flask import render_template, redirect, request, flash, url_for
from flask_mail import Message
from . import auth
from .forms import LoginForm, RegistrationForm
from .. import db, mail
from ..models import User, Role
from flask_login import login_user, login_required, logout_user, current_user
from threading import Thread


@auth.before_app_request
def before_request():
    '''
    Выполняется перед каждым запросом.
    Проверяет, авторизован ли пользователь, и если да, обновляет время его последней активности.
    Если пользователь не подтвердил свою учетную запись и запрос не относится к авторизации или статическим файлам,
    перенаправляет его на страницу подтверждения.
    '''
    if current_user.is_authenticated:
        current_user.ping()
        if (
                not current_user.confirmed
                and request.blueprint != 'auth'
                and request.endpoint != 'static'
                and request.endpoint != 'auth.confirm'
        ):
            return redirect(url_for('auth.unconfirmed'))


@auth.route('/login', methods=['GET', 'POST'])
def login():
    '''
    Обрабатывает вход пользователя.
    Создает форму входа, проверяет введенные данные и, если они верны, авторизует пользователя.
    Если следующая страница указана в параметрах запроса, перенаправляет туда,
    иначе - на главную страницу.

    Returns:
        Возвращает HTML-страницу с формой входа или перенаправление на следующую страницу.
    '''
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


@auth.route("/register", methods=["GET", "POST"])
def register():
    '''
    Обрабатывает регистрацию нового пользователя.
    Создает форму регистрации, проверяет введенные данные и, если все в порядке,
    сохраняет пользователя в базе данных, генерирует токен подтверждения и отправляет письмо пользователю.
    После этого перенаправляет пользователя на страницу входа.

    Returns:
        Возвращает HTML-страницу с формой регистрации или перенаправление на страницу входа.
    '''
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


@auth.route("/logout")
@login_required
def logout():
    '''
    Обрабатывает выход пользователя из системы.
    Выполняет выход пользователя и перенаправляет его на главную страницу.

    Returns:
        Возвращает перенаправление на главную страницу.
    '''
    logout_user()
    flash("You have been logged out.")
    return redirect(url_for('main.index'))


@auth.route('/confirm/<token>')
@login_required
def confirm(token):
    '''
    Обрабатывает подтверждение учетной записи пользователя.

Если пользователь уже подтвержден, перенаправляет его на главную страницу.
Если токен подтверждения верный, подтверждает учетную запись пользователя и перенаправляет его на страницу входа.
Если токен недействителен, выводит сообщение об ошибке и перенаправляет на главную страницу.

Args:
    token (str): Токен подтверждения, отправленный пользователю по электронной почте.

Returns:
    Возвращает перенаправление на главную страницу или страницу входа.
'''
    if current_user.confirmed:
        return redirect(url_for('main.index'))
    if current_user.confirm(token):
        db.session.commit()
        flash("Подтверждено")
        return redirect(url_for('auth.login'))
    else:
        flash("Ссылка не работает")
    return redirect(url_for('main.index'))


def send_confirm(user, token):
    '''
    Отправляет пользователю письмо для подтверждения учетной записи.

    Args:
        user (User): Объект пользователя, которому необходимо отправить письмо.
        token (str): Токен подтверждения, который будет использован в ссылке для подтверждения.
    '''
    confirm_url = url_for('auth.confirm', token=token, _external=True)
    send_mail(user.email, 'Подтвердите свою учетную запись', 'auth/confirm', user=user, confirm_url=confirm_url)


def send_mail(to, subject, template, **kwargs):
    '''
    Вспомогательная функция для отправки электронной почты.
    Принимает адрес электронной почты получателя, тему письма, имя шаблона и дополнительные параметры для шаблона.
    Создает экземпляр объекта сообщения, пытается отобразить HTML-версию сообщения,
    а если это не удается, отображает простой текстовый вариант.
    Затем отправляет сообщение асинхронно в отдельном потоке.

    Args:
        to (str): Адрес электронной почты получателя.
        subject (str): Тема письма.
        template (str): Имя шаблона для отображения содержимого письма.
        **kwargs: Дополнительные параметры для передачи в шаблон.

    Returns:
        thread (Thread): Объект потока, в котором происходит отправка сообщения.
    '''
    msg = Message(subject, sender="k27112999@gmail.com", recipients=[to])
    try:
        msg.html = render_template(template + ".html", **kwargs)
    except:
        msg.body = render_template(template + ".txt", **kwargs)
    from app_file import flask_app
    thread = Thread(target=send_async_email, args=[flask_app, msg])
    thread.start()
    return thread


def send_async_email(app, msg):
    '''
    Вспомогательная функция для асинхронной отправки электронной почты.
    Принимает экземпляр Flask-приложения и объект сообщения,
    и отправляет сообщение в контексте приложения.

    Args:
        app (Flask): Экземпляр Flask-приложения.
        msg (Message): Объект сообщения электронной почты.
    '''
    with app.app_context():
        mail.send(msg)
