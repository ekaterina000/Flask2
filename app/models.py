from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from . import db
from . import login_manager
import jwt


class Role(db.Model):
    __tablename__ = 'roles'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(60), unique=True)
    users = db.relationship('User', backref='role')

    def __repr__(self):
        return '<Role %r>' % self.name


class User(db.Model, UserMixin):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(64), unique=True, index=True)
    username = db.Column(db.String(60), unique=True, index=True)
    password_hash = db.Column(db.String(128))
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'))
    confirmed = db.Column(db.Boolean, default=False)

    def generate_confirmation_token(self):
        secret = 'secret-key'
        token = jwt.encode({'user_id': self.id}, secret, algorithm='HS256')
        return token

    def confirm(self, token):
        secret = 'secret-key'
        try:
            data = jwt.decode(token, secret, algorithms=['HS256'])
        except jwt.InvalidTokenError:
            print("Ссылка недействительна")
            return False

        if data.get('user_id') != self.id:
            print("Это не ваш токен")
            return False

        self.confirmed = True
        db.session.add(self)
        db.session.commit()
        return True

    @property
    def password(self):
        raise AttributeError('password not enable for read')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password, method='pbkdf2:sha256')

    def password_verify(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return '<User %r>' % self.username

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))