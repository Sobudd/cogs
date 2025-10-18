import discord
from redbot.core import commands
from datetime import datetime, timedelta, timezone
import asyncio


def unix_now() -> int:
    """Return current UTC time as a UNIX timestamp (seconds)."""
    return int(datetime.now(timezone.utc).timestamp())


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
        expires = datetime.now(timezone.utc) + timedelta(hours=1)
        expiry_unix = int(expires.timestamp())

        # build embed description with expiry line
        desc = (
            "Please check in for gaming!\n"
            "React to this message to consent to gaming!\n\n"
            f"Slots available: {slots}\n\n"
            + "\n".join([f"{i+1}. [empty]" for i in range(slots)])
            + f"\n\n⏰ Session expires <t:{expiry_unix}:R>\n"
            "❌ Session creator can cancel with the ❌ reaction."
        )

        embed = discord.Embed(
            title="🎮 whens has been called!!",
            description=desc,
            color=discord.Color.green()
        )

        msg = await ctx.send(embed=embed)
        await msg.add_reaction("✅")
        await msg.add_reaction("❌")

        # store session info
        self.active_sessions[msg.id] = {
            "slots": slots,
            "participants": [],
            "expires": expires,
            "channel": ctx.channel.id,
            "owner": ctx.author.id
        }

        # schedule expiry task
        self.bot.loop.create_task(self._expire_session(msg.id))

    @commands.Cog.listener()
    async def on_reaction_add(self, reaction, user):
        """Handle ✅ reactions to join and ❌ to cancel."""
        if user.bot:
            return

        msg = reaction.message
        if msg.id not in self.active_sessions:
            return

        session = self.active_sessions[msg.id]

        # ✅ join logic
        if str(reaction.emoji) == "✅":
            if user in session["participants"]:
                return
            if len(session["participants"]) >= session["slots"]:
                return

            session["participants"].append(user)

            ts = unix_now()
            filled = [
                f"{i+1}. {p.display_name} (<t:{ts}:R>)"
                for i, p in enumerate(session["participants"])
            ]
            empty = [f"{i+1}. [empty]" for i in range(len(session["participants"]), session["slots"])]

            expiry_unix = int(session["expires"].timestamp())

            desc = (
                "Please check in for gaming!\n"
                "React to this message to consent to gaming!\n\n"
                f"Slots available: {session['slots']}\n\n"
                + "\n".join(filled + empty)
                + f"\n\n⏰ Session expires <t:{expiry_unix}:R>\n"
                "❌ Session creator can cancel with the ❌ reaction."
            )

            embed = discord.Embed(
                title="🎮 whens has been called!!",
                description=desc,
                color=discord.Color.green()
            )

            await msg.edit(embed=embed)

        # ❌ cancel logic
        elif str(reaction.emoji) == "❌":
            if user.id != session["owner"]:
                return  # only creator can cancel

            channel = self.bot.get_channel(session["channel"])
            if channel:
                try:
                    original = await channel.fetch_message(msg.id)
                    if original.embeds:
                        embed = original.embeds[0].copy()
                        embed.color = discord.Color.red()
                        embed.title = "❌ Session Cancelled"
                        embed.description += f"\n\n⚠️ Cancelled by {user.display_name}."
                        await original.edit(embed=embed)
                except Exception:
                    pass
                await channel.send("❌ Session cancelled by the creator.")
            self.active_sessions.pop(msg.id, None)

    async def _expire_session(self, message_id: int):
        """Wait until expiry, then clean up if session still active."""
        session = self.active_sessions.get(message_id)
        if not session:
            return

        now = datetime.now(timezone.utc)
        delay = (session["expires"] - now).total_seconds()
        if delay > 0:
            await asyncio.sleep(delay)

        session = self.active_sessions.get(message_id)
        if session:
            channel = self.bot.get_channel(session["channel"])
            if channel:
                try:
                    original = await channel.fetch_message(message_id)
                    if original.embeds:
                        embed = original.embeds[0].copy()
                        embed.color = discord.Color.red()
                        embed.title = "⏰ Session Expired"
                        embed.description += "\n\n⚠️ This session has expired."
                        await original.edit(embed=embed)
                except Exception:
                    pass
                await channel.send("⏰ Session expired — not enough players checked in.")
            self.active_sessions.pop(message_id, None)


async def setup(bot):
    await bot.add_cog(Whens(bot))