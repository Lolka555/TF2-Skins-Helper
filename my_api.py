import datetime

import requests
from bs4 import BeautifulSoup
from flask import Blueprint, jsonify, make_response, request
from data import db_session
from data.user import User
from data.past_task import UserHistory
from constants import CURRENCIES_TO_RUB, LINK, convert_steam_cost, QUALITIES, BACKPACK_LINK, EXCHANGE_TASK, KEY_COST, LAST_USED_IMG

my_blueprint = Blueprint(
    'my_api',
    __name__
)


@my_blueprint.route('/api/users/<id>', methods=['GET'])
def get_user_inventory(id):
    session = db_session.create_session()
    user = session.query(User).get(id)
    if not user:
        return make_response(jsonify({'error': 'Not found'}), 404)
    return jsonify({'user_inventory': user.inventory_items.split(';')})


@my_blueprint.route('/api/users_history/<id>', methods=['GET'])
def get_user_history(id):
    session = db_session.create_session()
    history = session.query(UserHistory).get(id)
    if not history:
        return make_response(jsonify({'error': 'Not found'}), 404)
    history_dict = {}
    dates = history.tasks.split('#')[1:][::2]
    tasks = history.tasks.split('#')[1:]
    for i in range(len(dates)):
        date_list = []
        task = tasks[i * 2 + 1]
        items = task.split(';;')
        for item in items:
            item_info = {}
            keys = item.split('>')[1::2]
            vals = item.split('>')[2::2]
            for s in range(len(keys)):
                item_info[keys[s]] = vals[s]
            date_list.append(item_info)
        history_dict[dates[i]] = date_list

    return jsonify(history_dict)


@my_blueprint.route('/api/add_history/<history>/<id>', methods=['GET', 'POST'])
def add_user_history(history, id):
    try:
        db_sess = db_session.create_session()
        user = db_sess.query(UserHistory).get(id)
        if user:
            user.tasks += history
        else:
            user = UserHistory()
            user.userId = id
            user.tasks = history
        db_sess.add(user)
        db_sess.commit()
        return jsonify({'status': 'success'})
    except:
        return jsonify({'status': 'failed'})


@my_blueprint.route('/api/add_user/<login>/<password>', methods=['GET', 'POST'])
def add_user(login, password):
    try:
        db_sess = db_session.create_session()
        user = User()
        user.login = login
        user.password = password
        db_sess.add(user)
        db_sess.commit()
        return jsonify({'status': 'success'})
    except:
        return jsonify({'status': 'failed'})


@my_blueprint.route('/api/del_user/<id>', methods=['DELETE'])
def delete_user(id):
    try:
        session = db_session.create_session()
        user = session.query(User).get(id)
        if not user:
            return make_response(jsonify({'error': 'Not found'}), 404)
        session.delete(user)

        history = session.query(UserHistory).get(id)
        if history:
            session.delete(history)

        session.commit()
        return jsonify({'status': 'success'})
    except:
        return jsonify({'status': 'failed'})


@my_blueprint.route('/api/change_user/<id>', methods=['PUT'])
def change_user(id):
    try:
        if not request.json:
            return make_response({'error': 'Empty request'}, 400)
        session = db_session.create_session()
        user = session.query(User).get(id)
        if not user:
            return make_response(jsonify({'error': 'Not found'}), 404)

        for key, val in dict(request.json).items():
            if type(val) == str:
                exec(f'user.{key} = "{request.json[key]}"')
            else:
                exec(f'user.{key} = {request.json[key]}')
        session.commit()
        return jsonify({'status': 'success'})
    except:
        return jsonify({'status': 'failed'})


@my_blueprint.route('/api/users/inventory/<id>', methods=['GET', 'POST', 'PUT'])
def upload_inventory(id):
    try:
        if not request.json:
            return make_response({'error': 'Empty request'}, 400)
        session = db_session.create_session()
        user = session.query(User).get(id)
        if not user:
            return make_response(jsonify({'error': 'Not found'}), 404)
        print(user, request.json)
        user.inventory_path = request.json['path']
        user.inventory_items = request.json['items']
        session.commit()
        return jsonify({'status': 'success'})
    except:
        return jsonify({'status': 'failed'})


@my_blueprint.route('/api/find_on_steam/<name>', methods=['GET'])
def find_on_steam(name):
    global LAST_USED_IMG
    if name.split()[0] in QUALITIES:
        quality = name.split()[0]
    else:
        quality = QUALITIES[0]
    '''Поиск цен предмета на торговой площадке Steam'''
    item_page = requests.get(LINK + name)  # Получение страницы
    soup = BeautifulSoup(item_page.text, 'lxml')
    costs = soup.find_all('span', attrs={'class': 'market_listing_price_with_fee'})  # Парсинг страницы
    image = soup.find_all('meta')[-1]['content']
    LAST_USED_IMG = [name, image]
    if costs:
        costs = list(map(lambda x: convert_steam_cost(x), costs))
        return jsonify({'name': name, 'steam_costs': costs, 'image': image})
    else:
        if image.split('//')[-1] == '360fx360f':
            return make_response(jsonify({'error': 'Not found'}), 404)
        else:
            '''Поиск цен предмета на торговой площадке Steam через Backpack.tf'''
            if quality != 'Unique':
                name = name[name.find(quality) + len(quality) + 3:]
            item_page = requests.get(BACKPACK_LINK.format(quality, name))  # Получение страницы
            soup = BeautifulSoup(item_page.text, 'lxml')
            costs = soup.find_all('div', attrs={'class': 'value'})  # Парсинг страницы

            if not costs:
                return make_response(jsonify({'error': 'Not found'}), 404)

            index = 0 if len(costs) <= 2 else 1
            cost = float(costs[index].text.strip()[1:])
            if 'USD' not in CURRENCIES_TO_RUB.keys():
                CURRENCIES_TO_RUB['USD'] = requests.get(EXCHANGE_TASK.format('USD')).json()['{}_RUB'.format('USD')]
            cost = round(float(cost) * CURRENCIES_TO_RUB['USD'], 2)

            return jsonify({'name': name, 'steam_costs': cost, 'image': image})


