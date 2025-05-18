import asyncio
import discord
from discord.ext import commands
from discord import app_commands
from mcstatus import JavaServer

from utils import get_guild_config, run_rcon_command

TEST_GUILD = discord.Object(id=800622420536590346)

class ServerInfoCog(commands.Cog):
    """Prefix + Slash commands for Minecraft server status and RCON queries."""
    def __init__(self, bot):
        self.bot = bot

    #
    # --- PREFIX COMMANDS ---
    #

    @commands.command(
        name="mcstatus",
        help="**Usage**\n"
             "`!mcstatus`\n\n"
             "Checks if the Minecraft server is online and shows player count.\n\n"
             "**Example**\n"
             "`!mcstatus`"
    )
    async def mcstatus(self, ctx):
        cfg = ctx.bot.server_configs.get(str(ctx.guild.id), {})
        ip   = cfg.get("ip", "mc.hypixel.net")
        port = cfg.get("port", 25565)
        srv  = JavaServer(ip, port)
        try:
            st = await asyncio.get_event_loop().run_in_executor(None, srv.status)
            await ctx.send(
                f"✅ **Online!** {st.players.online}/{st.players.max} players\n"
                f"Latency: {round(st.latency)} ms"
            )
        except:
            await ctx.send("⚠️ Server appears offline or unreachable.")

    @commands.command(
        name="mcplayers",
        help="**Usage**\n"
             "`!mcplayers`\n\n"
             "Lists currently online players.\n\n"
             "**Example**\n"
             "`!mcplayers`"
    )
    async def mcplayers(self, ctx):
        cfg = ctx.bot.server_configs.get(str(ctx.guild.id), {})
        ip, port = cfg.get("ip",""), cfg.get("port",25565)
        srv = JavaServer(ip, port)
        try:
            q = await asyncio.get_event_loop().run_in_executor(None, srv.query)
            names = q.players.names
        except:
            st = await asyncio.get_event_loop().run_in_executor(None, srv.status)
            names = [p.name for p in st.players.sample] if st.players.sample else []
        if names:
            await ctx.send(f"🧑‍💻 Players online ({len(names)}/{st.players.max}): {', '.join(names)}")
        else:
            await ctx.send(f"No players online. (0/{st.players.max})")

    @commands.command(
        name="mcinfo",
        help="**Usage**\n"
             "`!mcinfo`\n\n"
             "Displays server IP, version, player count, and latency.\n\n"
             "**Example**\n"
             "`!mcinfo`"
    )
    async def mcinfo(self, ctx):
        cfg = ctx.bot.server_configs.get(str(ctx.guild.id), {})
        ip, port = cfg.get("ip",""), cfg.get("port",25565)
        srv = JavaServer(ip, port)
        try:
            st = await asyncio.get_event_loop().run_in_executor(None, srv.status)
            e = discord.Embed(title="Server Info", color=0x00ff00)
            e.add_field(name="IP",      value=f"`{ip}:{port}`", inline=False)
            e.add_field(name="Version", value=st.version.name, inline=True)
            e.add_field(name="Players", value=f"{st.players.online}/{st.players.max}", inline=True)
            e.add_field(name="Latency", value=f"{round(st.latency)} ms", inline=True)
            await ctx.send(embed=e)
        except:
            await ctx.send("⚠️ Unable to retrieve server information.")

    @commands.command(
        name="mcping",
        help="**Usage**\n"
             "`!mcping`\n\n"
             "Pings the server to measure latency.\n\n"
             "**Example**\n"
             "`!mcping`"
    )
    async def mcping(self, ctx):
        cfg = ctx.bot.server_configs.get(str(ctx.guild.id), {})
        ip, port = cfg.get("ip",""), cfg.get("port",25565)
        srv = JavaServer(ip, port)
        try:
            ping = await asyncio.get_event_loop().run_in_executor(None, srv.ping)
            await ctx.send(f"🏓 Ping: {round(ping,5)} ms")
        except:
            await ctx.send("⚠️ Failed to ping the server.")

    @commands.command(
        name="mctime",
        help="**Usage**\n"
             "`!mctime`\n\n"
             "Shows in-game time; requires RCON.\n\n"
             "**Example**\n"
             "`!mctime`"
    )
    async def mctime(self, ctx):
        cfg = get_guild_config(self.bot, str(ctx.guild.id))
        try:
            resp = await asyncio.get_event_loop().run_in_executor(
                None, run_rcon_command, "time query daytime", cfg
            )
            await ctx.send(f"🕒 In-game time: {resp}")
        except Exception as e:
            await ctx.send(f"⚠️ RCON error: {e}")

    @commands.command(
        name="mcseed",
        help="**Usage**\n"
             "`!mcseed`\n\n"
             "Returns the world seed; requires RCON.\n\n"
             "**Example**\n"
             "`!mcseed`"
    )
    async def mcseed(self, ctx):
        cfg = get_guild_config(self.bot, str(ctx.guild.id))
        try:
            resp = await asyncio.get_event_loop().run_in_executor(
                None, run_rcon_command, "seed", cfg
            )
            await ctx.send(f"🌱 World seed: {resp}")
        except Exception as e:
            await ctx.send(f"⚠️ RCON error: {e}")

    @commands.has_permissions(administrator=True)
    @commands.command(
        name="mcstop",
        help="**Usage**\n"
             "`!mcstop`\n\n"
             "Stops the server; requires RCON; admin only.\n\n"
             "**Example**\n"
             "`!mcstop`"
    )
    async def mcstop(self, ctx):
        cfg = get_guild_config(self.bot, str(ctx.guild.id))
        try:
            await asyncio.get_event_loop().run_in_executor(
                None, run_rcon_command, "stop", cfg
            )
            await ctx.send("🔌 Server stopping…")
        except Exception as e:
            await ctx.send(f"⚠️ RCON error: {e}")

    #
    # --- SLASH COMMANDS ---
    #

    @app_commands.command(
        name="mcstatus",
        description="Checks if the server is online and shows player count."
    )
    async def mcstatus_slash(self, interaction: discord.Interaction):
        cfg = self.bot.server_configs.get(str(interaction.guild_id), {})
        ip, port = cfg.get("ip",""), cfg.get("port",25565)
        srv = JavaServer(ip, port)
        try:
            st = await asyncio.get_event_loop().run_in_executor(None, srv.status)
            await interaction.response.send_message(
                f"✅ **Online!** {st.players.online}/{st.players.max} players\n"
                f"Latency: {round(st.latency)} ms"
            )
        except:
            await interaction.response.send_message("⚠️ Server appears offline or unreachable.")

    @app_commands.command(
        name="mcplayers",
        description="Lists currently online players."
    )
    async def mcplayers_slash(self, interaction: discord.Interaction):
        cfg = self.bot.server_configs.get(str(interaction.guild_id), {})
        ip, port = cfg.get("ip",""), cfg.get("port",25565)
        srv = JavaServer(ip, port)
        try:
            q = await asyncio.get_event_loop().run_in_executor(None, srv.query)
            names = q.players.names
        except:
            st = await asyncio.get_event_loop().run_in_executor(None, srv.status)
            names = [p.name for p in st.players.sample] if st.players.sample else []
        if names:
            await interaction.response.send_message(
                f"🧑‍💻 Players online ({len(names)}/{st.players.max}): {', '.join(names)}"
            )
        else:
            await interaction.response.send_message(f"No players online. (0/{st.players.max})")

    @app_commands.command(
        name="mcinfo",
        description="Displays server IP, version, player count, and latency."
    )
    async def mcinfo_slash(self, interaction: discord.Interaction):
        cfg = self.bot.server_configs.get(str(interaction.guild_id), {})
        ip, port = cfg.get("ip",""), cfg.get("port",25565)
        srv = JavaServer(ip, port)
        try:
            st = await asyncio.get_event_loop().run_in_executor(None, srv.status)
            e = discord.Embed(title="Server Info", color=0x00ff00)
            e.add_field(name="IP",      value=f"`{ip}:{port}`", inline=False)
            e.add_field(name="Version", value=st.version.name, inline=True)
            e.add_field(name="Players", value=f"{st.players.online}/{st.players.max}", inline=True)
            e.add_field(name="Latency", value=f"{round(st.latency)} ms", inline=True)
            await interaction.response.send_message(embed=e)
        except:
            await interaction.response.send_message("⚠️ Unable to retrieve server information.")

    @app_commands.command(
        name="mcping",
        description="Pings the server to measure latency."
    )
    async def mcping_slash(self, interaction: discord.Interaction):
        cfg = self.bot.server_configs.get(str(interaction.guild_id), {})
        ip, port = cfg.get("ip",""), cfg.get("port",25565)
        srv = JavaServer(ip, port)
        try:
            ping = await asyncio.get_event_loop().run_in_executor(None, srv.ping)
            await interaction.response.send_message(f"🏓 Ping: {round(ping,5)} ms")
        except:
            await interaction.response.send_message("⚠️ Failed to ping the server.")

    @app_commands.command(
        name="mctime",
        description="Shows in-game time; requires RCON."
    )
    async def mctime_slash(self, interaction: discord.Interaction):
        cfg = get_guild_config(self.bot, str(interaction.guild_id))
        try:
            resp = await asyncio.get_event_loop().run_in_executor(
                None, run_rcon_command, "time query daytime", cfg
            )
            await interaction.response.send_message(f"🕒 In-game time: {resp}")
        except Exception as e:
            await interaction.response.send_message(f"⚠️ RCON error: {e}")

    @app_commands.command(
        name="mcseed",
        description="Returns the world seed; requires RCON."
    )
    async def mcseed_slash(self, interaction: discord.Interaction):
        cfg = get_guild_config(self.bot, str(interaction.guild_id))
        try:
            resp = await asyncio.get_event_loop().run_in_executor(
                None, run_rcon_command, "seed", cfg
            )
            await interaction.response.send_message(f"🌱 World seed: {resp}")
        except Exception as e:
            await interaction.response.send_message(f"⚠️ RCON error: {e}")

    @app_commands.command(
        name="mcstop",
        description="Stops the server; requires RCON; admin only."
    )
    @app_commands.checks.has_permissions(administrator=True)
    async def mcstop_slash(self, interaction: discord.Interaction):
        cfg = get_guild_config(self.bot, str(interaction.guild_id))
        try:
            await asyncio.get_event_loop().run_in_executor(
                None, run_rcon_command, "stop", cfg
            )
            await interaction.response.send_message("🔌 Server stopping…")
        except Exception as e:
            await interaction.response.send_message(f"⚠️ RCON error: {e}")

async def setup(bot: commands.Bot):
    await bot.add_cog(ServerInfoCog(bot), guild=TEST_GUILD)
