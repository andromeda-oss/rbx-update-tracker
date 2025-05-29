import io
import os
import discord
from discord.ext import tasks, commands
from dotenv import load_dotenv
from utils.tracker import check_for_update, fetch_api_dump, load_json

load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")
CHANNEL_ID = int(os.getenv("DISCORD_CHANNEL_ID"))
CHECK_INTERVAL = int(os.getenv("CHECK_INTERVAL", "300"))

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user.name}")
    check_update.start()

@tasks.loop(seconds=CHECK_INTERVAL)
async def check_update():
    try:
        updated, new_version, new_hash, diff_text = await check_for_update()
        if updated:
            embed = discord.Embed(title="📦 Roblox Update Detected!", color=0x008000)
            embed.add_field(name="Roblox Version", value=f"`{new_version}`", inline=False)
            embed.add_field(name="API Hash", value=f"`{new_hash}`", inline=False)
            embed.set_footer(text="yeah we're cracking flushed all summer 💀🙏💔🥀")

            if len(diff_text) <= 1024 and len(diff_text) > 0:
                embed.add_field(name="API Changes", value=f"```diff\n{diff_text}\n```", inline=False)
                files = None
            elif len(diff_text) == 0:
                embed.add_field(name="API Changes", value="```diff\n- No changes detected\n```", inline=False)
                files = None
            else:
                files = [discord.File(fp=io.StringIO(diff_text), filename="diff.txt")]

            channel = await bot.fetch_channel(CHANNEL_ID)
            await channel.send(embed=embed, files=files)
            print("✅ Sent update message.")

            # dump = load_json("latest_api_dump.json")
            # if dump:
            #     dump_file = discord.File(io.BytesIO(str(dump).encode('utf-8')), filename="latest_api_dump.json")
            #     await channel.send(file=dump_file)
            #     print("✅ Sent latest API dump.")

    except Exception as e:
        print(f"❌ Error in check_update task: {e}")


bot.run(TOKEN)
