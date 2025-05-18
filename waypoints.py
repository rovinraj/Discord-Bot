import discord
from discord.ui import View, button
from discord import app_commands
from discord.ext import commands
from datetime import datetime
from utils import save_json, WAYPOINTS_PATH

class WaypointPaginator(View):
    def __init__(self, pages, author, footer_texts):
        super().__init__(timeout=120)
        self.pages = pages
        self.current = 0
        self.author = author
        self.footer_texts = footer_texts
    async def on_timeout(self):
        for b in self.children: b.disabled = True
        await self.message.edit(view=self)
    @button(label="◀️ Prev", style=discord.ButtonStyle.secondary)
    async def prev_button(self, interaction, button):
        if interaction.user != self.author:
            return await interaction.response.send_message("Only the author can navigate.", ephemeral=True)
        if self.current > 0:
            self.current -= 1
            embed = self.pages[self.current]
            embed.set_footer(text=self.footer_texts[self.current])
            await interaction.response.edit_message(embed=embed, view=self)
    @button(label="Next ▶️", style=discord.ButtonStyle.secondary)
    async def next_button(self, interaction, button):
        if interaction.user != self.author:
            return await interaction.response.send_message("Only the author can navigate.", ephemeral=True)
        if self.current < len(self.pages) - 1:
            self.current += 1
            embed = self.pages[self.current]
            embed.set_footer(text=self.footer_texts[self.current])
            await interaction.response.edit_message(embed=embed, view=self)

class WaypointCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    #
    # --- PREFIX COMMANDS ---
    #

    @commands.command(
        name="waypointadd",
        help="**Usage**\n"
             "`!waypointadd <x> <y> <name>` or `!waypointadd <x> <y> <z> <name>`\n\n"
             "Adds a waypoint at integer coords; stores who added and date added.\n\n"
             "**Example**\n"
             "`!waypointadd 100 64 HomeBase`"
    )
    async def waypointadd(self, ctx, *args):
        wps = self.bot.all_waypoints.setdefault(str(ctx.guild.id), {})
        if len(args) < 3:
            return await ctx.send("❌ Usage: `!waypointadd <x> <y> <name>` …")
        try:
            x, y = int(args[0]), int(args[1])
        except ValueError:
            return await ctx.send("❌ X and Y must be integers.")
        z = None
        if len(args) >= 4 and args[2].lstrip("-").isdigit():
            z, name_parts = int(args[2]), args[3:]
        else:
            name_parts = args[2:]
        if not name_parts:
            return await ctx.send("❌ You must provide a name.")
        name = " ".join(name_parts).lower()
        if name in wps:
            return await ctx.send(f"❌ A waypoint named `{name}` already exists.")
        wps[name] = {
            "x": x, "y": y, "z": z,
            "added_by": ctx.author.id,
            "added_at": datetime.now().strftime("%m/%d/%y")
        }
        save_json(WAYPOINTS_PATH, self.bot.all_waypoints)
        coord = f"({x}, {y}" + (f", {z})" if z is not None else ")")
        await ctx.send(f"✅ Waypoint `{name}` added at {coord}.")

    @commands.command(name="waypointremove", help="**Usage**\n"
         "`!waypointremove <name>`\n\n"
         "Removes a waypoint you created (or any if admin).\n\n"
         "**Example**\n"
         "`!waypointremove HomeBase`")
    async def waypointremove(self, ctx, *args):
        wps = self.bot.all_waypoints.setdefault(str(ctx.guild.id), {})
        if not args:
            return await ctx.send("❌ Usage: `!waypointremove <name>`")
        name = " ".join(args).lower()
        if name not in wps:
            return await ctx.send(f"❌ No waypoint named `{name}`.")
        rec = wps[name]
        if ctx.author.id != rec["added_by"] and not ctx.author.guild_permissions.administrator:
            return await ctx.send("❌ Only creator or admin may remove.")
        del wps[name]
        save_json(WAYPOINTS_PATH, self.bot.all_waypoints)
        await ctx.send(f"🗑️ Waypoint `{name}` removed.")

    @commands.command(
        name="waypoints",
        help="**Usage**\n"
             "`!waypoints`\n\n"
             "Lists all waypoint names and coords (5 per page).\n\n"
             "**Example**\n"
             "`!waypoints`"
    )
    async def waypoints(self, ctx):
        wps = self.bot.all_waypoints.setdefault(str(ctx.guild.id), {})
        if not wps:
            return await ctx.send("ℹ️ No waypoints added yet.")
        entries = [
            (n.title(),
             f"`X: {r['x']}, Y: {r['y']}" + (f", Z: {r['z']}`" if r['z'] else "`"))
            for n, r in wps.items()
        ]
        pages, footers = [], []
        total = (len(entries) - 1) // 5 + 1
        for i in range(0, len(entries), 5):
            embed = discord.Embed(title="📍 Waypoints", color=0x00ff00)
            for name, coord in entries[i:i + 5]:
                embed.add_field(name=name, value=coord, inline=False)
            footer = f"Page {i//5+1}/{total} • {ctx.author.display_name}"
            embed.set_footer(text=footer)
            pages.append(embed)
            footers.append(footer)
        paginator = WaypointPaginator(pages, ctx.author, footers)
        msg = await ctx.send(embed=pages[0], view=paginator)
        paginator.message = msg

    @commands.command(
        name="waypointinfo",
        help="**Usage**\n"
             "`!waypointinfo <name>`\n\n"
             "Shows coords, who added, and date for a waypoint.\n\n"
             "**Example**\n"
             "`!waypointinfo HomeBase`"
    )
    async def waypointinfo(self, ctx, *args):
        wps = self.bot.all_waypoints.setdefault(str(ctx.guild.id), {})
        if not args:
            return await ctx.send("❌ Usage: `!waypointinfo <name>`")
        name = " ".join(args).lower()
        if name not in wps:
            return await ctx.send(f"❌ No waypoint named `{name}`.")
        r = wps[name]
        embed = discord.Embed(title=f"📍 Waypoint: {name.title()}", color=0x00ff00)
        coords = [f"• X: `{r['x']}`", f"• Y: `{r['y']}`"]
        if r["z"] is not None:
            coords.append(f"• Z: `{r['z']}`")
        embed.add_field(name="Coordinates", value="\n".join(coords), inline=False)
        added_by = (ctx.guild.get_member(r['added_by']).display_name
                    if ctx.guild.get_member(r['added_by']) else "Unknown")
        embed.set_author(name=f"Added by {added_by}")
        embed.set_footer(text=f"Date added: {r['added_at']} • {ctx.author.display_name}")
        await ctx.send(embed=embed)

    #
    # --- SLASH COMMANDS ---
    #

    @app_commands.command(
        name="waypointadd",
        description="Add a waypoint at X Y [Z] with a name"
    )
    @app_commands.describe(
        x="X coordinate (integer)",
        y="Y coordinate (integer)",
        z="Z coordinate (integer, optional)",
        name="Waypoint name"
    )
    async def waypointadd_slash(self, interaction: discord.Interaction,
                                x: int,
                                y: int,
                                z: int | None,
                                name: str):
        """Slash /waypointadd"""
        wps = self.bot.all_waypoints.setdefault(str(interaction.guild_id), {})
        nm = name.lower()
        if nm in wps:
            return await interaction.response.send_message(f"❌ `{nm}` already exists.", ephemeral=True)
        wps[nm] = {
            "x": x, "y": y, "z": z,
            "added_by": interaction.user.id,
            "added_at": datetime.now().strftime("%m/%d/%y")
        }
        save_json(WAYPOINTS_PATH, self.bot.all_waypoints)
        coord = f"({x}, {y}" + (f", {z})" if z is not None else ")")
        await interaction.response.send_message(f"✅ Waypoint `{nm}` added at {coord}.")

    @app_commands.command(
        name="waypointremove",
        description="Remove a named waypoint (your own or, if admin, any)"
    )
    @app_commands.describe(name="Name of the waypoint")
    async def waypointremove_slash(self, interaction: discord.Interaction, name: str):
        """Slash /waypointremove"""
        wps = self.bot.all_waypoints.setdefault(str(interaction.guild_id), {})
        nm = name.lower()
        if nm not in wps:
            return await interaction.response.send_message(f"❌ No `{nm}` found.", ephemeral=True)
        rec = wps[nm]
        if interaction.user.id != rec["added_by"] and not interaction.user.guild_permissions.administrator:
            return await interaction.response.send_message("❌ You may only remove your own.", ephemeral=True)
        del wps[nm]
        save_json(WAYPOINTS_PATH, self.bot.all_waypoints)
        await interaction.response.send_message(f"🗑️ Waypoint `{nm}` removed.")

    @app_commands.command(
        name="waypoints",
        description="List all waypoints (paginated)"
    )
    async def waypoints_slash(self, interaction: discord.Interaction):
        """Slash /waypoints"""
        wps = self.bot.all_waypoints.setdefault(str(interaction.guild_id), {})
        if not wps:
            return await interaction.response.send_message("ℹ️ No waypoints added.", ephemeral=True)
        entries = [(n.title(),
                    f"`X: {r['x']}, Y: {r['y']}" + (f", Z: {r['z']}`" if r['z'] else "`"))
                   for n, r in wps.items()]
        pages, footers = [], []
        total = (len(entries) - 1) // 5 + 1
        for i in range(0, len(entries), 5):
            e = discord.Embed(title="📍 Waypoints", color=0x00ff00)
            for name, coord in entries[i:i+5]:
                e.add_field(name=name, value=coord, inline=False)
            footer = f"Page {i//5+1}/{total} • {interaction.user.display_name}"
            e.set_footer(text=footer)
            pages.append(e); footers.append(footer)

        paginator = WaypointPaginator(pages, interaction.user, footers)
        await interaction.response.send_message(embed=pages[0], view=paginator)

    @app_commands.command(
        name="waypointinfo",
        description="Show details about a named waypoint"
    )
    @app_commands.describe(name="Name of the waypoint")
    async def waypointinfo_slash(self, interaction: discord.Interaction, name: str):
        """Slash /waypointinfo"""
        wps = self.bot.all_waypoints.setdefault(str(interaction.guild_id), {})
        nm = name.lower()
        if nm not in wps:
            return await interaction.response.send_message(f"❌ No `{nm}` found.", ephemeral=True)
        r = wps[nm]
        embed = discord.Embed(title=f"📍 Waypoint: {nm.title()}", color=0x00ff00)
        coords = [f"• X: `{r['x']}`", f"• Y: `{r['y']}`"]
        if r["z"] is not None:
            coords.append(f"• Z: `{r['z']}`")
        embed.add_field(name="Coordinates", value="\n".join(coords), inline=False)
        added_by = (interaction.guild.get_member(r['added_by']).display_name
                    if interaction.guild.get_member(r['added_by']) else "Unknown")
        embed.set_author(name=f"Added by {added_by}")
        embed.set_footer(text=f"Date added: {r['added_at']} • {interaction.user.display_name}")
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(WaypointCog(bot))
