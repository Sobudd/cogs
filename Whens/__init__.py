from .whens import Whens

async def setup(bot):
    await bot.add_cog(Whens(bot))