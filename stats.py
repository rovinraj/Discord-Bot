# stats.py

import asyncio
import re
import discord
from discord import app_commands
from discord.ext import commands

from utils import get_guild_config, run_rcon_command, save_json, WAYPOINTS_PATH

class StatsCog(commands.Cog):
    """Prefix & Slash commands for scoreboard objectives & stats (RCON)."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    #
    # PREFIX COMMANDS
    #

    @commands.command(
        name="mcobjs",
        help="**Usage**\n"
             "`!mcobjs`\n\n"
             "Lists all scoreboard objectives; *requires RCON.*\n\n"
             "**Example**\n"
             "`!mcobjs`"
    )
    async def mcobjs(self, ctx: commands.Context):
        cfg = get_guild_config(self.bot, str(ctx.guild.id))
        try:
            raw = await asyncio.get_event_loop().run_in_executor(
                None, run_rcon_command, "scoreboard objectives list", cfg
            )
            objs = raw.split(":", 1)[1].split(",") if ":" in raw else []
            names = [o.strip().split(" ", 1)[0] for o in objs]
            await ctx.send(
                f"🗒️ Objectives: {', '.join(names)}"
                if names else "ℹ️ No objectives found."
            )
        except Exception as e:
            await ctx.send(f"⚠️ Error: {e}")

    @commands.command(
        name="mcstat",
        help="**Usage**\n"
             "`!mcstat <player> <objective>`\n\n"
             "Fetches a player’s score for the specified objective; *requires RCON.*\n\n"
             "**Example**\n"
             "`!mcstat Steve deaths`"
    )
    async def mcstat(self, ctx: commands.Context, player: str = None, objective: str = None):
        if not player or not objective:
            return await ctx.send("❌ Usage: `!mcstat <player> <objective>`")
        cfg = get_guild_config(self.bot, str(ctx.guild.id))
        try:
            raw = await asyncio.get_event_loop().run_in_executor(
                None, run_rcon_command,
                f"scoreboard players get {player} {objective}", cfg
            )
            m = re.search(r"(-?\d+)", raw)
            score = m.group(1) if m else "0"
            await ctx.send(f"📊 `{player}` has `{score}` on `{objective}`.")
        except Exception as e:
            await ctx.send(f"⚠️ Error: {e}")

    @commands.command(
        name="mcleaderboard",
        help="**Usage**\n"
             "`!mcleaderboard <objective> [count]`\n\n"
             "Shows top players for the specified objective; *requires RCON.*\n\n"
             "**Example**\n"
             "`!mcleaderboard deaths 10`"
    )
    async def mcleaderboard(self, ctx: commands.Context, objective: str = None, count: int = 5):
        if not objective:
            return await ctx.send("❌ Usage: `!mcleaderboard <objective> [count]`")
        cfg = get_guild_config(self.bot, str(ctx.guild.id))
        try:
            raw = await asyncio.get_event_loop().run_in_executor(
                None, run_rcon_command,
                f"scoreboard players list {objective}", cfg
            )
            parts = raw.split(":", 1)[1].split(",") if ":" in raw else []
            entries = []
            for part in parts:
                part = part.strip()
                m = re.match(r"(\S+) has (-?\d+)", part)
                if m:
                    entries.append((m.group(1), int(m.group(2))))
            if not entries:
                return await ctx.send(f"ℹ️ No scores for `{objective}`.")
            entries.sort(key=lambda x: x[1], reverse=True)

            embed = discord.Embed(
                title=f"🏆 Leaderboard: {objective}",
                color=0x00ff00
            )
            for i, (name, score) in enumerate(entries[:count], start=1):
                embed.add_field(name=f"{i}. {name}", value=str(score), inline=False)
            await ctx.send(embed=embed)
        except Exception as e:
            await ctx.send(f"⚠️ Error: {e}")

    #
    # SLASH COMMANDS
    #

    @app_commands.command(
        name="mcobjs",
        description="Lists all scoreboard objectives (requires RCON)."
    )
    async def mcobjs_slash(self, interaction: discord.Interaction):
        cfg = get_guild_config(self.bot, str(interaction.guild_id))
        try:
            raw = await asyncio.get_event_loop().run_in_executor(
                None, run_rcon_command, "scoreboard objectives list", cfg
            )
            objs = raw.split(":", 1)[1].split(",") if ":" in raw else []
            names = [o.strip().split(" ", 1)[0] for o in objs]
            msg = f"🗒️ Objectives: {', '.join(names)}" if names else "ℹ️ No objectives found."
            await interaction.response.send_message(msg)
        except Exception as e:
            await interaction.response.send_message(f"⚠️ Error: {e}", ephemeral=True)

    @app_commands.command(
        name="mcstat",
        description="Fetch a player’s score for a scoreboard objective (requires RCON)."
    )
    @app_commands.describe(player="Player name", objective="Objective name")
    async def mcstat_slash(
        self,
        interaction: discord.Interaction,
        player: str,
        objective: str
    ):
        cfg = get_guild_config(self.bot, str(interaction.guild_id))
        try:
            raw = await asyncio.get_event_loop().run_in_executor(
                None, run_rcon_command,
                f"scoreboard players get {player} {objective}", cfg
            )
            m = re.search(r"(-?\d+)", raw)
            score = m.group(1) if m else "0"
            await interaction.response.send_message(f"📊 `{player}` has `{score}` on `{objective}`.")
        except Exception as e:
            await interaction.response.send_message(f"⚠️ Error: {e}", ephemeral=True)

    @app_commands.command(
        name="mcleaderboard",
        description="Show top players for a scoreboard objective (requires RCON)."
    )
    @app_commands.describe(
        objective="Objective name",
        count="How many top entries (default 5)"
    )
    async def mcleaderboard_slash(
        self,
        interaction: discord.Interaction,
        objective: str,
        count: int = 5
    ):
        cfg = get_guild_config(self.bot, str(interaction.guild_id))
        try:
            raw = await asyncio.get_event_loop().run_in_executor(
                None, run_rcon_command,
                f"scoreboard players list {objective}", cfg
            )
            parts = raw.split(":", 1)[1].split(",") if ":" in raw else []
            entries = []
            for part in parts:
                part = part.strip()
                m = re.match(r"(\S+) has (-?\d+)", part)
                if m:
                    entries.append((m.group(1), int(m.group(2))))
            if not entries:
                return await interaction.response.send_message(f"ℹ️ No scores for `{objective}`.")
            entries.sort(key=lambda x: x[1], reverse=True)

            embed = discord.Embed(
                title=f"🏆 Leaderboard: {objective}",
                color=0x00ff00
            )
            for i, (name, score) in enumerate(entries[:count], start=1):
                embed.add_field(name=f"{i}. {name}", value=str(score), inline=False)

            await interaction.response.send_message(embed=embed)
        except Exception as e:
            await interaction.response.send_message(f"⚠️ Error: {e}", ephemeral=True)


async def setup(bot: commands.Bot):
    await bot.add_cog(StatsCog(bot))
