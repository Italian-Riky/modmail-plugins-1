"""
Autorole plugin per Modmail.

Scritto da Papiersnipper(tradotto da Italian-Riky).
Tutti i diritti riservati.
"""

import asyncio
import logging

from discord import Embed, Guild, Member, Role
from discord.ext.commands import Bot, Cog, Context, Greedy, group
from discord.utils import get
from motor.motor_asyncio import AsyncIOMotorCollection

from core.checks import has_permissions
from core.models import PermissionLevel


logger = logging.getLogger("Modmail")


class Autorole(Cog):
    """
    Assegna Ruoli automaticamente appena un membro entra nel server! (Plugin tradotto da [Italian Riky](https://github.com/Italian-Riky)).
    More info: [Clicca qua](https://github.com/papiersnipper/modmail-plugins/tree/master/autorole)
    """

    def __init__(self, bot: Bot) -> None:
        self.bot = bot
        self.db: AsyncIOMotorCollection = bot.plugin_db.get_partition(self)
        asyncio.create_task(self.migrate())

    async def migrate(self) -> None:
        """Migra il modello di database per contenere un elenco di ID ruolo invece del campo `` nome ruolo ``."""
        config = await self.db.find_one({"_id": "autorole-config"})

        if config is None:
            return

        try:
            rolename = config["rolename"]
        except KeyError:
            return

        guild: Guild = get(self.bot.guilds, id=int(self.bot.config["guild_id"]))

        if guild is None:
            return await self.db.delete_one({"_id": "autorole-config"})

        role: Role = get(guild.roles, name=rolename)

        roles = []
        roles.append(role.id)

        await self.db.replace_one({"_id": "autorole-config"}, {"roles": roles})

    @Cog.listener()
    async def on_member_join(self, member: Member) -> None:
        """Assegna al membro iscritto tutti i ruoli attualmente impostati."""
        config = await self.db.find_one({"_id": "autorole-config"})

        if config is None:
            return logger.warning("Il membro si è unito mentre nessun ruolo era stato impostato!")

        try:
            role_ids = config["roles"]
        except KeyError:
            return logger.error("Qualcosa è andato storto nel tuo database!")

        if not role_ids:
            return

        roles = []
        for role_id in role_ids:
            role: Role = get(member.guild.roles, id=role_id)

            if role is not None:
                roles.append(role)

        await member.add_roles(*roles)

    @group(name="autorole", invoke_without_command=True)
    @has_permissions(PermissionLevel.ADMINISTRATOR)
    async def autorole(self, ctx: Context) -> None:
        """Assegna automaticamente un ruolo a un utente quando si unisce al tuo server."""
        await ctx.send_help(ctx.command)

    @autorole.command(name="set")
    @has_permissions(PermissionLevel.ADMINISTRATOR)
    async def autorole_set(self, ctx: Context, roles: Greedy[Role]) -> None:
        """Imposta i ruoli predefiniti che un membro ottiene quando si unisce."""
        if not roles:
            return await ctx.send_help(ctx.command)

        config = await self.db.find_one({"_id": "autorole-config"})

        if config is None:
            await self.db.insert_one({"_id": "autorole-config"})
            logger.info("Creato file di configurazione autorole.")

        role_ids = [r.id for r in roles]
        role_mentions = [r.mention for r in roles]

        await self.db.find_one_and_update(
            {"_id": "autorole-config"}, {"$set": {"roles": role_ids}}
        )

        embed = Embed(
            title="Autorole",
            url="https://github.com/Italian-Riky/modmail-plugins-1/blob/master/autorole",
            description=f"{', '.join(role_mentions)} will now be given to all new members.",
            color=self.bot.main_color,
        )

        await ctx.send(embed=embed)

    @autorole.command(name="give")
    @has_permissions(PermissionLevel.ADMINISTRATOR)
    async def autorole_give(self, ctx: Context, role: Role) -> None:
        """Give this role to all members of your server."""
        users = 0
        for member in ctx.guild.members:
            if role.id in [role.id for role in member.roles]:
                continue
            else:
                await member.add_roles(role)
                users = users + 1

        embed = Embed(
            title="Autorole",
            url="https://github.com/Italian-Riky/modmail-plugins-1/blob/master/autorole",
            description=f"Added {role.mention} for {users} members.",
            colour=self.bot.main_color,
        )

        await ctx.send(embed=embed)

    @autorole.command(name="clear", aliases=["reset"])
    @has_permissions(PermissionLevel.ADMINISTRATOR)
    async def autorole_clear(self, ctx: Context) -> None:
        """Clear the default role(s)."""
        embed = Embed(
            title="Autorole",
            url="https://github.com/Italian-Riky/modmail-plugins-1/blob/master/autorole",
            description=f"Cleared role(s).",
            color=self.bot.main_color,
        )

        config = await self.db.find_one({"_id": "autorole-config"})

        if config is None:
            return await ctx.send(embed=embed)

        await self.db.find_one_and_update({"_id": "autorole-config"}, {"$set": {"roles": []}})

        await ctx.send(embed=embed)


def setup(bot: Bot) -> None:
    """Bot cog load."""
    bot.add_cog(Autorole(bot))
