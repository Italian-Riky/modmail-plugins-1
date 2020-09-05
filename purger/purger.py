"""
Purger plugin per ModMail.

Scritto da Papiersnipper(Tradotto da Italian Riky:https://github.com/Italian-Riky ).
Tutti i diritti riservati.
"""

import asyncio

from discord import Forbidden, Message
from discord.ext.commands import Bot, Cog, Context, command

from core.checks import has_permissions
from core.models import PermissionLevel


class Purger(Cog):
    """Elimina piu messaggi nello stesso tempo!(Plugin tradotto da [Italian Riky](https://github.com/Italian-Riky)).
    Piu informazioni: [Clicca qua!](https://github.com/papiersnipper/modmail-plugins/tree/master/purger)
    """

    def __init__(self, bot: Bot) -> None:
        self.bot = bot

    @command()
    @has_permissions(PermissionLevel.MODERATOR)
    async def purge(self, ctx: Context, amount: int) -> None:
        """Elimina il numero specificato di messaggi."""
        if amount < 1:
            return

        try:
            deleted = await ctx.channel.purge(limit=amount + 1)
        except Forbidden:
            return await ctx.send("Non ho il permesso di eliminare i messaggi qua.")

        delete_message: Message = await ctx.send(f"Eliminati con successo {len(deleted)} Messaggi!")
        await asyncio.sleep(3)
        await delete_message.delete()


def setup(bot: Bot) -> None:
    """Bot cog load."""
    bot.add_cog(Purger(bot))
