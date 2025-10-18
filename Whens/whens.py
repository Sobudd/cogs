import discord
from discord.ext import commands
from datetime import datetime, timedelta
import asyncio


class Whens(commands.Cog):
    """A cog to call gaming sessions and track participants."""

    def __init__(self, bot):
        self.bot = bot
        # active_sessions maps message_id -> session data
        self.active_sessions = {}

    @commands.command(name="whens")
    async def whens_command(self, ctx, slots: int):
        """Start a whens session with a given number of slots."""
        if slots < 1:
            return await ctx.send("Slots must be at least 1.")

        # calculate expiry time and unix timestamp
        expires = datetime.utcnow() + timedelta(hours=1)
        expiry_unix = int(expires.timestamp())

        # build embed
        embed = discord.Embed(
            title="🎮 whens has been called!!",
            description=(
                "Please check in for gaming!\n"
                "React to this message to consent to gaming!\n\n"
                f"Slots available: {slots}\n\n"
                + "\n".join([f"{i+1}. [empty]" for i in range(slots)])
            ),
            color=discord.Color.green()
        )
        embed.set_footer(text=f"Session expires <t:{expiry_unix}:R>")

        msg = await ctx.send(embed=embed)
        await msg.add_reaction("✅")

        # store session info
        self.active_sessions[msg.id] = {
            "slots": slots,
            "participants": [],
            "expires": expires,
            "channel": ctx.channel.id
        }

        # schedule expiry task
        self.bot.loop.create_task(self._expire_session(msg.id))

    @commands.Cog.listener()
    async def on_reaction_add(self, reaction, user):
        """Handle ✅ reactions to join a session."""
        if user.bot:
            return

        msg = reaction.message
        if msg.id not in self.active_sessions:
            return
        if str(reaction.emoji) != "✅":
            return

        session = self.active_sessions[msg.id]
        if user in session["participants"]:
            return
        if len(session["participants"]) >= session["slots"]:
            return

        session["participants"].append(user)

        # rebuild embed with updated participants
        timestamp = int(datetime.utcnow().timestamp())
        filled = [
            f"{i+1}. {p.display_name} (<t:{timestamp}:R>)"
            for i, p in enumerate(session["participants"])
        ]
        empty = [f"{i+1}. [empty]" for i in range(len(session["participants"]), session["slots"])]

        embed = discord.Embed(
            title="🎮 whens has been called!!",
            description=(
                "Please check in for gaming!\n"
                "React to this message to consent to gaming!\n\n"
                f"Slots available: {session['slots']}\n\n"
                + "\n".join(filled + empty)
            ),
            color=discord.Color.green()
        )
        expiry_unix = int(session["expires"].timestamp())
        embed.set_footer(text=f"Session expires <t:{expiry_unix}:R>")

        await msg.edit(embed=embed)

    async def _expire_session(self, message_id: int):
        """Wait until expiry, then clean up if session still active."""
        session = self.active_sessions.get(message_id)
        if not session:
            return

        now = datetime.utcnow()
        delay = (session["expires"] - now).total_seconds()
        if delay > 0:
            await asyncio.sleep(delay)

        # after waiting, check if still active
        session = self.active_sessions.get(message_id)
        if session:
            channel = self.bot.get_channel(session["channel"])
            if channel:
                await channel.send("⏰ Session expired — not enough players checked in.")
            self.active_sessions.pop(message_id, None)


async def setup(bot):
    await bot.add_cog(Whens(bot))