# help_command.py

import discord
from discord.ext import commands
from discord import app_commands

# commands that need RCON (we’ll mark them with *)
RCON_COMMANDS = {
    "mctime", "mcseed", "mcstop",
    "mcobjs", "mcstat", "mcleaderboard",
}

# categories for the command list
CATEGORIES = {
    "📍 Server Waypoints":    ["waypointadd", "waypointremove", "waypoints", "waypointinfo"],
    "⚙️ Configuration":       ["config", "setserverinfo", "prefix"],
    "🖥️ Server Info":         ["mcstatus", "mcplayers", "mcinfo", "mcping"],
    "🔌 RCON":                ["mctime", "mcseed", "mcstop"],
    "📊 Stats":               ["mcobjs", "mcstat", "mcleaderboard"],
}


class MyHelp(commands.HelpCommand):
    def __init__(self):
        super().__init__(command_attrs={
            "help":    "Shows help about the bot or a specific command",
            "aliases": ["h"]
        })

    async def send_bot_help(self, mapping):
        """Prefix !help (no args)"""
        embed = discord.Embed(title="Help — Command List", color=0x00ff00)
        for cat_name, names in CATEGORIES.items():
            lines = []
            for name in names:
                cmd = self.context.bot.get_command(name)
                if not cmd:
                    continue
                try:
                    if not await cmd.can_run(self.context):
                        continue
                except commands.CommandError:
                    continue
                tag = "*" if name in RCON_COMMANDS else ""
                lines.append(f"`{name}`{tag}")
            if lines:
                embed.add_field(name=cat_name, value="\n".join(lines), inline=False)
        embed.set_footer(text="* commands require RCON")
        await self.get_destination().send(embed=embed)

    async def send_command_help(self, command):
        """Prefix !help <command>"""
        embed = discord.Embed(
            title=f"!{command.name}",
            description=command.help or "No description available.",
            color=0x00ff00
        )
        # mark if it needs RCON
        if command.name in RCON_COMMANDS:
            embed.set_footer(text="* requires RCON")
        await self.get_destination().send(embed=embed)

    async def send_error_message(self, error):
        await self.get_destination().send(f"❌ {error}")


class HelpCog(commands.Cog):
    """Adds a /help slash command mirroring the prefix help."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(
        name="help",
        description="Show help — command list or details for one command"
    )
    @app_commands.describe(
        command="(Optional) Name of a command to get detailed help"
    )
    async def help_slash(self, interaction: discord.Interaction, command: str = None):
        # If a command name was given, show detailed help
        if command:
            cmd = self.bot.get_command(command)
            if not cmd:
                return await interaction.response.send_message(
                    f"❌ Unknown command `{command}`",
                    ephemeral=True
                )
            # build the same embed as prefix help would
            embed = discord.Embed(
                title=f"/{cmd.name}",
                description=cmd.help or "No description available.",
                color=0x00ff00
            )
            if cmd.name in RCON_COMMANDS:
                embed.set_footer(text="* requires RCON")
            return await interaction.response.send_message(embed=embed, ephemeral=True)

        # Otherwise, show the full command list
        embed = discord.Embed(title="Help — Command List", color=0x00ff00)
        for cat_name, names in CATEGORIES.items():
            lines = []
            for name in names:
                if not self.bot.get_command(name):
                    continue
                tag = "*" if name in RCON_COMMANDS else ""
                lines.append(f"`/{name}`{tag}")
            if lines:
                embed.add_field(name=cat_name, value="\n".join(lines), inline=False)
        embed.set_footer(text="* commands require RCON")
        await interaction.response.send_message(embed=embed, ephemeral=True)


async def setup(bot: commands.Bot):
    await bot.add_cog(HelpCog(bot))
