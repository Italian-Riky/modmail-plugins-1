"""
Supporters plugin per Modmail.

Scritto da Papiersnipper, Tradotto da Italian-Riky.
Tutti i dirriti riservati.
"""

from discord import Embed
from discord.ext.commands import Bot, Cog, Context, command

from core.checks import has_permissions
from core.models import PermissionLevel


class Supporters(Cog):
    """Controlla chi sono le persone che aiutano.
    Piu informazioni(inglese): [click here](https://github.com/papiersnipper/modmail-plugins/tree/master/supporters)
    """

    def __init__(self, bot: Bot) -> None:
        self.bot = bot

    @command(aliases=["helpers", "supporters", "supportmembers"])
    @has_permissions(PermissionLevel.REGULAR)
    async def support(self, ctx: Context) -> None:
        """Invia un'embed con le persone che aiutano."""

        category_id = self.bot.config.get("main_category_id")

        if category_id is None:
            embed = Embed(
                title="Aiutanti",
                url="https://github.com/papiersnipper/modmail-plugins/blob/master/supporters",
                description=f"Non riesco a trovare la categoria del modmail.\nAssicurati di aver usato il comando `?config set main_category_id`.",
                color=self.bot.main_color,
            )

            return await ctx.send(embed=embed)

        categories = self.bot.modmail_guild.categories

        for category in categories:
            if category.id != int(category_id):
                continue

            member_list = []
            for member in self.bot.modmail_guild.members:
                if member.permissions_in(category).read_messages:
                    if not member.bot:
                        member_list.append(member.mention)

        embed = Embed(
            title="Membri Aiutanti",
            url="https://github.com/papiersnipper/modmail-plugins/blob/master/supporters",
            colour=self.bot.main_color,
            description=", ".join(member_list),
        )

        await ctx.send(embed=embed)


def setup(bot: Bot) -> None:
    """Bot cog load."""
    bot.add_cog(Supporters(bot))
