import os
import atexit
import discord
from discord.ext import commands
from dotenv import load_dotenv
from utils        import load_json, save_json, get_prefix, SERVER_CFG_PATH, WAYPOINTS_PATH
from help_command import MyHelp, HelpCog

import config
import server_info
import stats
import waypoints

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

class MyBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(
            command_prefix=get_prefix,
            intents=intents,
            help_command=MyHelp()
        )
        self.server_configs = load_json(SERVER_CFG_PATH)
        self.all_waypoints  = load_json(WAYPOINTS_PATH)

    async def setup_hook(self):
        for module in (config, server_info, stats):
            for attr in dir(module):
                cmd = getattr(module, attr)
                if isinstance(cmd, commands.Command):
                    self.add_command(cmd)

        await self.add_cog(waypoints.WaypointCog(self))
        await self.add_cog(HelpCog(self))
        await self.add_cog(config.ConfigCog(self))
        await self.add_cog(server_info.ServerInfoCog(self))
        await self.add_cog(stats.StatsCog(self))
        
        await self.tree.sync()
        TEST_GUILD = discord.Object(id=800622420536590346)
        await self.tree.sync(guild=TEST_GUILD)

    async def on_ready(self):
        print(f"Logged in as {self.user} (ID: {self.user.id})")

bot = MyBot()

atexit.register(lambda: (
    save_json(SERVER_CFG_PATH, bot.server_configs),
    save_json(WAYPOINTS_PATH,   bot.all_waypoints)
))

bot.run(TOKEN)
