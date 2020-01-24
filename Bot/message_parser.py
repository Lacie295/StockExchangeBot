# created by Sami Bosch on Wednesday, 27 November 2019

# This file contains all functions necessary to reply to messages

from discord.ext import commands
import db_handler


def init(client):
    class Stock(commands.Cog):
        frozen = False

        @commands.command(pass_context=True,
                          aliases=['createaccount', 'createacc', 'create_acc', 'createacct', 'create_acct'])
        async def create_account(self, context):
            """Creates an account for users. Admin only.
            Usage: !create_account [@users]
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
            Usage: !check_amount [@user] or !check_amount company or !check_amount
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
                    if db_handler.get_owner(name) == m.author.id or m.author.guild_permissions.administrator:
                        amount = db_handler.get_account(name)
                        if amount is not None:
                            free = db_handler.get_free_stocks(name)
                            price = db_handler.get_price(name)
                            stocks = db_handler.get_stocks(name)
                            s = "Balance: " + str(amount) + "\n" + "Available stocks: " + str(
                                free) + "\n" + "Stock price: " + str(price) + "\n"
                            for uid in stocks:
                                s += m.guild.get_member(int(uid)).display_name + " has " + str(
                                    stocks[uid]) + " stocks.\n"
                            await context.send(s)
                        else:
                            await context.send("Company doesn't exist.")
                    else:
                        await context.send("You do not have permission to use this!")
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
            Usage: !create_company company stockprice
            Aliases: 'add'"""
            m = context.message
            if m.author.guild_permissions.administrator:
                split = m.content.split(" ")
                if len(split) == 3:
                    name = split[1]
                    price = float(split[2])
                    if db_handler.add_account(name):
                        db_handler.add_company(name, price)
                        await context.send("Created company.")
                    else:
                        await context.send("Company exists.")
                else:
                    await context.send("Please provide a company name and a price.")
            else:
                await context.send("You do not have permission to use this!")

        @commands.command(pass_context=True)
        async def set_owner(self, context):
            """Transfers company ownership. Admin or owner only.
            Usage: !set_owner @user"""
            m = context.message
            split = m.content.split(" ")
            if len(split) == 3 and len(m.mentions) == 1:
                name = split[1]
                mention = m.mentions[0]
                if db_handler.get_owner(name) == m.author.id or m.author.guild_permissions.administrator:
                    if db_handler.set_owner(name, mention.id):
                        await context.send("Ownership of " + name + " given to " + mention.display_name + ".")
                    else:
                        await context.send("Company doesn't exist.")
                else:
                    await context.send("You do not have permission to use this!")
            else:
                await context.send("Please provide a single company name.")

        @commands.command(pass_context=True)
        async def deposit(self, context):
            """Deposits amount into account, user or company. Admin only.
            Usage: !deposit @user amount or !deposit company amount"""
            m = context.message
            if m.author.guild_permissions.administrator:
                split = m.content.split(" ")
                if len(split) == 3 and len(m.mentions) == 1:
                    amount = float(split[2])
                    mention = m.mentions[0]
                    if db_handler.get_account(str(mention.id)) is not None:
                        db_handler.deposit(str(mention.id), amount)
                        await context.send("Deposited " + str(amount) + " into " + mention.display_name + "'s account.")
                    else:
                        await context.send("Account doesn't exist.")
                elif len(split) == 3:
                    name = split[1]
                    amount = float(split[2])
                    if db_handler.get_account(name) is not None:
                        db_handler.deposit(name, amount)
                        await context.send("Deposited " + str(amount) + " into " + name + "'s account.")
                    else:
                        await context.send("Company doesn't exist.")
                else:
                    await context.send("Please provide an account and an amount.")
            else:
                await context.send("You do not have permission to use this!")

        @commands.command(pass_context=True)
        async def withdraw(self, context):
            """Withdraws amount fromm account, user or company. Admin only.
            Usage: !withdraw @user amount or !withdraw company amount"""
            m = context.message
            if m.author.guild_permissions.administrator:
                split = m.content.split(" ")
                if len(split) == 3 and len(m.mentions) == 1:
                    amount = float(split[2])
                    mention = m.mentions[0]
                    if db_handler.get_account(str(mention.id)) is not None and db_handler.get_account(
                            str(mention.id)) >= amount:
                        db_handler.withdraw(str(mention.id), amount)
                        await context.send("Withdrew " + str(amount) + " from " + mention.display_name + "'s account.")
                    else:
                        await context.send("Account doesn't exist.")
                elif len(split) == 3:
                    name = split[1]
                    amount = float(split[2])
                    if db_handler.get_account(name) is not None and db_handler.get_account(name) >= amount:
                        db_handler.withdraw(name, amount)
                        await context.send("Withdrew " + str(amount) + " from " + name + "'s account.")
                    else:
                        await context.send("Company doesn't exist.")
                else:
                    await context.send("Please provide an account and an amount.")
            else:
                await context.send("You do not have permission to use this!")

        @commands.command(pass_context=True)
        async def buy(self, context):
            """Buy stocks from commpany.
            Usage: !buy company #stocks"""
            if self.frozen:
                await context.send("Market is frozen!")
            else:
                m = context.message
                split = m.content.split(" ")
                if len(split) == 3:
                    name = split[1]
                    amount = float(split[2])
                    if db_handler.buy_stock(name, str(m.author.id), amount):
                        await context.send("Stocks bought.")
                    else:
                        await context.send("Not enough funds or stocks left to buy.")
                else:
                    await context.send("Please provide a company and an amount.")

        @commands.command(pass_context=True)
        async def sell(self, context):
            """Sells stocks from commpany.
            Usage: !sell company #stocks"""
            if self.frozen:
                await context.send("Market is frozen!")
            else:
                m = context.message
                split = m.content.split(" ")
                if len(split) == 3:
                    name = split[1]
                    amount = float(split[2])
                    if db_handler.sell_stock(name, str(m.author.id), amount):
                        await context.send("Stocks sold.")
                    else:
                        await context.send("Not enough stocks left to sell.")
                else:
                    await context.send("Please provide a company and an amount.")

        @commands.command(pass_context=True)
        async def freeze(self, context):
            """Freezes the market. Admin only.
            Usage: !freeze"""
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
            Usage: !unfreeze"""
            m = context.message
            if m.author.guild_permissions.administrator:
                if not self.frozen:
                    await context.send("Market is already unfrozen.")
                else:
                    self.frozen = False
                    await context.send("Market is now unfrozen.")

    client.add_cog(Stock())
