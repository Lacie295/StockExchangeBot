# created by Sami Bosch on Wednesday, 27 November 2019

# This file contains all functions necessary to reply to messages

from discord.ext import commands
import db_handler


def init(client):
    class Stock(commands.Cog):
        @commands.command(pass_context=True,
                          aliases=['createaccount', 'createacc', 'create_acc', 'createacct', 'create_acct'])
        async def create_account(self, context):
            m = context.message
            if m.author.guild_permissions.administrator:
                if m.mentions:
                    s = ""
                    f = ""
                    for member in m.mentions:
                        if db_handler.add_account(str(member.id)):
                            s += " " + member.name
                        else:
                            f += " " + member.name
                    await context.send(("Created accounts for" + s + "." if s else "")
                                       + ("Failed to create accounts for" + f + "." if f else ""))
                else:
                    await context.send("Please specify at least one user.")
            else:
                await context.send("You do not have permission to use this!")

        @commands.command(pass_context=True, aliases=['checkamount', 'check_amnt', 'checkamnt', 'check'])
        async def check_amount(self, context):
            m = context.message
            if m.mentions:
                if m.author.guild_permissions.administrator:
                    s = ""
                    f = ""
                    for member in m.mentions:
                        amnt = db_handler.get_account(str(member.id))
                        if amnt is not None:
                            s += member.name + " has " + str(amnt) + ".\n"
                            stocks = db_handler.get_user_stocks(str(member.id))
                            s += "Stock holdings:\n"
                            for name in stocks:
                                s += stocks[name] + " in " + name + ".\n"
                            s += "\n"
                        else:
                            f += member.name + " "
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
                                s += m.guild.get_member(uid).name + " has " + stocks[uid] + " stocks.\n"
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
                            s += stocks[name] + " in " + name + ".\n"
                        s += "\n"
                        await context.send(s)
                    else:
                        await context.send("You have no account.")

        @commands.command(pass_context=True, aliases=['add'])
        async def create_company(self, context):
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
            m = context.message
            split = m.content.split(" ")
            if len(split) == 3:
                name = split[1]
                mention = m.mentions[0]
                if db_handler.get_owner(name) == m.author.id or m.author.guild_permissions.administrator:
                    if db_handler.set_owner(name, mention.id):
                        await context.send("Ownership of " + name + " given to " + mention.name + ".")
                    else:
                        await context.send("Company doesn't exist.")
                else:
                    await context.send("You do not have permission to use this!")
            else:
                await context.send("Please provide a single company name.")



    client.add_cog(Stock())
