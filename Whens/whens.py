import discord
from redbot.core import commands
from datetime import datetime, timedelta

class Whens(commands.Cog):
    """Organize quick gaming sessions with a ready-check system."""

    def __init__(self, bot):
        self.bot = bot
        self.active_sessions = {}  # message_id -> session data

    @commands.command(name="whens")
    async def whens_command(self, ctx, slots: int):
        """Start a Whens session with a given number of slots."""
        if slots < 1:
            return await ctx.send("Slots must be at least 1.")

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

        # Store session info
        self.active_sessions[msg.id] = {
            "slots": slots,
            "participants": [],
            "expires": datetime.utcnow() + timedelta(hours=1),
            "channel": ctx.channel.id
        }

    @commands.Cog.listener()
    async def on_reaction_add(self, reaction, user):
        if user.bot:
            return

        msg = reaction.message
        if msg.id not in self.active_sessions:
            return
        if str(reaction.emoji) != "✅":
            return

        session = self.active_sessions[msg.id]
        if user.id in [u.id for u in session["participants"]]:
            return  # already joined

        if len(session["participants"]) >= session["slots"]:
            return  # session full

        # Add participant
        session["participants"].append(user)

        # Update embed
        embed = msg.embeds[0]
        filled = [
            f"{i+1}. {p.display_name} (<t:{int(datetime.utcnow().timestamp())}:R>)"
            for i, p in enumerate(session["participants"])
        ]
        empty = [f"{i+1}. [empty]" for i in range(len(session["participants"]), session["slots"])]
        embed.description = (
            "Please check in for gaming!\n"
            "React to this message to consent to gaming!\n\n"
            f"Slots available: {session['slots']}\n\n"
            + "\n".join(filled + empty)
        )
        await msg.edit(embed=embed)

        # If session is full, announce
        if len(session["participants"]) == session["slots"]:
            mentions = " ".join([p.mention for p in session["participants"]])
            await msg.channel.send(f"🔥 GAMING NOW COMMENCING 🔥\n{mentions}")
            del self.active_sessions[msg.id]