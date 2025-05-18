import os
import json
from dotenv import load_dotenv
from mcrcon import MCRcon

load_dotenv()

# Defaults & paths
DEFAULT_IP            = os.getenv("MC_IP", "mc.hypixel.net")
DEFAULT_PORT          = int(os.getenv("MC_PORT", "25565"))
DEFAULT_RCON_PASSWORD = os.getenv("MC_RCON_PASSWORD", "")
DEFAULT_PREFIX        = "!"

SERVER_CFG_PATH = "server_configs.json"
WAYPOINTS_PATH  = "waypoints.json"

def load_json(path: str):
    if os.path.exists(path):
        return json.load(open(path))
    return {}

def save_json(path: str, data):
    json.dump(data, open(path, "w"), indent=4)

async def get_prefix(bot, message):
    if not message.guild:
        return DEFAULT_PREFIX
    return bot.server_configs.get(str(message.guild.id), {}).get("prefix", DEFAULT_PREFIX)

def get_guild_config(bot, guild_id: str):
    raw = bot.server_configs.get(guild_id, {})
    return {
        "ip":       raw.get("ip",       DEFAULT_IP),
        "port":     raw.get("port",     DEFAULT_PORT),
        "password": raw.get("password", DEFAULT_RCON_PASSWORD),
    }

def run_rcon_command(cmd: str, cfg: dict) -> str:
    ip, port, pw = cfg["ip"], cfg["port"], cfg["password"]
    if not pw:
        raise RuntimeError("RCON password not set for this server.")
    with MCRcon(ip, pw, port=port) as mcr:
        return mcr.command(cmd)