@my_blueprint.route('/api/find_on_backpack/<name>', methods=['GET'])
def find_on_backpack(name):
    if name.split()[0] in QUALITIES:
        quality = name.split()[0]
    else:
        quality = QUALITIES[0]

    '''Поиск цен предмета на Backpack.tf'''
    if quality != 'Unique':
        bp_name = name[name.find(quality) + len(quality) + 3:]
    else:
        bp_name = name

    item_page = requests.get(BACKPACK_LINK.format(quality, bp_name))  # Получение страницы
    find_before = item_page.text.find('Buy Orders')
    '''Проверка что станица с предметом существует'''
    if find_before == -1:
        return make_response(jsonify({'error': 'Not found'}), 404)

    soup = BeautifulSoup(item_page.text[:find_before], 'lxml')
    costs = soup.find_all('div', attrs={'class': 'tag bottom-right'})[1:]  # Парсинг страницы
    if not costs:
        return make_response(jsonify({'error': 'Not found'}), 404)

    '''Обработка результатов (пересчет ключей в рубли; рефов в ключи и рубли)'''
    costs = sorted(map(lambda x: x.text.strip().split(), costs), key=lambda x: float(x[0]))
    for i in range(len(costs)):
        elem = costs[i]
        if elem[1] == 'ref':
            in_keys = round(float(elem[0]) / KEY_COST[0], 2)
            in_refs = float(elem[0])
            in_rubles = round(in_keys * KEY_COST[1], 2)
        else:
            in_keys = float(elem[0])
            in_refs = round(in_keys * KEY_COST[0], 2)
            in_rubles = round(in_keys * KEY_COST[1], 2)
        costs[i] = {'rubles': in_rubles, 'refs': in_refs, 'keys': in_keys}
    image = find_image(name).json['image']

    return jsonify({'name': name, 'backpack_costs': costs, 'image': image})

@my_blueprint.route('/api/find_on_steam_bp/<name>/<id>', methods=['GET'])
def find_on_steam_bp(name, id):
    global LAST_USED_IMG
    if name.split()[0] in QUALITIES:
        quality = name.split()[0]
    else:
        quality = QUALITIES[0]

    if quality != 'Unique':
        bp_name = name[name.find(quality) + len(quality) + 3:]
    else:
        bp_name = name

    history = f'#{str(datetime.datetime.now().date())}#>name>{name}'
    history += f'>steam_link>{LINK + name}'
    history += f'>backpack_link>{BACKPACK_LINK.format(quality, bp_name)}'
    history += '>result>'
    '''Поиск цен предмета на торговой площадке Steam'''
    item_page = requests.get(LINK + name)  # Получение страницы
    soup = BeautifulSoup(item_page.text, 'lxml')
    costs = soup.find_all('span', attrs={'class': 'market_listing_price_with_fee'})  # Парсинг страницы
    image = soup.find_all('meta')[-1]['content']
    LAST_USED_IMG = [name, image]
    if costs:
        history += 'Found,'
        costs = list(map(lambda x: convert_steam_cost(x), costs))

        backpack_costs = find_on_backpack(name).json
        if 'error' in backpack_costs:
            history += 'Not Found;;'
            backpack_costs = 'Not Found'
        else:
            history += 'Found;;'
            backpack_costs = backpack_costs['backpack_costs']

        print(history)
        add_user_history(history, id)
        return jsonify({'name': name, 'steam_costs': costs, 'backpack_costs': backpack_costs, 'image': image})

    else:
        if image.split('//')[-1] == '360fx360f':
            history += 'Not Found,Not Found;;'
            add_user_history(history, id)
            return make_response(jsonify({'error': 'Not found'}), 404)
        else:
            '''Поиск цен предмета на торговой площадке Steam через Backpack.tf'''
            item_page = requests.get(BACKPACK_LINK.format(quality, bp_name))  # Получение страницы
            soup = BeautifulSoup(item_page.text, 'lxml')
            costs = soup.find_all('div', attrs={'class': 'value'})  # Парсинг страницы
            index = 0 if len(costs) <= 2 else 1
            cost = float(costs[index].text.strip()[1:])
            if 'USD' not in CURRENCIES_TO_RUB.keys():
                CURRENCIES_TO_RUB['USD'] = requests.get(EXCHANGE_TASK.format('USD')).json()['{}_RUB'.format('USD')]
            cost = round(float(cost) * CURRENCIES_TO_RUB['USD'], 2)
            history += 'Found,'

            backpack_costs = find_on_backpack(name).json
            if 'error' in backpack_costs:
                history += 'Not Found;;'
                backpack_costs = 'Not Found'
            else:
                history += 'Found;;'
                backpack_costs = backpack_costs['backpack_costs']

            add_user_history(history, id)
            return jsonify({'name': name, 'steam_costs': costs, 'backpack_costs': backpack_costs, 'image': image})

@my_blueprint.route('/api/find_image/<name>', methods=['GET'])
def find_image(name):
    global LAST_USED_IMG
    if LAST_USED_IMG[0] == name:
        return jsonify({'image': LAST_USED_IMG[1]})

    item_page = requests.get(LINK + name)
    soup = BeautifulSoup(item_page.text, 'lxml')
    image = soup.find_all('meta')[-1]['content']
    LAST_USED_IMG = [name, image]
    return jsonify({'image': image})