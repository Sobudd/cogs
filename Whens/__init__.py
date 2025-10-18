from .whens import whens

async def setup(bot):
    await bot.add_cog(whens(bot))