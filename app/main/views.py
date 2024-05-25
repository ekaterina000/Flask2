from flask import request, render_template, session, redirect, url_for
from app.main.forms import UserForm
from . import main
from app.models import User
from datetime import datetime
from flask_mail import Message
from app import mail
from flask_login import login_required
from .. import db

@main.route("/user/<name>")
def hello_user(name):
    return '<h2>, {}</h2>'.format(name)


@main.route("/user_info")
def info():
    user_ip = request.remote_addr
    user_agent = request.headers.get ('User-Agent')
    return '<h2>Your IP address is {}/</h2><h2>Your browser is {}</h2>'. format(user_ip, user_agent)


@main.route("/")
def index():
    today = datetime.now()
    session_text = session.get('text')
    if session_text is not None or session_text != '':
        return render_template('index.html', today=today)
    else:
        return render_template('index.html', today=today)


@main.route('/production_calendar')
def production_calendar():
    today = datetime.now()
    return render_template(today=today)



@main.route('/form', methods=['GET', 'POST'])
def form():
    form = UserForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is not None:
            session['auth'] = True
            confirm(user)
        else:
            session['auth'] = False
        return redirect(url_for('index'))
    return render_template('formTemplate.html', form=form,auth=session.get('auth'))

@main.route('/profile', methods=['GET', 'POST'])
def profile():
    if request.method == 'POST':
        session['username'] = request.form.get('username')
        session['email'] = request.form.get('email')
        session['gender'] = request.form.get('gender')
        return redirect(url_for('profile'))

    username = session.get('username')
    email = session.get('email')
    gender = session.get('gender')

    return render_template('profile.html', username=username, email=email, gender=gender)

'''@main.route('/logout')
def logout():
    if session.get('auth'):
        session['auth'] = False
    return redirect(url_for('index'))'''

@main.route('/confirm_auth')
def confirm(user):
    send_mail('k27112999@gmail.com','Добро пожаловать!', 'send_mail', user=user)
    redirect(url_for('index'))

def send_mail(to, subject, template, **kwargs):
    msg = Message(subject,
                  sender=main.config['MAIL_USERNAME'],
                  recipients=[to])
    msg.body = render_template(template+".txt", **kwargs)
    msg.html = render_template(template+".html", **kwargs)
    mail.send(msg)

@main.route('/secret')
@login_required
def secret():
    return "Only for auth"
