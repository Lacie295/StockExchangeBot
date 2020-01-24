# created by Sami Bosch on Wednesday, 27 November 2019

# This file contains all functions necessary to reply to messages

from discord.ext import commands


def init(client):
    class Example(commands.Cog):
        @commands.command(pass_context=True)
        async def example(self, context):
            m = context.message

    client.add_cog(Example())
