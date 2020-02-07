# created by Sami Bosch on Friday, 24 January 2020

# This class handles all accesses to db

import json
import os

songs = '../stocks.json'
dirname = os.path.dirname(__file__)
filename = os.path.join(dirname, songs)

if not os.path.exists(filename):
    with open(filename, "w+") as f:
        json.dump({"accounts": {}, "stocks": {}, "sales": {}}, f)
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

if "sales" not in db:
    db['sales'] = {}


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


def delete_account(uid):
    if uid in db['accounts']:
        acc = db['accounts'].pop(uid)
        for name in get_user_stocks(uid):
            free_stocks(name, uid, get_user_stocks(uid)[name])
        write()
        return acc
    else:
        return None


def get_account(uid):
    if uid in db['accounts']:
        return db['accounts'][uid]
    else:
        return None


def deposit(uid, amount):
    db['accounts'][uid] += amount
    db['accounts'][uid] = round(db['accounts'][uid] * 100) / 100
    write()


def withdraw(uid, amount):
    db['accounts'][uid] -= amount
    db['accounts'][uid] = round(db['accounts'][uid] * 100) / 100
    write()


def add_company(name, price):
    if name not in db['stocks']:
        db['stocks'][name] = [price, 0, {}, None, 0.0]
        add_account(name)
        write()
        return 1
    else:
        return 0


def delete_company(name):
    if name in db['stocks']:
        company = db['stocks'].pop(name)
        acc = delete_account(name)
        write()
        return company, acc
    else:
        return None


def delete_owner(uid):
    for name in db['stocks']:
        company = get_company(name)
        if get_owner(name) == uid:
            company[3] = None
    write()


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


def set_price(name, price):
    if name in db['stocks']:
        db['stocks'][name][0] = price
        return 1
    else:
        return 0


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


def get_revenue(name):
    if name in db['stocks']:
        return db['stocks'][name][4]
    else:
        return None


def set_revenue(name, revenue):
    if name in db['stocks']:
        db['stocks'][name][4] = revenue
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


def release_stocks(name, amount):
    free = get_free_stocks(name)
    stocks = get_stocks(name)
    for uid in stocks:
        free += stocks[uid]
    if free + amount > 100:
        return 0
    else:
        get_company(name)[1] += amount
        return 1


def buy_stock(name, uid, amount):
    acct = get_account(uid)
    if acct is None or get_company(name) is None:
        return 0
    price = get_price(name) * amount
    if amount <= get_free_stocks(name) and price <= acct:
        assign_stocks(name, uid, amount)
        withdraw(uid, price)
        deposit(name, price)
        return 1
    else:
        return 0


def sell_stock(name, uid, amount):
    stocks = get_stocks(name)
    if stocks is None or get_account(uid) is None:
        return 0
    price = get_price(name) * amount
    if uid in stocks and amount <= stocks[uid]:
        free_stocks(name, uid, amount)
        deposit(uid, price)
        return 1
    else:
        return 0


def add_request(uid, name, price, amount):
    # if amount < 0, uid is selling, check if -amount < owned stocks
    if uid in get_stocks(name) and -amount <= get_stocks(name)[uid]:
        if name not in db['sales']:
            db['sales'][name] = {}
        db['sales'][name][uid] = (price, amount)
        write()
        return 1
    else:
        return 0


def remove_request(uid, name):
    if name in db['sales'] and uid in db['sales'][name]:
        db['sales'][name].pop(uid)
        write()
        return 1
    else:
        return 0


def get_request(uid, name):
    if name in db['sales'] and uid in db['sales'][name]:
        return db['sales'][name][uid]
    else:
        return None


def get_requests(name):
    if name in db['sales']:
        return db['sales'][name]
    else:
        return None


def edit_request(uid, name, price, amount):
    if remove_request(uid, name) and add_request(uid, name, price, amount):
        write()
        return 1
    else:
        return 0


def confirm_sale(sid, bid, name, amount):
    # sid created the request, bid is confirming it
    request = get_request(sid, name)
    if request is None:
        return 0
    else:
        price = abs(request[1] * amount)
        max_amount = request[0]
        if max_amount <= amount < 0 and price <= get_account(bid):
            # sid was selling, amount is negative
            # bid pays, sid gains
            withdraw(bid, price)
            deposit(sid, price)

            # change the stocks
            free_stocks(name, sid, -amount)
            assign_stocks(name, bid, -amount)

            # change the request
            if amount == max_amount:
                remove_request(sid, name)
            else:
                edit_request(sid, name, request[0], max_amount - amount)
            return 1
        elif max_amount >= amount > 0 and price <= get_account(sid):
            # sid was buying, amount is positive
            # sid pays, bid gains
            withdraw(sid, price)
            deposit(bid, price)

            # change the stocks
            assign_stocks(name, sid, amount)
            free_stocks(name, bid, amount)

            # change the request
            if amount == max_amount:
                remove_request(sid, name)
            else:
                edit_request(sid, name, request[0], max_amount - amount)
            return 1
        else:
            return 0
