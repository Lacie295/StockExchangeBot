# created by Sami Bosch on Wednesday, 27 November 2019

# This file contains all functions necessary to reply to messages

from discord.ext import commands
import db_handler
import re
import discord

r_int = r"^[0-9]*$"
r_float = r"^[0-9]+(\.[0-9]+)?$"
currency = "g"


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
                    embed = discord.Embed(title="User data", colour=discord.Colour.blue())

                    for member in m.mentions:
                        amnt = db_handler.get_account(str(member.id))
                        if amnt is not None:
                            embed.add_field(name="User", value=member.display_name, inline=True)
                            embed.add_field(name="Balance", value=str(amnt) + currency, inline=True)

                            stocks = db_handler.get_user_stocks(str(member.id))
                            for name in stocks:
                                embed.add_field(name="Stocks in " + name + ":", value=str(stocks[name]), inline=False)

                        else:
                            embed.add_field(name=member.display_name, value="No account", inline=False)
                    await context.send(embed=embed)
                else:
                    await context.send("You do not have permission to use this!")
            else:
                split = m.content.split(" ")
                if len(split) == 2:
                    name = split[1]
                    amount = db_handler.get_account(name)
                    if amount is not None:
                        embed = discord.Embed(title="Company data", colour=discord.Colour.blue())
                        free = db_handler.get_free_stocks(name)
                        price = db_handler.get_price(name)
                        stocks = db_handler.get_stocks(name)
                        owner = db_handler.get_owner(name)
                        owner_user = m.guild.get_member(owner)
                        revenue = db_handler.get_revenue(name)
                        alias = db_handler.get_alias(name)
                        embed.add_field(name="Company", value=name, inline=True)
                        if alias is not None:
                            embed.add_field(name="Alias", value=alias, inline=True)
                        embed.add_field(name="Balance", value=str(amount) + currency, inline=True)
                        embed.add_field(name="Free Stocks", value=free, inline=True)
                        embed.add_field(name="Stock Price", value=str(price) + currency, inline=True)
                        embed.add_field(name="Owner", value=(owner_user.display_name if owner_user is not None else
                                                             "USER LEFT GUILD") if owner is not None else "No owner",
                                        inline=True)
                        embed.add_field(name="Revenue", value=str(revenue) + currency, inline=True)
                        for uid in stocks:
                            member = m.guild.get_member(int(uid))
                            embed.add_field(name="Stocks owned by " + (member.display_name if member else
                                                                       "USER LEFT GUILD"), value=str(stocks[uid]),
                                            inline=False)
                        await context.send(embed=embed)
                    else:
                        await context.send("Company doesn't exist.")
                else:
                    amnt = db_handler.get_account(str(m.author.id))
                    if amnt is not None:
                        embed = discord.Embed(title="User data", colour=discord.Colour.blue())
                        embed.add_field(name="User", value=m.author.display_name, inline=True)
                        embed.add_field(name="Balance", value=str(amnt) + currency, inline=True)

                        stocks = db_handler.get_user_stocks(str(m.author.id))
                        for name in stocks:
                            embed.add_field(name="Stocks in " + name + ":", value=str(stocks[name]), inline=False)
                        await context.send(embed=embed)
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
                            await context.send(
                                "Created company" + name + " with stock price " + str(price) + currency + ".")
                            await update_offers()
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
            Usage: %set_owner company @user"""
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
        async def set_price(self, context):
            """Sets the price of company stocks. Admin only.
            Usage: %set_price company price"""
            m = context.message
            split = m.content.split(" ")
            if len(split) == 3:
                name = split[1]
                if re.match(r_float, split[2]):
                    price = float(split[2])
                    if db_handler.set_price(name, price):
                        await context.send("Set stock price of " + name + " to " + str(price) + currency + ".")
                    else:
                        await context.send("Company doesn't exist.")
                else:
                    await context.send("2nd parameter must be a number.")
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
                            await context.send(
                                "Deposited " + str(amount) + currency + " into " + mention.display_name + "'s account.")
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
                            await context.send("Deposited " + str(amount) + currency + " into " + name + "'s account.")
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
                                    "Withdrew " + str(
                                        amount) + currency + " from " + mention.display_name + "'s account.")
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
                            await context.send("Withdrew " + str(amount) + currency + " from " + name + "'s account.")
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
            """Buy free stocks from company.
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
                                await update_offers()
                            else:
                                await context.send("Not enough funds or stocks left to buy.")
                        else:
                            await context.send("2nd parameter must be a number.")
                else:
                    await context.send("Please provide a company and an amount.")

        @commands.command(pass_context=True)
        async def offer(self, context):
            """Puts up an offer to sell stocks.
            Usage: %offer company #stocks price/stock"""
            if self.frozen:
                await context.send("Market is frozen!")
            else:
                m = context.message
                split = m.content.split(" ")
                if len(split) == 4:
                    name = split[1]
                    if db_handler.get_stocks(name) is None:
                        await context.send("Company doesn't exist.")
                    else:
                        if re.match(r_int, split[2]) and re.match(r_float, split[3]):
                            amount = int(split[2])
                            price = float(split[3])
                            if db_handler.add_request(str(m.author.id), name, -amount, price):
                                await context.send(str(amount) + " " + name + " stocks set for sale at " + str(
                                    price) + currency + " a piece.")
                                await update_offers()
                            else:
                                await context.send("Not enough stocks left to sell.")
                        else:
                            await context.send("2nd and 3rd parameter must be numbers.")
                else:
                    await context.send("Please provide a company, an amount and a price.")

        @commands.command(pass_context=True)
        async def request(self, context):
            """Puts up a request to sell stocks.
            Usage: %request company #stocks price/stock"""
            if self.frozen:
                await context.send("Market is frozen!")
            else:
                m = context.message
                split = m.content.split(" ")
                if len(split) == 4:
                    name = split[1]
                    if db_handler.get_stocks(name) is None:
                        await context.send("Company doesn't exist.")
                    else:
                        if re.match(r_int, split[2]) and re.match(r_float, split[3]):
                            amount = int(split[2])
                            price = float(split[3])
                            if db_handler.add_request(str(m.author.id), name, amount, price):
                                await context.send("Request set for " + str(amount) + " " + name + " stocks at " + str(
                                    price) + currency + " a piece.")
                                await update_offers()
                            else:
                                await context.send("Not enough stocks left to sell.")
                        else:
                            await context.send("2nd and 3rd parameter must be numbers.")
                else:
                    await context.send("Please provide a company, an amount and a price.")

        @commands.command(pass_context=True)
        async def accept(self, context):
            """Accepts a request or offer and does the transaction.
            Usage: %accept @user company #stocks"""
            if self.frozen:
                await context.send("Market is frozen!")
            else:
                m = context.message
                split = m.content.split(" ")
                if len(split) == 4 and len(m.mentions) == 1:
                    s = m.mentions[0]
                    sid = str(s.id)
                    bid = str(m.author.id)
                    name = split[2]
                    if re.match(r_int, split[3]):
                        if sid == bid:
                            await context.send("Cannot do a transaction with yourself.")
                        else:
                            amount = int(split[3])
                            req = db_handler.get_request(sid, name)
                            if req is not None:
                                sell = -1 if req[0] < 0 else 1
                                if db_handler.confirm_sale(sid, bid, name, amount * sell):
                                    await context.send(
                                        "Exchanged " + str(amount) + " stocks with " + s.display_name + ".")
                                    await update_offers()
                                else:
                                    await context.send("Not enough stocks or funds.")
                            else:
                                await context.send("Offer/Request does not exist.")
                    else:
                        await context.send("3rd parameter must be a number.")
                else:
                    await context.send("Please provide a user, a company and an amount.")

        @commands.command(pass_context=True)
        async def list_offers(self, context):
            """Lists all current offers and requests for a company.
            Usage: %list_offers company"""
            m = context.message
            split = m.content.split(" ")
            if len(split) == 2:
                name = split[1]
                requests = db_handler.get_requests(name)
                if requests is None:
                    await context.send("No offers or request currently available for " + name + ".")
                else:
                    embed = discord.Embed(title="Offers for " + name, colour=discord.Colour.red())
                    value = ""
                    for uid in requests:
                        member = m.guild.get_member(int(uid))
                        uname = member.display_name if member else "USER LEFT GUILD"
                        price = requests[uid][1]
                        amount = requests[uid][0]
                        value += uname + (" selling " if amount < 0 else " requesting ") + str(
                            abs(amount)) + " for " + str(price) + currency + " per stock\n"
                    embed.add_field(name="Listings",
                                    value=value,
                                    inline=False)
                    if len(requests) > 0:
                        await context.send(embed=embed)
                    else:
                        await context.send("No requests for " + name + ".")
            else:
                await context.send("Please provide a company.")

        @commands.command(pass_context=True)
        async def list_all_offers(self, context):
            """Lists all current offers and requests.
            Usage: %list_all_offers"""
            m = context.message
            if m.author.guild_permissions.administrator:
                message = await context.send("loading...")
                mid = message.id
                cid = m.channel.id
                gid = m.guild.id
                db_handler.set_offers_message(gid, cid, mid)
                await update_offers()

        @commands.command(pass_context=True)
        async def remove_offer(self, context):
            """Removes your current offer/request on the company.
            Usage: %remove_offer company"""
            if self.frozen:
                await context.send("Market is frozen!")
            else:
                m = context.message
                split = m.content.split(" ")
                if len(split) == 2:
                    name = split[1]
                    uid = str(m.author.id)
                    result = db_handler.remove_request(uid, name)
                    if result:
                        await context.send("Removed your offer.")
                        await update_offers()
                    else:
                        await context.send("No offer to be removed.")
                else:
                    await context.send("Please provide a company.")

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
                if m.author.guild_permissions.administrator:
                    if re.match(r_int, split[2]):
                        amount = int(split[2])
                        if db_handler.release_stocks(name, amount):
                            await context.send("Released " + str(amount) + " stocks for " + name + ".")
                            await update_offers()
                        else:
                            await context.send("Can't release more than " + str(db_handler.MAX_STOCKS) + " stocks.")
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
                        await context.send("Set revenue for " + name + " to " + str(amount) + currency + ".")
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
            if m.author.guild_permissions.administrator:
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
                        alias = db_handler.get_alias(acc)
                        c += acc + (" " + "(" + alias + ") ") if alias is not None else " "
                        if owner is None:
                            c += "no owner"
                        else:
                            member = m.guild.get_member(owner)
                            if member is not None:
                                c += "owned by " + member.display_name
                            else:
                                c += "owned by USER LEFT GUILD " + str(owner)
                        c += "\n"
                s = s + "\n" + c.strip()

                buffer = ""
                while s.find("\n") > 0:
                    chunk = s[:s.find("\n") + 1]
                    if len(buffer + chunk) > 2000:
                        await context.send(buffer)
                        buffer = ""
                    buffer += chunk
                    s = s[s.find("\n") + 1:]

                await context.send(buffer + s)
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
                    await update_offers()
                else:
                    await context.send("You do not have permission to use this!")
            else:
                await context.send("Please provide a company name!")

        @commands.command(pass_context=True)
        async def delete_user(self, context):
            """Deletes an user. Admin only.
            Usage: %delete_user user_id"""
            m = context.message
            split = m.content.split(" ")
            if len(split) == 2:
                if re.match(r_int, split[1]):
                    uid = int(split[1])
                    if m.author.guild_permissions.administrator:
                        db_handler.delete_account(str(uid))
                        db_handler.delete_owner(uid)
                        await context.send(str(uid) + " deleted.")
                    else:
                        await context.send("You do not have permission to use this!")
                else:
                    await context.send("Parameter must be a number.")
            else:
                await context.send("Please provide a user id!")

        @commands.command(pass_context=True)
        async def set_alias(self, context):
            """Sets an alias for a company. Owner and Admin only.
            Usage: %delete_user user_id"""
            m = context.message
            split = m.content.split(" ")
            if len(split) == 3:
                name = split[1]
                alias = split[2]
                if len(alias) == 4:
                    if db_handler.get_owner(name) == m.author.id or m.author.guild_permissions.administrator:
                        db_handler.set_alias(alias.upper(), name)
                        await context.send("Alias set.")
                    else:
                        await context.send("You do not have permission to use this!")
                else:
                    await context.send("Alias must be 4 letters long!")
            else:
                await context.send("Please provide a company and an alias!")

        @commands.command(pass_context=True)
        async def delete_alias(self, context):
            """Deletes the alias of a company. Owner and Admin only.
            Usage: %delete_user user_id"""
            m = context.message
            split = m.content.split(" ")
            if len(split) == 2:
                name = split[1]
                if db_handler.get_owner(name) == m.author.id or m.author.guild_permissions.administrator:
                    db_handler.remove_alias(name)
                    await context.send("Alias set.")
                else:
                    await context.send("You do not have permission to use this!")
            else:
                await context.send("Please provide a company!")

    async def update_offers():
        gid, cid, mid = db_handler.get_offers_message()
        guild = client.get_guild(gid)
        channel = guild.get_channel(cid)
        message = await channel.fetch_message(mid)
        names = db_handler.get_names()
        embed = discord.Embed(title="All offers", colour=discord.Colour.dark_gold())
        for name in names:
            stemp = ""
            alias = db_handler.get_alias(name)
            requests = db_handler.get_requests(name)
            free = db_handler.get_free_stocks(name)
            if requests is None:
                stemp = "\tNo requests.\n"
            else:
                for uid in requests:
                    amount, price = requests[uid]
                    member = guild.get_member(int(uid))
                    temp = " selling " if amount < 0 else " asking for "
                    amount = amount if amount > 0 else -amount
                    if member:
                        stemp += "\t" + member.display_name
                    else:
                        stemp += "\t" + "USER LEFT GUILD"
                    stemp += temp + str(amount) + " stocks at " + str(price) + currency + " a piece.\n"
            stemp += "Available stocks: " + str(free)
            embed.add_field(name="Offers for " + name + (" (" + alias + ")") if alias is not None else "", value=stemp,
                            inline=False)
        await message.edit(content="", embed=embed)

    client.add_cog(Stock())
