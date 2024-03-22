import asyncio
from dataclasses import dataclass
from typing import Any

import aiohttp
import asyncpg
import discord
from discord.ext import commands

import config
from src import env
from src.env import DEEPL_API_KEY
from src.ext import MODULE_PATHS
from src.logging import book
from src.types.database import TLINK, Currency, StarBoard, TLink, Todo


class Vanir(commands.Bot):
    def __init__(self):
        super().__init__(
            command_prefix=commands.when_mentioned_or("\\"),
            tree_cls=VanirTree,
            intents=discord.Intents.all(),
            help_command=None,
            max_messages=5000,
        )
        self.connect_db_on_init: bool = config.use_system_assets
        self.db_starboard = StarBoard()
        self.db_currency = Currency()
        self.db_todo = Todo()
        self.db_link = TLink()
        self.session: VanirSession = VanirSession()

        self.cache: BotCache = BotCache(self)

        self.launch_time = discord.utils.utcnow()

        self.debug: bool = True

    async def get_context(
        self,
        origin: discord.Message | discord.Interaction,
        /,
        *,
        cls: Any = None,
    ) -> "VanirContext":
        return await super().get_context(origin, cls=VanirContext)

    async def setup_hook(self) -> None:
        if self.connect_db_on_init:
            book.info("Instantiating database pool and wrappers")
            self.pool = await asyncpg.create_pool(**env.PSQL_CONNECTION)

            if self.pool is None:
                raise RuntimeError("Could not connect to database")

            databases = [
                self.db_starboard,
                self.db_currency,
                self.db_todo,
                self.db_link,
            ]
            for db in databases:
                db.start(self.pool)

        else:
            book.info("Not connecting to database")

        await self.cache.init()
        await self.add_cogs()

    async def add_cogs(self):
        asyncio.gather(*(self.load_extension(ext) for ext in MODULE_PATHS))

        await self.load_extension("jishaku")
    
    async def add_cog(self, cog: commands.Cog):
        if config.use_system_assets or not getattr(cog, "uses_sys_assets", False):
            await super().add_cog(cog)
        else:
            book.info(
                f"Skipping {cog.qualified_name} because it requires system assets"
            )


class VanirTree(discord.app_commands.CommandTree):
    def __init__(self, client: discord.Client) -> None:
        super().__init__(client=client, fallback_to_global=True)


class VanirContext(commands.Context):
    bot: Vanir

    def embed(
        self,
        title: str | None = None,
        description: str | None = None,
        color: discord.Color | None = None,
        url: str | None = None,
    ) -> discord.Embed:
        if color is None:
            if isinstance(self.author, discord.Member):
                color = self.author.top_role.color
            else:
                color = discord.Color.light_embed()

        embed = discord.Embed(title=title, description=description, color=color)

        embed.set_author(
            name=f"{self.author.global_name or self.author.name}",
            icon_url=self.author.display_avatar.url,
        )

        if url is not None:
            embed.url = url
        return embed

    @staticmethod
    def syn_embed(
        title: str | None = None,
        description: str | None = None,
        color: discord.Color | None = None,
        url: str | None = None,
        *,
        user: discord.User | discord.Member,
    ) -> discord.Embed:
        if color is None:
            if isinstance(user, discord.Member):
                color = user.top_role.color
            else:
                color = discord.Color.light_embed()

        embed = discord.Embed(title=title, description=description, color=color)

        # %B %-d, %H:%M -> September 8, 13:59 UTC
        embed.set_author(
            name=f"{user.global_name or user.name}",
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

    async def deepl(
        self, path: str, headers: dict | None = None, json: dict | None = None
    ):
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


class BotCache:
    def __init__(self, bot: Vanir):
        self.bot = bot
        self.tlinks: list[TLINK] = []

        # channel id: (source_msg_id, translated_msg_id)
        self.tlink_translated_messages: dict[int, list[TranslatedMessage]] = {}

    async def init(self):
        if self.bot.connect_db_on_init:
            self.tlinks = await self.bot.db_link.get_all_links()


@dataclass
class TranslatedMessage:
    source_message_id: int
    translated_message_id: int
    source_author_id: int
