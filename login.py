from flask_wtf import FlaskForm
from wtforms import EmailField, PasswordField, BooleanField, SubmitField


class LoginForm(FlaskForm):
    login = EmailField('Логин')
    password = PasswordField('Пароль')
    remember_me = BooleanField('Запомнить меня')
    submit = SubmitField('Войти')
    go_to_reg = SubmitField('Зарегистрироваться')

