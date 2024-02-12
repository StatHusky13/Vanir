import discord
from discord import InteractionResponse
from discord.ext import commands

from src.types.command_types import cog_hidden, VanirCog, vanir_group, VanirView
from src.types.core_types import VanirContext, Vanir
from src.util import (
    format_dict,
    discover_cog,
    discover_group,
    get_display_cogs,
    get_param_annotation,
)


@cog_hidden
class Help(VanirCog):
    @vanir_group()
    async def help(self, ctx: VanirContext):
        """Stop it, get some help"""

        # Cogs -> Modules
        embed = await self.get_cog_display_embed(ctx)
        sel = CogDisplaySelect(ctx.bot, self)

        view = VanirView(user=ctx.author).add_item(sel)

        await ctx.send(embed=embed, view=view)

    async def get_cog_display_embed(self, ctx: VanirContext) -> discord.Embed:
        embed = ctx.embed(
            title="Module Select",
        )

        cogs = get_display_cogs(self.bot)
        for c in cogs:
            embed.add_field(
                name=c.qualified_name,
                value=f"*{c.description or 'No Description'}*",
                inline=True,
            )

        return embed

    async def get_cog_info_embed(
        self, itx: discord.Interaction, cog: commands.Cog
    ) -> discord.Embed:
        embed = VanirContext.syn_embed(
            title=f"Module Info: **{cog.qualified_name}**",
            description=f"*{cog.description or 'No Description'}*",
            author=itx.user,
        )

        other_commands: list[commands.Command] = []

        for c in cog.get_commands():
            if isinstance(c, commands.Group):
                embed.add_field(
                    name=f"`{c.qualified_name}` Commands",
                    value="\n".join(
                        f"`/{sub.qualified_name}`" for sub in discover_group(c)
                    ),
                )
            else:
                other_commands.append(c)

        if other_commands:
            embed.add_field(
                name=f"...{len(other_commands)} Other Command{'s' if len(other_commands) > 1 else ''}",
                value="\n".join(f"`/{o.qualified_name}`" for o in other_commands),
            )

        return embed

    async def get_command_info_embed(
        self, itx: discord.Interaction, command: commands.Command
    ) -> discord.Embed:
        embed = VanirContext.syn_embed(
            title=f"Info: `/{command.qualified_name} {command.signature}`",
            description=f"*{command.description or command.short_doc or 'No Description'}*",
            author=itx.user,
        )

        for name, param in command.params.items():
            data = {"Required": "Yes" if param.required else "No"}
            if not param.required:
                data["Default"] = param.default
            embed.add_field(
                name=f"__`{name}`__: `{get_param_annotation(param)}`",
                value=f"*{param.description}*\n{format_dict(data)}",
                inline=False,
            )

        return embed

    async def get_command_info_select(
        self, itx: discord.Interaction, command: commands.Command
    ):
        return CogInfoSelect(self.bot, self, command.cog)


class CogDisplaySelect(discord.ui.Select):
    """Creates a select which displays all cogs in the bot"""

    def __init__(self, bot: Vanir, instance: Help):
        self.bot = bot
        self.instance = instance
        options = [
            discord.SelectOption(
                label=c.qualified_name,
                description=c.description or "No Description",
                value=c.qualified_name,
                emoji=getattr(c, "emoji", "\N{Black Question Mark Ornament}"),
            )
            for c in get_display_cogs(self.bot)
        ]
        super().__init__(options=options, placeholder="Select a Module")

    async def callback(self, itx: discord.Interaction):
        selected = self.values[0]
        cog = self.bot.get_cog(selected)

        embed = await self.instance.get_cog_info_embed(itx, cog)
        sel = CogInfoSelect(self.bot, self.instance, cog)

        view = VanirView(user=itx.user)
        view.add_item(sel)

        await InteractionResponse(itx).defer()
        await itx.message.edit(embed=embed, view=view)


class CogInfoSelect(discord.ui.Select):
    """Creates a select which displays commands in a cog"""

    def __init__(self, bot: Vanir, instance: Help, cog: commands.Cog):
        self.bot = bot
        self.instance = instance
        options = [
            discord.SelectOption(
                label=c.qualified_name,
                description=f"{c.description or 'No Description'}",
                value=c.qualified_name,
            )
            for c in discover_cog(cog)
        ]
        super().__init__(options=options, placeholder="Select a Command")

    async def callback(self, itx: discord.Interaction):
        selected = self.values[0]
        command = self.bot.get_command(selected)

        embed = await self.instance.get_command_info_embed(itx, command)
        sel = await self.instance.get_command_info_select(itx, command)

        view = VanirView(user=itx.user)
        view.user = itx.user
        view.add_item(sel)

        await InteractionResponse(itx).defer()
        await itx.message.edit(embed=embed, view=view)


async def setup(bot: Vanir):
    await bot.add_cog(Help(bot))
