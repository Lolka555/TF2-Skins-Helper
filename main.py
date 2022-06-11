import os
import requests
from flask_login import LoginManager, login_user, current_user, logout_user, login_required
from flask import Flask, render_template, make_response, session
from werkzeug.utils import redirect, secure_filename
from data.user import User
from main_page_form import MainForm
from login import LoginForm
from reg import RegForm
from flask_restful import Api
from data import db_session
from my_api import my_blueprint
from constants import DB_NAME, API_ADDRESS

app = Flask(__name__)
api = Api(app)
app.config['SECRET_KEY'] = '727 WYSI'
login_manager = LoginManager()
login_manager.init_app(app)


@login_manager.user_loader
def load_user(user_id):
    db_sess = db_session.create_session()
    return db_sess.query(User).get(user_id)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect('/')


@app.route('/', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect('/main')
    form = LoginForm()
    if form.validate_on_submit():
        if form.submit.data:
            db_sess = db_session.create_session()
            user = db_sess.query(User).filter(User.login == form.login.data).first()
            if user and user.password == form.password.data:
                login_user(user, remember=form.remember_me.data)
                return redirect('/main')
            return render_template('authorize.html',
                                   message='Неправильный логин или пароль',
                                   form=form)
        if form.go_to_reg.data:
            return redirect('/reg')
    return render_template('authorize.html', title='Авторизация', form=form)


@app.route('/reg', methods=['GET', 'POST'])
def reg():
    form = RegForm()
    if form.validate_on_submit():
        requests.get(f'{API_ADDRESS}add_user/{form.login.data}/{form.password.data}')
        return redirect('/')

    return render_template('registration.html', title='Регистрация', form=form)


@app.route('/test')
def test():
    visits_count = session.get('visits_count', 0)
    session['visits_count'] = visits_count + 1
    return make_response(
        f'Вы пришли на эту страницу {visits_count + 1} раз')


@app.route('/main', methods=['GET', 'POST'])
@login_required
def main():
    form = MainForm()
    if form.validate_on_submit():
        if form.submit.data:
            filename = os.path.abspath(form.load_inventory.data)
            if not filename or filename.split('.')[-1] not in ['txt', 'pdf', 'doc']:
                return render_template('main.html', title='About |tems', form=form)
            with open(filename, 'r') as f:
                inventory_items = list(map(str.strip, f.readlines()))
            info = {'path': filename, 'items': ';'.join(inventory_items)}
            requests.request('POST', f'{API_ADDRESS}users/inventory/{current_user.get_id()}', json=info)
            for i in inventory_items:
                result = requests.get(f'{API_ADDRESS}find_on_steam_bp/{i}/{current_user.get_id()}').json()
                form.items.append(result)
        if form.logout.data:
            return redirect('/logout')
    return render_template('main.html', title='About |tems', form=form)


if __name__ == '__main__':
    db_session.global_init(os.path.join(os.getcwd(), DB_NAME))
    app.register_blueprint(my_blueprint)
    '''запускайте на вашем серваке'''
    app.run(port=8080, host='127.0.0.1') # локалка
