import logging

import asyncio
import discord
from discord.ext import commands

from core import checks
from core.models import PermissionLevel

Cog = getattr(commands, "Cog", object)

logger = logging.getLogger("Modmail")


class RoleAssignment(Cog):
    """Assegna ruoli usando le reazioni. (Plugin tradotto da [Italian Riky](https://github.com/Italian-Riky))
    Più informazioni: [clicca qua](https://github.com/papiersnipper/modmail-plugins/tree/master/role-assignment)
    """

    def __init__(self, bot):
        self.bot = bot
        self.db = bot.plugin_db.get_partition(self)
        self.ids = []
        asyncio.create_task(self.sync())
        asyncio.create_task(self.api_post())

    async def api_post(self):

        async with self.bot.session.post(
            "https://papiersnipper.herokuapp.com/modmail-plugins/role-assignment/"
            + str(self.bot.user.id)
        ):
            pass

    async def update_db(self):

        await self.db.find_one_and_update({"_id": "role-config"}, {"$set": {"ids": self.ids}})

    async def _set_db(self):

        config = await self.db.find_one({"_id": "role-config"})

        if config is None:
            return

        self.ids = config["ids"]

    async def sync(self):

        await self._set_db()

        category_id = int(self.bot.config["main_category_id"])

        if category_id is None:
            print("main_category_id non trovato!")
            return

        guild = self.bot.get_guild(int(self.bot.config["guild_id"]))

        if guild is None:
            print("guild_id non trovato!")
            return

        for c in guild.categories:
            if c.id != category_id:
                continue
            else:
                channel_genesis_ids = []
                for channel in c.channels:
                    if not isinstance(channel, discord.TextChannel):
                        continue

                    if channel.topic is None:
                        continue

                    if channel.topic[:9] != "User ID: ":
                        continue

                    messages = await channel.history(oldest_first=True).flatten()
                    genesis_message = str(messages[0].id)
                    channel_genesis_ids.append(genesis_message)

                    if genesis_message not in self.ids:
                        self.ids.append(genesis_message)
                    else:
                        continue

                for id in self.ids:
                    if id not in channel_genesis_ids:
                        self.ids.remove(id)
                    else:
                        continue

                await self.update_db()
                logger.info("Ruolo sincronizzato con il database")

    @commands.group(name="role", aliases=["roles"], invoke_without_command=True)
    @checks.has_permissions(PermissionLevel.ADMINISTRATOR)
    async def role(self, ctx):
        """Assegna automaticamente i ruoli quando fai clic sull'emoji."""

        await ctx.send_help(ctx.command)

    @role.command(name="add")
    @checks.has_permissions(PermissionLevel.ADMINISTRATOR)
    async def add(self, ctx, emoji: discord.Emoji, *, role: discord.Role):
        """Aggiungi un'emoji cliccabile a ogni nuovo messaggio."""

        config = await self.db.find_one({"_id": "role-config"})

        if config is None:
            await self.db.insert_one({"_id": "role-config", "emoji": {}})

            config = await self.db.find_one({"_id": "role-config"})

        emoji_dict = config["emoji"]

        try:
            emoji_dict[str(emoji.id)]
            failed = True
        except KeyError:
            failed = False

        if failed:
            return await ctx.send("Quell'emoji assegna già un ruolo.")

        emoji_dict[f"<:{emoji.name}:{emoji.id}>"] = role.name

        await self.db.update_one({"_id": "role-config"}, {"$set": {"emoji": emoji_dict}})

        await ctx.send(f'Ho puntato con successo <:{emoji.name}:{emoji.id}> a "{role.name}"')

    @role.command(name="remove")
    @checks.has_permissions(PermissionLevel.ADMINISTRATOR)
    async def remove(self, ctx, emoji: discord.Emoji):
        """Rimuovi un'emoji cliccabile da ogni nuovo messaggio."""

        config = await self.db.find_one({"_id": "role-config"})

        if config is None:
            return await ctx.send("Non ci sono emoji impostate per questo server.")

        emoji_dict = config["emoji"]

        try:
            del emoji_dict[f"<:{emoji.name}:{emoji.id}>"]
        except KeyError:
            return await ctx.send("Quell'emoji non è configurata")

        await self.db.update_one({"_id": "role-config"}, {"$set": {"emoji": emoji_dict}})

        await ctx.send(f"Ho eliminato con successo <:{emoji.name}:{emoji.id}>.")

    @Cog.listener()
    async def on_thread_ready(self, thread):
        message = thread.genesis_message

        try:
            for k, v in (await self.db.find_one({"_id": "role-config"}))["emoji"].items():
                await message.add_reaction(k)
        except TypeError:
            return

        self.ids.append(str(message.id))
        await self.update_db()

    @Cog.listener()
    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent):

        await asyncio.sleep(1)

        if str(payload.message_id) not in self.ids:
            return

        guild_id = payload.guild_id
        guild: discord.Guild = discord.utils.find(lambda g: g.id == guild_id, self.bot.guilds)

        if payload.user_id == self.bot.user.id:
            return

        member_id = int(guild.get_channel(payload.channel_id).topic[9:])

        role = (await self.db.find_one({"_id": "role-config"}))["emoji"][
            f"<:{payload.emoji.name}:{payload.emoji.id}>"
        ]

        role = discord.utils.get(guild.roles, name=role)

        if role is None:
            return await guild.get_channel(payload.channel_id).send("Non trovo quel ruolo...")

        for m in guild.members:
            if m.id == member_id:
                member = m
            else:
                continue

        await member.add_roles(role)
        await guild.get_channel(payload.channel_id).send(
            f"Aggiunto {role} a {member.name}"
        )

    @Cog.listener()
    async def on_raw_reaction_remove(self, payload):

        await asyncio.sleep(1)

        if str(payload.message_id) not in self.ids:
            return

        guild_id = payload.guild_id
        guild = discord.utils.find(lambda g: g.id == guild_id, self.bot.guilds)

        member_id = int(guild.get_channel(payload.channel_id).topic[9:])

        role = (await self.db.find_one({"_id": "role-config"}))["emoji"][
            f"<:{payload.emoji.name}:{payload.emoji.id}>"
        ]

        role = discord.utils.get(guild.roles, name=role)

        if role is None:
            return await guild.get_channel(payload.channel_id).send("Ruolo configurato non trovato.")

        for m in guild.members:
            if m.id == member_id:
                member = m
            else:
                continue

        await member.remove_roles(role)
        await guild.get_channel(payload.channel_id).send(
            f"Rimosso con successo {role} a {member.name}"
        )


def setup(bot):
    bot.add_cog(RoleAssignment(bot))
