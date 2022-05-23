import requests
from bs4 import BeautifulSoup

LAST_USED_IMG = ['', '']
DB_NAME = 'users_db.sqlite'
QUALITIES = ['Unique', 'Strange', 'Vintage', 'Genuine', 'Unusual', "Collector's"]
LINK = 'https://steamcommunity.com/market/listings/440/'
BACKPACK_LINK = 'https://backpack.tf/stats/{}/{}/Tradable/Craftable'

EXCHANGE_TASK = 'https://free.currconv.com/api/v7/convert?q={}_RUB&compact=ultra&apiKey=ce89dafe2b42ce995034'
API_ADDRESS = 'http://127.0.0.1:8080/api/'

CURRENCIES = {'€': 'EUR', 'A$': 'AUD', '$USD': 'USD', 'ARS$': 'ARS', 'R$': 'BRL', '£': 'GBP', 'pуб.': 'RUB',
              'CDN$': 'CAD', '₴': 'UAH', '¥': 'JPY', 'COL$': 'COP', '฿': 'THB', 'P': 'PHP', 'S/.': 'PEN',
              'Rp': 'IDR', 'Mex$ ': 'MXN', 'zł': 'PLN', 'SR': 'SAR', 'pуб': 'RUB', 'NZ$ ': 'NZD',
              '₩': 'KRW', 'TL': 'TRY', '₸': 'KZT', '₫': 'VND', 'KD': 'KWD', 'S$': 'SGD', 'CLP$': 'CLP',
              '₪': 'ILS'}

CURRENCIES_TO_RUB = {}
"""try:
    '''Поиск курса ключа в рефах и рублях'''
    site = requests.get('https://backpack.tf/stats/Unique/Mann%20Co.%20Supply%20Crate%20Key/Tradable/Craftable')
    soup = BeautifulSoup(site.text, 'lxml')
    print(site.text)
    costs = soup.find_all('div', attrs={'class': 'value'})
    costs = list(map(lambda x: x.text.strip(), costs))[:2]
    costs[0] = float(costs[0].split('-')[0])
    costs[1] = float(costs[1][1:])
    KEY_COST = (costs[0], costs[1] * requests.get(EXCHANGE_TASK.format('USD')).json()['USD_RUB'])
except:
    print('Нет соединения с интернетом')"""
KEY_COST = [70.22, 71.250495]

def convert_steam_cost(elem):
    '''Функция, принимающая цену с торговой площадки Steam и возвращающая её в рублях
    Если цена была указане не в рублях последним элементом возвращаемого списка будет 1, т.е. цену пересчитывали'''
    elem = elem.text.strip().replace(',', '.').replace(' ', '')
    cost = ''
    curr = ''
    no_point = True
    if elem[0] == '₩':
        elem = ''.join(elem.split('.')[:-1])
    for i in elem:
        if i.isdigit():
            cost += i
        elif i == '.' and no_point and cost:
            cost += i
            no_point = False
        elif i == '-':
            cost += '0'
        else:
            curr += i
    if curr in ['CLP$']:
        cost = cost.replace('.', '')
    real_curr = CURRENCIES[curr]
    if real_curr == 'RUB':
        return float(cost)

    if real_curr not in CURRENCIES_TO_RUB.keys():
        CURRENCIES_TO_RUB[real_curr] = requests.get(EXCHANGE_TASK.format(real_curr)).json()['{}_RUB'.format(real_curr)]

    return round(float(cost) * CURRENCIES_TO_RUB[real_curr], 2)