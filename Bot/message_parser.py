# created by Sami Bosch on Wednesday, 27 November 2019

# This file contains all functions necessary to reply to messages

from discord.ext import commands
import db_handler
import re

r_int = r"^[0-9]*$"
r_float = r"^[0-9]+(.[0-9]]+)?$"


def init(client):
    class Stock(commands.Cog):
        frozen = False

        @commands.command(pass_context=True,
                          aliases=['createaccount', 'createacc', 'create_acc', 'createacct', 'create_acct'])
        async def create_account(self, context):
            """Creates an account for users. Admin only.
            Usage: %create_account [@users]
            Aliases: 'createaccount', 'createacc', 'create_acc', 'createacct', 'create_acct'"""
            m = context.message
            if m.author.guild_permissions.administrator:
                if m.mentions:
                    s = ""
                    f = ""
                    for member in m.mentions:
                        if db_handler.add_account(str(member.id)):
                            s += " " + member.display_name
                        else:
                            f += " " + member.display_name
                    await context.send(("Created accounts for" + s + "." if s else "")
                                       + ("Failed to create accounts for" + f + "." if f else ""))
                else:
                    await context.send("Please specify at least one user.")
            else:
                await context.send("You do not have permission to use this!")

        @commands.command(pass_context=True, aliases=['checkamount', 'check_amnt', 'checkamnt', 'check'])
        async def check_amount(self, context):
            """Checks a company or user's balance and stocks. Checking other companies and users is Admin only.
            Usage: %check_amount [@user] or %check_amount company or %check_amount
            Aliases: 'checkamount', 'check_amnt', 'checkamnt', 'check'"""
            m = context.message
            if m.mentions:
                if m.author.guild_permissions.administrator:
                    s = ""
                    f = ""
                    for member in m.mentions:
                        amnt = db_handler.get_account(str(member.id))
                        if amnt is not None:
                            s += member.display_name + " has " + str(amnt) + ".\n"
                            stocks = db_handler.get_user_stocks(str(member.id))
                            s += "Stock holdings:\n"
                            for name in stocks:
                                s += str(stocks[name]) + " in " + name + ".\n"
                            s += "\n"
                        else:
                            f += member.display_name + " "
                    await context.send((s if s else "")
                                       + (f + "has/have no account." if f else ""))
                else:
                    await context.send("You do not have permission to use this!")
            else:
                split = m.content.split(" ")
                if len(split) == 2:
                    name = split[1]
                    amount = db_handler.get_account(name)
                    if amount is not None:
                        free = db_handler.get_free_stocks(name)
                        price = db_handler.get_price(name)
                        stocks = db_handler.get_stocks(name)
                        owner = db_handler.get_owner(name)
                        revenue = db_handler.get_revenue(name)
                        s = "Balance: " + str(amount) + "\n" + "Available stocks: " + str(
                            free) + "\n" + "Stock price: " + str(
                            price) + "\n" + ("Owner: " + m.guild.get_member(
                            owner).display_name if owner else "No owner.") + "\n" + "Revenue: " + str(revenue) + "\n"
                        for uid in stocks:
                            s += m.guild.get_member(int(uid)).display_name + " has " + str(
                                stocks[uid]) + " stocks.\n"
                        await context.send(s)
                    else:
                        await context.send("Company doesn't exist.")
                else:
                    amnt = db_handler.get_account(str(m.author.id))
                    if amnt is not None:
                        s = "You have " + str(amnt) + ".\n"
                        stocks = db_handler.get_user_stocks(str(m.author.id))
                        s += "Stock holdings:\n"
                        for name in stocks:
                            s += str(stocks[name]) + " in " + name + ".\n"
                        s += "\n"
                        await context.send(s)
                    else:
                        await context.send("You have no account.")

        @commands.command(pass_context=True, aliases=['add'])
        async def create_company(self, context):
            """Creates a company. Admin only.
            Usage: %create_company company stockprice
            Aliases: 'add'"""
            m = context.message
            if m.author.guild_permissions.administrator:
                split = m.content.split(" ")
                if len(split) == 3:
                    name = split[1]
                    if re.match(r_float, split[2]):
                        price = float(split[2])
                        if db_handler.add_account(name):
                            db_handler.add_company(name, price)
                            await context.send("Created company.")
                        else:
                            await context.send("Company exists.")
                    else:
                        await context.send("2nd parameter must be a number.")
                else:
                    await context.send("Please provide a company name and a price.")
            else:
                await context.send("You do not have permission to use this!")

        @commands.command(pass_context=True)
        async def set_owner(self, context):
            """Transfers company ownership. Admin or owner only.
            Usage: %set_owner @user"""
            m = context.message
            split = m.content.split(" ")
            if len(split) == 3 and len(m.mentions) == 1:
                name = split[1]
                mention = m.mentions[0]
                if db_handler.get_account(str(mention.id)) is not None:
                    if db_handler.get_owner(name) == m.author.id or m.author.guild_permissions.administrator:
                        if db_handler.set_owner(name, mention.id):
                            await context.send("Ownership of " + name + " given to " + mention.display_name + ".")
                        else:
                            await context.send("Company doesn't exist.")
                    else:
                        await context.send("You do not have permission to use this!")
                else:
                    await context.send("User has no account!")
            else:
                await context.send("Please provide a single company name.")

        @commands.command(pass_context=True)
        async def deposit(self, context):
            """Deposits amount into account, user or company. Admin only.
            Usage: %deposit @user amount or %deposit company amount"""
            m = context.message
            if m.author.guild_permissions.administrator:
                split = m.content.split(" ")
                if len(split) == 3 and len(m.mentions) == 1:
                    mention = m.mentions[0]
                    if re.match(r_float, split[2]):
                        amount = float(split[2])
                        if db_handler.get_account(str(mention.id)) is not None:
                            db_handler.deposit(str(mention.id), amount)
                            await context.send("Deposited " + str(amount) + " into " + mention.display_name + "'s account.")
                        else:
                            await context.send("Account doesn't exist.")
                    else:
                        await context.send("2nd parameter must be a number.")
                elif len(split) == 3:
                    name = split[1]
                    if re.match(r_float, split[2]):
                        amount = float(split[2])
                        if db_handler.get_account(name) is not None:
                            db_handler.deposit(name, amount)
                            await context.send("Deposited " + str(amount) + " into " + name + "'s account.")
                        else:
                            await context.send("Company doesn't exist.")
                    else:
                        await context.send("2nd parameter must be a number.")
                else:
                    await context.send("Please provide an account and an amount.")
            else:
                await context.send("You do not have permission to use this!")

        @commands.command(pass_context=True)
        async def withdraw(self, context):
            """Withdraws amount fromm account, user or company. Admin only.
            Usage: %withdraw @user amount or %withdraw company amount"""
            m = context.message
            if m.author.guild_permissions.administrator:
                split = m.content.split(" ")
                if len(split) == 3 and len(m.mentions) == 1:
                    mention = m.mentions[0]
                    if re.match(r_float, split[2]):
                        amount = float(split[2])
                        if db_handler.get_account(str(mention.id)) is not None:
                            if db_handler.get_account(str(mention.id)) >= amount:
                                db_handler.withdraw(str(mention.id), amount)
                                await context.send(
                                    "Withdrew " + str(amount) + " from " + mention.display_name + "'s account.")
                            else:
                                await context.send("Not enough funds.")
                        else:
                            await context.send("Account doesn't exist.")
                    else:
                        await context.send("2nd parameter must be a number.")
                elif len(split) == 3:
                    name = split[1]
                    if re.match(r_float, split[2]):
                        amount = float(split[2])
                        if db_handler.get_account(name) is not None and db_handler.get_account(name) >= amount:
                            db_handler.withdraw(name, amount)
                            await context.send("Withdrew " + str(amount) + " from " + name + "'s account.")
                        else:
                            await context.send("Company doesn't exist.")
                    else:
                        await context.send("2nd parameter must be a number.")
                else:
                    await context.send("Please provide an account and an amount.")
            else:
                await context.send("You do not have permission to use this!")

        @commands.command(pass_context=True)
        async def buy(self, context):
            """Buy stocks from commpany.
            Usage: %buy company #stocks"""
            if self.frozen:
                await context.send("Market is frozen!")
            else:
                m = context.message
                split = m.content.split(" ")
                if len(split) == 3:
                    name = split[1]
                    if db_handler.get_owner(name) == m.author.id:
                        await context.send("You can't invest in your own company.")
                    else:
                        if re.match(r_int, split[2]):
                            amount = int(split[2])
                            if db_handler.buy_stock(name, str(m.author.id), amount):
                                await context.send("Stocks bought.")
                            else:
                                await context.send("Not enough funds or stocks left to buy.")
                        else:
                            await context.send("2nd parameter must be a number.")
                else:
                    await context.send("Please provide a company and an amount.")

        @commands.command(pass_context=True)
        async def sell(self, context):
            """Sells stocks from commpany.
            Usage: %sell company #stocks"""
            if self.frozen:
                await context.send("Market is frozen!")
            else:
                m = context.message
                split = m.content.split(" ")
                if len(split) == 3:
                    name = split[1]
                    if re.match(r_int, split[2]):
                        amount = int(split[2])
                        if db_handler.sell_stock(name, str(m.author.id), amount):
                            await context.send("Stocks sold.")
                        else:
                            await context.send("Not enough stocks left to sell.")
                    else:
                        await context.send("2nd parameter must be a number.")
                else:
                    await context.send("Please provide a company and an amount.")

        @commands.command(pass_context=True)
        async def freeze(self, context):
            """Freezes the market. Admin only.
            Usage: %freeze"""
            m = context.message
            if m.author.guild_permissions.administrator:
                if self.frozen:
                    await context.send("Market is already frozen.")
                else:
                    self.frozen = True
                    await context.send("Market is now frozen.")

        @commands.command(pass_context=True)
        async def unfreeze(self, context):
            """Unfreezes the market. Admin only.
            Usage: %unfreeze"""
            m = context.message
            if m.author.guild_permissions.administrator:
                if not self.frozen:
                    await context.send("Market is already unfrozen.")
                else:
                    self.frozen = False
                    await context.send("Market is now unfrozen.")

        @commands.command(pass_context=True, aliases=['release'])
        async def release_stocks(self, context):
            """Releases stocks for a company. Owner only.
            Usage: %release company #stocks
            Aliases: 'release'"""
            m = context.message
            split = m.content.split(" ")
            if len(split) == 3:
                name = split[1]
                if db_handler.get_owner(name) == m.author.id or m.author.guild_permissions.administrator:
                    if re.match(r_int, split[2]):
                        amount = int(split[2])
                        if db_handler.release_stocks(name, amount):
                            await context.send("Released " + str(amount) + " stocks for " + name + ".")
                        else:
                            await context.send("Can't release more than 100 stocks.")
                    else:
                        await context.send("2nd parameter must be a number.")
                else:
                    await context.send("You don't own this company.")
            else:
                await context.send("Please indicate a company and a quantity.")

        @commands.command(pass_context=True, aliases=['revenue'])
        async def set_revenue(self, context):
            """Sets revenue for a company. Owner only.
            Usage: %set_revenue company amount
            Aliases: 'revenue'"""
            m = context.message
            split = m.content.split(" ")
            if len(split) == 3:
                name = split[1]
                if db_handler.get_owner(name) == m.author.id or m.author.guild_permissions.administrator:
                    if re.match(r_float, split[2]):
                        amount = float(split[2])
                        db_handler.set_revenue(name, amount)
                        await context.send("Set revenue for " + name + " to " + str(amount) + ".")
                    else:
                        await context.send("2nd parameter must be a number.")
                else:
                    await context.send("You don't own this company.")
            else:
                await context.send("Please indicate a company and a quantity.")

        @commands.command(pass_context=True)
        async def list(self, context):
            """Lists all users and companies. Admin only.
            Usage: %list"""
            m = context.message
            if not m.author.guild_permissions.administrator:
                accounts = db_handler.db['accounts']
                s = "Users:\n"
                c = "Companies:\n"
                for acc in accounts:
                    if re.match(r_int, acc):
                        uid = int(acc)
                        member = m.guild.get_member(uid)
                        if member:
                            s += member.display_name + " " + acc
                        else:
                            user = client.get_user(uid)
                            if user:
                                s += "USER LEFT GUILD " + user.name + " " + acc
                            else:
                                s += "USER LEFT GUILD " + acc
                        s += "\n"
                    else:
                        owner = db_handler.get_owner(acc)
                        c += acc + " "
                        if owner is None:
                            c += "no owner"
                        else:
                            member = m.guild.get_member(owner)
                            if member is not None:
                                c += "owned by " + member.display_name
                            else:
                                c += "owned by USER LEFT GUILD " + str(owner)
                        c += "\n"
                await context.send(s + "\n" + c.strip())
            else:
                await context.send("You do not have permission to use this!")

        @commands.command(pass_context=True)
        async def delete_company(self, context):
            """Deletes a company. Owner and Admin only.
            Usage: %delete_company company"""
            m = context.message
            split = m.content.split(" ")
            if len(split) == 2:
                name = split[1]
                if db_handler.get_owner(name) == m.author.id or m.author.guild_permissions.administrator:
                    price = db_handler.get_price(name)
                    stocks = db_handler.get_stocks(name)
                    for stock in stocks:
                        db_handler.deposit(stock, stocks[stock] * price)
                    db_handler.delete_company(name)
                    await context.send(name + " deleted.")
                else:
                    await context.send("You do not have permission to use this!")
            else:
                await context.send("Please provide a company name!")

        @commands.command(pass_context=True)
        async def delete_user(self, context):
            """Deletes an user. Owner and Admin only.
            Usage: %delete_user user_id"""
            m = context.message
            split = m.content.split(" ")
            if len(split) == 2:
                if re.match(r_int, split[1]):
                    uid = int(split[1])
                    if db_handler.get_owner(uid) == m.author.id or not m.author.guild_permissions.administrator:
                        db_handler.delete_account(str(uid))
                        db_handler.delete_owner(uid)
                        await context.send(str(uid) + " deleted.")
                    else:
                        await context.send("You do not have permission to use this!")
                else:
                    await context.send("Parameter must be a number.")
            else:
                await context.send("Please provide a user id!")

    client.add_cog(Stock())
