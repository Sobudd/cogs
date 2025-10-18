from redbot.core import commands

class Whens(commands.Cog):
    """A cog for tracking 'when' events."""

    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def whens(self, ctx):
        """Example command for Whens cog."""
        await ctx.send("This is the Whens cog in action!")