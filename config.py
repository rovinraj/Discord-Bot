# config.py

import discord
from discord.ext import commands
from discord import app_commands
from utils import save_json, SERVER_CFG_PATH

class ConfigCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    #
    # PREFIX COMMANDS
    #

    @commands.has_permissions(administrator=True)
    @commands.command(
        name="config",
        help="**Usage**\n"
             "`!config <ip> [port] [password]` or `!config ip=<ip> port=<port> pw=<password>`\n\n"
             "Sets server IP/port/RCON password for this server; admin only.\n\n"
             "**Example**\n"
             "`!config mc.example.net 25565 secret`"
    )
    async def config(self, ctx, *args):
        cfgs = ctx.bot.server_configs
        guild_id = str(ctx.guild.id)
        raw = cfgs.setdefault(guild_id, {})

        ip = port = pw = None
        pos = []
        for a in args:
            if "=" in a:
                k, v = a.split("=", 1)
                key = k.lower()
                if key in ("ip", "host"):
                    ip = v
                elif key == "port":
                    try:
                        port = int(v)
                    except:
                        return await ctx.send("❌ `port` must be a number.")
                elif key in ("pw", "password", "rcon"):
                    pw = v
                else:
                    return await ctx.send(f"❌ Unknown parameter `{k}`.")
            else:
                pos.append(a)

        # positional fallback
        if pos:
            if ip is None:
                ip = pos[0]
            if len(pos) > 1 and port is None:
                try:
                    port = int(pos[1])
                except:
                    return await ctx.send("❌ `port` must be a number.")
            if len(pos) > 2 and pw is None:
                pw = pos[2]
            if len(pos) > 3:
                return await ctx.send("❌ Too many arguments.")

        if not ip:
            return await ctx.send("❌ You must specify at least an IP.")

        raw["ip"] = ip
        updates = [f"ip={ip}"]
        if port is not None:
            raw["port"] = port
            updates.append(f"port={port}")
        if pw is not None:
            raw["password"] = pw
            updates.append("password=******")

        save_json(SERVER_CFG_PATH, cfgs)
        await ctx.send("✅ Config updated: " + ", ".join(updates))


    @commands.has_permissions(administrator=True)
    @commands.command(
        name="setserverinfo",
        help="Alias for `!config`, admin only."
    )
    async def setserverinfo(self, ctx, *args):
        # simply delegate to the same logic
        await self.config.callback(self, ctx, *args)


    @commands.has_permissions(administrator=True)
    @commands.command(
        name="prefix",
        help="**Usage**\n"
             "`!prefix <new_prefix>`\n\n"
             "Changes the bot’s command prefix for this server.\n\n"
             "**Example**\n"
             "`!prefix $`"
    )
    async def prefix(self, ctx, new_prefix: str):
        cfgs = ctx.bot.server_configs
        raw = cfgs.setdefault(str(ctx.guild.id), {})
        raw["prefix"] = new_prefix
        save_json(SERVER_CFG_PATH, cfgs)
        await ctx.send(f"✅ Prefix set to `{new_prefix}`")


    #
    # SLASH COMMANDS
    #

    @app_commands.command(
        name="config",
        description="Sets server IP, port, and RCON password for this server; admin only."
    )
    @app_commands.describe(
        ip="Minecraft server IP or hostname",
        port="Minecraft server port (default 25565)",
        password="RCON password (optional)"
    )
    @app_commands.checks.has_permissions(administrator=True)
    async def config_slash(
        self,
        interaction: discord.Interaction,
        ip: str,
        port: int = 25565,
        password: str = None
    ):
        guild_id = str(interaction.guild_id)
        cfgs = self.bot.server_configs
        raw = cfgs.setdefault(guild_id, {})

        raw["ip"] = ip
        updates = [f"ip={ip}"]

        if port != 25565:
            raw["port"] = port
            updates.append(f"port={port}")
        if password is not None:
            raw["password"] = password
            updates.append("password=******")

        save_json(SERVER_CFG_PATH, cfgs)
        await interaction.response.send_message(
            content="✅ Config updated: " + ", ".join(updates),
            ephemeral=True
        )

    @app_commands.command(
        name="setserverinfo",
        description="Alias for `/config`; admin only."
    )
    @app_commands.describe(
        ip="Minecraft server IP or hostname",
        port="Minecraft server port (default 25565)",
        password="RCON password (optional)"
    )
    @app_commands.checks.has_permissions(administrator=True)
    async def setserverinfo_slash(
        self,
        interaction: discord.Interaction,
        ip: str,
        port: int = 25565,
        password: str = None
    ):
        # just call config_slash under the hood
        await self.config_slash.callback(
            self, interaction, ip=ip, port=port, password=password
        )

    @app_commands.command(
        name="prefix",
        description="Changes the bot’s command prefix for this server; admin only."
    )
    @app_commands.describe(
        new_prefix="The new command prefix (e.g. !, $, etc.)"
    )
    @app_commands.checks.has_permissions(administrator=True)
    async def prefix_slash(
        self,
        interaction: discord.Interaction,
        new_prefix: str
    ):
        guild_id = str(interaction.guild_id)
        cfgs = self.bot.server_configs
        raw = cfgs.setdefault(guild_id, {})
        raw["prefix"] = new_prefix
        save_json(SERVER_CFG_PATH, cfgs)
        await interaction.response.send_message(
            content=f"✅ Prefix set to `{new_prefix}`",
            ephemeral=True
        )


async def setup(bot: commands.Bot):
    await bot.add_cog(ConfigCog(bot))
