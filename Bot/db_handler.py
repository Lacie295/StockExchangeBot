# created by Sami Bosch on Friday, 24 January 2020

# This class handles all accesses to db

import json
import os

songs = '../stocks.json'
dirname = os.path.dirname(__file__)
filename = os.path.join(dirname, songs)

if not os.path.exists(filename):
    with open(filename, "w+") as f:
        json.dump({"accounts": {}, "stocks": {}}, f)
        f.truncate()
        f.close()

with open(filename, "r+") as f:
    db = json.load(f)
    f.close()

print(db)

if "accounts" not in db:
    db['accounts'] = {}

if "stocks" not in db:
    db['stocks'] = {}


def write():
    with open(filename, "w+") as file:
        json.dump(db, file)
        file.truncate()
        file.close()


def add_account(uid):
    if uid not in db['accounts']:
        db['accounts'][uid] = 0.0
        write()
        return 1
    else:
        return 0


def get_account(uid):
    if uid in db['accounts']:
        return db['accounts'][uid]
    else:
        return None


def deposit(uid, amount):
    db['accounts'][uid] += amount
    write()


def withdraw(uid, amount):
    db['accounts'][uid] -= amount
    write()


def add_company(name, price):
    if name not in db['stocks']:
        db['stocks'][name] = [price, 100, {}, None]
        add_account(name)
        write()
        return 1
    else:
        return 0


def get_company(name):
    if name in db['stocks']:
        return db['stocks'][name]
    else:
        return None


def get_price(name):
    if name in db['stocks']:
        return db['stocks'][name][0]
    else:
        return None


def get_free_stocks(name):
    if name in db['stocks']:
        return db['stocks'][name][1]
    else:
        return None


def get_stocks(name):
    if name in db['stocks']:
        return db['stocks'][name][2]
    else:
        return None


def get_user_stocks(uid):
    if uid not in db['accounts']:
        return None
    s = {}
    for name in db['stocks']:
        stocks = get_stocks(name)
        if uid in stocks:
            s[name] = stocks[uid]
    return s


def get_owner(name):
    if name in db['stocks']:
        return db['stocks'][name][3]
    else:
        return None


def set_owner(name, uid):
    if name in db['stocks']:
        db['stocks'][name][3] = uid
        write()
        return 1
    else:
        return 0


def assign_stocks(name, uid, amount):
    c = get_company(name)
    c[1] -= amount
    stocks = get_stocks(name)
    if uid not in stocks:
        stocks[uid] = amount
    else:
        stocks[uid] += amount
    write()


def free_stocks(name, uid, amount):
    c = get_company(name)
    c[1] += amount
    stocks = get_stocks(name)
    stocks[uid] -= amount
    if stocks[uid] == 0:
        stocks.pop(uid)
    write()


def buy_stock(name, uid, amount):
    acct = get_account(uid)
    if acct is None or get_company(name) is None:
        return 0
    price = get_price(name) * amount
    if amount < get_free_stocks(name) and price <= acct:
        assign_stocks(name, uid, amount)
        withdraw(uid, price)
        return 1
    else:
        return 0


def sell_stock(name, uid, amount):
    stocks = get_stocks(name)
    if stocks is None or get_account(uid) is None:
        return 0
    price = get_price(name) * amount
    if uid in stocks and amount < stocks[uid]:
        free_stocks(name, uid, amount)
        deposit(uid, price)
        return 1
    else:
        return 0
