import datetime
from typing import AsyncGenerator, Any
import pkgutil

import aiohttp
import asyncpg
import discord
from discord.ext import commands

import logging

from src import env
from src.env import DEEPL_API_KEY
from src.types.database import StarBoard, Currency


class Vanir(commands.Bot):
    def __init__(self):
        super().__init__(
            command_prefix=commands.when_mentioned_or("\\"),
            tree_cls=VanirTree,
            intents=discord.Intents.all(),
            help_command=None,
            max_messages=5000,
        )
        self.db_starboard = StarBoard()
        self.db_currency = Currency()
        self.session: VanirSession = VanirSession()

    async def get_context(
        self,
        origin: discord.Message | discord.Interaction,
        /,
        *,
        cls: Any = None,
    ) -> "VanirContext":
        return await super().get_context(origin, cls=VanirContext)

    async def setup_hook(self) -> None:

        connection = await asyncpg.connect(**env.PSQL_CONNECTION)
        self.db_starboard.start(connection)
        self.db_currency.start(connection)

    async def add_cogs(self):
        for path in pkgutil.iter_modules(__path__, f"src.ext"):

            # TODO: Reimplement this set comparison jank into cog.on_load

            await self.load_extension(f"src.ext.{path[:-3]}")

        await self.load_extension("jishaku")


class VanirTree(discord.app_commands.CommandTree):
    def __init__(self, client: discord.Client) -> None:
        super().__init__(client=client, fallback_to_global=True)


class VanirContext(commands.Context):
    bot: Vanir

    def embed(
        self,
        title: str | None = None,
        description: str | None = None,
        color: discord.Color = None,
        url: str | None = None,
    ) -> discord.Embed:
        if title is None and description is None:
            raise ValueError("Must provide either a title or a description")

        if color is None:
            if isinstance(self.author, discord.Member):
                color = self.author.top_role.color
            else:
                color = discord.Color.light_embed()

        embed = discord.Embed(title=title, description=description, color=color)

        embed.set_footer(
            text=f"{self.author.global_name or self.author.name} @ {discord.utils.utcnow().strftime('%H:%M, %d %b, %Y')} UTC",
            icon_url=self.author.display_avatar.url,
        )

        if url is not None:
            embed.url = url
        return embed

    @staticmethod
    def syn_embed(
        title: str | None,
        description: str | None = None,
        color: discord.Color = None,
        url: str | None = None,
        *,
        user: discord.User | discord.Member,
    ) -> discord.Embed:
        if title is None and description is None:
            raise ValueError("Must provide either a title or a description")

        if color is None:
            if isinstance(user, discord.Member):
                color = user.top_role.color
            else:
                color = discord.Color.light_embed()

        embed = discord.Embed(title=title, description=description, color=color)

        # %B %-d, %H:%M -> September 8, 13:59 UTC
        embed.set_footer(
            text=f"{user.global_name or user.name} @ {datetime.datetime.utcnow().strftime('%H:%M, %d %b, %Y')} UTC",
            icon_url=user.display_avatar.url,
        )

        if url is not None:
            embed.url = url
        return embed


class VanirSession(aiohttp.ClientSession):
    def __init__(self):
        super().__init__(
            raise_for_status=False,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:101.0) Gecko/20100101 Firefox/101.0"
            },
        )

    async def deepl(self, path: str, headers: dict = None, json: dict = None):
        if headers is None:
            headers = {}
        if json is None:
            json = {}

        url = "https://api-free.deepl.com/v2"

        headers.update(
            {
                "Authorization": f"DeepL-Auth-Key {DEEPL_API_KEY}",
                "Content-Type": "application/json ",
            }
        )

        return await self.post(url + path, headers=headers, json=json)
