import discord
from discord.ext import commands

from src.types.command import (
    VanirCog,
    cog_hidden,
    vanir_group,
)
from src.types.core import VanirContext


@cog_hidden
class Dev(VanirCog):
    def __init__(self, bot):
        super().__init__(bot)
        self.bot = bot

    @vanir_group()
    @commands.is_owner()
    async def dev(self, ctx):
        pass

    @dev.command()
    async def sync(self, ctx: VanirContext, *, guild_id: str | None = None):
        if guild_id:
            await self.bot.tree.sync(guild=discord.Object(id=int(guild_id)))
        else:
            await self.bot.tree.sync()

        await ctx.reply(embed=ctx.embed("Synced"))

    @dev.command()
    async def desync(self, ctx: VanirContext):
        self.bot.recursively_remove_all_commands()
        await self.bot.tree.sync()
        await ctx.reply(str(ctx.bot.commands))

    @dev.command()
    async def echo(self, ctx: VanirContext, *, message: str):
        await ctx.reply(message)

    @dev.command()
    async def setbal(self, ctx: VanirContext, user: discord.User, amount: int):
        await self.bot.db_currency.set_balance(user.id, amount)
        await ctx.reply(f"{user.id} -> {amount}")


async def setup(bot):
    await bot.add_cog(Dev(bot))
