import discord
from discord import app_commands
from discord.ext import commands
from discord.ui import View, button
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
        for b in self.children:
            b.disabled = True
        await self.message.edit(view=self)

    @button(label="◀️ Prev", style=discord.ButtonStyle.secondary)
    async def prev_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.author:
            return await interaction.response.send_message(
                "Only the author can navigate.", ephemeral=True
            )
        if self.current > 0:
            self.current -= 1
            embed = self.pages[self.current]
            embed.set_footer(text=self.footer_texts[self.current])
            await interaction.response.edit_message(embed=embed, view=self)

    @button(label="Next ▶️", style=discord.ButtonStyle.secondary)
    async def next_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.author:
            return await interaction.response.send_message(
                "Only the author can navigate.", ephemeral=True
            )
        if self.current < len(self.pages) - 1:
            self.current += 1
            embed = self.pages[self.current]
            embed.set_footer(text=self.footer_texts[self.current])
            await interaction.response.edit_message(embed=embed, view=self)


class WaypointCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    #
    # --- PREFIX COMMANDS ---
    #

    @commands.command(
        name="waypointadd",
        help=(
            "**Usage**\n"
            "`!waypointadd <x> <z> <name>` or `!waypointadd <x> <z> <name> <y>`\n\n"
            "Adds a waypoint at integer coords; stores who added and date added.\n\n"
            "**Example**\n"
            "`!waypointadd 100 20 HomeBase`"
        )
    )
    async def waypointadd(self, ctx: commands.Context, *args):
        wps = self.bot.all_waypoints.setdefault(str(ctx.guild.id), {})
        if len(args) < 3:
            return await ctx.send(
                "❌ Usage: `!waypointadd <x> <z> <name>` or `!waypointadd <x> <y> <z> <name>`"
            )
        x = y = z = None
        name_parts = []
        if len(args) >= 4 and args[0].lstrip('-').isdigit() and args[1].lstrip('-').isdigit() and args[2].lstrip('-').isdigit():
            try:
                x, y, z = int(args[0]), int(args[1]), int(args[2])
            except ValueError:
                return await ctx.send("❌ Coordinates must be integers.")
            name_parts = args[3:]
        else:
            if args[0].lstrip('-').isdigit() and args[1].lstrip('-').isdigit():
                try:
                    x, z = int(args[0]), int(args[1])
                except ValueError:
                    return await ctx.send("❌ Coordinates must be integers.")
                name_parts = args[2:]
            else:
                return await ctx.send("❌ Coordinates must be integers.")
        if not name_parts:
            return await ctx.send("❌ You must provide a name.")
        name_key = " ".join(name_parts).lower()
        if name_key in wps:
            return await ctx.send(f"❌ A waypoint named `{name_key}` already exists.")
        wps[name_key] = {
            "x": x,
            "y": y,
            "z": z,
            "added_by": ctx.author.id,
            "added_at": datetime.now().strftime("%m/%d/%y")
        }
        save_json(WAYPOINTS_PATH, self.bot.all_waypoints)
        if y is None:
            coord_str = f"(X: {x}, Z: {z})"
        else:
            coord_str = f"(X: {x}, Y: {y}, Z: {z})"
        await ctx.send(f"✅ Waypoint `{name_key}` added at {coord_str}.")

    @commands.command(
        name="waypointremove",
        help=(
            "**Usage**\n"
            "`!waypointremove <name>`\n\n"
            "Removes a waypoint you created (or any if admin).\n\n"
            "**Example**\n"
            "`!waypointremove HomeBase`"
        )
    )
    async def waypointremove(self, ctx: commands.Context, *args):
        wps = self.bot.all_waypoints.setdefault(str(ctx.guild.id), {})
        if not args:
            return await ctx.send("❌ Usage: `!waypointremove <name>`")
        name = " ".join(args).lower()
        if name not in wps:
            return await ctx.send(f"❌ No waypoint named `{name}`.")
        rec = wps[name]
        if ctx.author.id != rec["added_by"] and not ctx.author.guild_permissions.administrator:
            return await ctx.send("❌ Only the creator or an admin may remove this.")
        del wps[name]
        save_json(WAYPOINTS_PATH, self.bot.all_waypoints)
        await ctx.send(f"🗑️ Waypoint `{name}` removed.")

    @commands.command(
        name="waypoints",
        help=(
            "**Usage**\n"
            "`!waypoints`\n\n"
            "Lists all waypoint names and coords (5 per page).\n\n"
            "**Example**\n"
            "`!waypoints`"
        )
    )
    async def waypoints(self, ctx: commands.Context):
        wps = self.bot.all_waypoints.setdefault(str(ctx.guild.id), {})
        if not wps:
            return await ctx.send("ℹ️ No waypoints added yet.")
        entries = []
        for n, r in wps.items():
            coords = [f"X: {r['x']}"]
            if r.get("y") is not None:
                coords.append(f"Y: {r['y']}")
            coords.append(f"Z: {r['z']}")
            coord_str = "`" + ", ".join(coords) + "`"
            entries.append((n.title(), coord_str))
        pages, footers = [], []
        total = (len(entries) - 1) // 5 + 1
        for i in range(0, len(entries), 5):
            embed = discord.Embed(title="📍 Waypoints", color=0x00ff00)
            for name, coord in entries[i : i + 5]:
                embed.add_field(name=name, value=coord, inline=False)
            footer = f"Page {i//5+1}/{total} • Requested by {ctx.author.display_name}"
            embed.set_footer(text=footer)
            pages.append(embed)
            footers.append(footer)
        paginator = WaypointPaginator(pages, ctx.author, footers)
        msg = await ctx.send(embed=pages[0], view=paginator)
        paginator.message = msg

    @commands.command(
        name="waypointinfo",
        help=(
            "**Usage**\n"
            "`!waypointinfo <name>`\n\n"
            "Shows coords, who added, and date for a waypoint.\n\n"
            "**Example**\n"
            "`!waypointinfo HomeBase`"
        )
    )
    async def waypointinfo(self, ctx: commands.Context, *args):
        wps = self.bot.all_waypoints.setdefault(str(ctx.guild.id), {})
        if not args:
            return await ctx.send("❌ Usage: `!waypointinfo <name>`")
        name = " ".join(args).lower()
        if name not in wps:
            return await ctx.send(f"❌ No waypoint named `{name}`.")
        r = wps[name]
        embed = discord.Embed(
            title=f"📍 Waypoint: {name.title()}",
            color=0x00ff00
        )
        coords = [f"• X: `{r['x']}`"]
        if r.get("y") is not None:
            coords.append(f"• Y: `{r['y']}`")
        coords.append(f"• Z: `{r['z']}`")
        embed.add_field(name="Coordinates", value="\n".join(coords), inline=False)
        added_by = (
            ctx.guild.get_member(r['added_by']).display_name
            if ctx.guild.get_member(r['added_by']) else "Unknown"
        )
        embed.set_author(name=f"Added by {added_by}")
        embed.set_footer(
            text=f"Date added: {r['added_at']} • Requested by {ctx.author.display_name}"
        )
        await ctx.send(embed=embed)

    #
    # --- SLASH COMMANDS ---
    #

    @app_commands.command(
        name="waypointadd",
        description="Add a waypoint at X [Y] Z with a name"
    )
    @app_commands.describe(
        x="X coordinate (integer)",
        z="Z coordinate (integer)",
        name="Waypoint name",
        y="Y coordinate (integer, optional)"
    )
    async def waypointadd_slash(
        self,
        interaction: discord.Interaction,
        x: int,
        z: int,
        name: str,
        y: int | None = None
    ):
        wps = self.bot.all_waypoints.setdefault(str(interaction.guild_id), {})
        key = name.lower()
        if key in wps:
            return await interaction.response.send_message(
                f"❌ A waypoint named `{key}` already exists.", ephemeral=True
            )
        wps[key] = {"x": x, "y": y, "z": z, "added_by": interaction.user.id, "added_at": datetime.now().strftime("%m/%d/%y")}        
        save_json(WAYPOINTS_PATH, self.bot.all_waypoints)
        if y is None:
            coord_str = f"(X: {x}, Z: {z})"
        else:
            coord_str = f"(X: {x}, Y: {y}, Z: {z})"
        await interaction.response.send_message(f"✅ Waypoint `{key}` added at {coord_str}.")

    @app_commands.command(name="waypointremove", description="Remove a named waypoint (your own or, if admin, any)")
    @app_commands.describe(name="Name of the waypoint")
    async def waypointremove_slash(self, interaction: discord.Interaction, name: str):
        wps = self.bot.all_waypoints.setdefault(str(interaction.guild_id), {})
        key = name.lower()
        if key not in wps:
            return await interaction.response.send_message(f"❌ No waypoint named `{key}` found.", ephemeral=True)
        rec = wps[key]
        if interaction.user.id != rec["added_by"] and not interaction.user.guild_permissions.administrator:
            return await interaction.response.send_message("❌ You may only remove your own.", ephemeral=True)
        del wps[key]
        save_json(WAYPOINTS_PATH, self.bot.all_waypoints)
        await interaction.response.send_message(f"🗑️ Waypoint `{key}` removed.")

    @app_commands.command(name="waypoints", description="List all waypoints (paginated)")
    async def waypoints_slash(self, interaction: discord.Interaction):
        wps = self.bot.all_waypoints.setdefault(str(interaction.guild_id), {})
        if not wps:
            return await interaction.response.send_message("ℹ️ No waypoints added.", ephemeral=True)
        entries = []
        for n, r in wps.items():
            coords = [f"X: {r['x']}"]
            if r.get("y") is not None:
                coords.append(f"Y: {r['y']}")
            coords.append(f"Z: {r['z']}")
            coord_str = "`" + ", ".join(coords) + "`"
            entries.append((n.title(), coord_str))
        pages, footers = [], []
        total = (len(entries) - 1) // 5 + 1
        for i in range(0, len(entries), 5):
            embed = discord.Embed(title="📍 Waypoints", color=0x00ff00)
            for name, coord in entries[i : i + 5]:
                embed.add_field(name=name, value=coord, inline=False)
            footer = f"Page {i//5+1}/{total} • {interaction.user.display_name}"
            embed.set_footer(text=footer)
            pages.append(embed)
            footers.append(footer)
        paginator = WaypointPaginator(pages, interaction.user, footers)
        await interaction.response.send_message(embed=pages[0], view=paginator)

    @app_commands.command(name="waypointinfo", description="Show details about a named waypoint")
    @app_commands.describe(name="Name of the waypoint")
    async def waypointinfo_slash(self, interaction: discord.Interaction, name: str):
        wps = self.bot.all_waypoints.setdefault(str(interaction.guild_id), {})
        key = name.lower()
        if key not in wps:
            return await interaction.response.send_message(f"❌ No waypoint named `{key}` found.", ephemeral=True)
        r = wps[key]
        embed = discord.Embed(title=f"📍 Waypoint: {key.title()}", color=0x00ff00)
        coords = [f"• X: `{r['x']}`"]
        if r.get("y") is not None:
            coords.append(f"• Y: `{r['y']}`")
        coords.append(f"• Z: `{r['z']}`")
        embed.add_field(name="Coordinates", value="\n".join(coords), inline=False)
        added_by = interaction.guild.get_member(r["added_by"]).display_name if interaction.guild.get_member(r["added_by"]) else "Unknown"
        embed.set_author(name=f"Added by {added_by}")
        embed.set_footer(text=f"Date added: {r['added_at']} • {interaction.user.display_name}")
        await interaction.response.send_message(embed=embed)

async def setup(bot: commands.Bot):
    await bot.add_cog(WaypointCog(bot))
