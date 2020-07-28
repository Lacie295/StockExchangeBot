# created by Sami Bosch on Friday, 24 January 2020

# This class handles all accesses to db

import json
import os

VERSION = 1.1
MAX_STOCKS = 1000

songs = '../stocks.json'
dirname = os.path.dirname(__file__)
filename = os.path.join(dirname, songs)

if not os.path.exists(filename):
    with open(filename, "w+") as f:
        json.dump({"accounts": {}, "stocks": {}, "sales": {}, "channels": {}, "version": VERSION, "alias": {},
                   "alias_rev": {}}, f)
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

if "channels" not in db:
    db['channels'] = {}

if "version" not in db:
    db['version'] = VERSION

if "alias" not in db:
    db['alias'] = {}

if "alias_rev" not in db:
    db['alias_rev'] = {}

for name in db['stocks']:
    stocks = {}
    for owner in db['stocks'][name][2]:
        if db['stocks'][name][2][owner] > 0:
            stocks[owner] = db['stocks'][name][2][owner]
    db['stocks'][name][2] = stocks


def write():
    with open(filename, "w+") as file:
        json.dump(db, file)
        file.truncate()
        file.close()


write()


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
    alias = reverse_alias(uid)
    if alias is not None:
        uid = alias
    if uid in db['accounts']:
        return db['accounts'][uid]
    else:
        return None


def deposit(uid, amount):
    alias = reverse_alias(uid)
    if alias is not None:
        uid = alias
    db['accounts'][uid] += amount
    db['accounts'][uid] = round(db['accounts'][uid] * 100) / 100
    write()


def withdraw(uid, amount):
    alias = reverse_alias(uid)
    if alias is not None:
        uid = alias
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
        remove_alias(name)
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


def get_company(name, alias=True):
    if name in db['stocks']:
        return db['stocks'][name]
    elif name in db['alias'] and alias:
        return db['stocks'][db['alias'][name]]
    else:
        return None


def get_stock_data(name, n):
    if name in db['stocks']:
        return db['stocks'][name][n]
    elif name in db['alias']:
        return db['stocks'][db['alias'][name]][n]
    else:
        return None


def set_stock_data(name, n, value):
    if name in db['stocks']:
        db['stocks'][name][n] = value
        write()
        return 1
    elif name in db['alias']:
        db['stocks'][db['alias'][name]][n] = value
        write()
        return 1
    else:
        return 0


def get_price(name):
    return get_stock_data(name, 0)


def set_price(name, price):
    return set_stock_data(name, 0, price)


def get_free_stocks(name):
    return get_stock_data(name, 1)


def get_stocks(name):
    return get_stock_data(name, 2)


def get_user_stocks(uid):
    if uid not in db['accounts']:
        return {}
    s = {}
    for name in db['stocks']:
        stocks = get_stocks(name)
        if uid in stocks:
            s[name] = stocks[uid]
    return s


def get_owner(name):
    return get_stock_data(name, 3)


def set_owner(name, uid):
    return set_stock_data(name, 3, uid)


def get_revenue(name):
    return get_stock_data(name, 4)


def set_revenue(name, revenue):
    return set_stock_data(name, 4, revenue)


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
    if free + amount > MAX_STOCKS:
        return 0
    else:
        get_company(name)[1] += amount
        write()
        return 1


def buy_stock(name, uid, amount):
    acct = get_account(uid)
    if acct is None or get_company(name) is None:
        return 0
    price = round(get_price(name) * amount, 2)
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


def add_request(uid, name, amount, price):
    # if amount < 0, uid is selling, check if -amount < owned stocks
    stocks = get_stocks(name)
    if stocks is not None and len(stocks) != 0 and ((uid in stocks and -amount <= stocks[uid]) or amount <= 100) and amount != 0:
        if name not in db['sales']:
            db['sales'][name] = {}
        db['sales'][name][uid] = (amount, price)
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


def edit_request(uid, name, amount, price):
    if remove_request(uid, name) and add_request(uid, name, amount, price):
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
                edit_request(sid, name, max_amount - amount, request[1])
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


def set_offers_message(gid, cid, mid):
    db['channels']["offers"] = (gid, cid, mid)
    write()


def get_offers_message():
    return db['channels']["offers"]


def get_names():
    return db['stocks'].keys()


def get_alias(name):
    if name in db['alias_rev']:
        return db['alias_rev'][name]
    else:
        return None


def reverse_alias(name):
    if name in db['alias']:
        return db['alias'][name]
    else:
        return None


def remove_alias(name):
    if get_alias(name) is not None:
        db['alias'].pop(get_alias(name))
        db['alias_rev'].pop(name)
        write()
        return 1
    else:
        return 0


def set_alias(alias, name):
    if get_company(name, False) is not None and get_company(alias) is None:
        remove_alias(name)
        db['alias'][alias] = name
        db['alias_rev'][name] = alias
        write()
        return 1
    else:
        return 0
