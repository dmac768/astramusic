import discord
from discord.ext import commands
import yt_dlp
import os

# Set up intents and bot
intents = discord.Intents.default()
intents.messages = True
intents.message_content = True
intents.guilds = True
intents.voice_states = True
intents.members = True
bot = commands.Bot(command_prefix="!", intents=intents)

# Function to play audio
async def play_audio(ctx, voice_channel, url):
    # Ensure cookies.txt exists
    cookies_file = "cookies.txt"
    if not os.path.exists(cookies_file):
        await ctx.send("Error: cookies.txt not found. Please ensure it is in the same folder as the bot script.")
        return

    # Connect to the voice channel
    vc = await voice_channel.connect()

    # Set yt-dlp options
    ydl_opts = {
        "format": "bestaudio",
        "cookies": cookies_file,
        "quiet": True,
        "postprocessors": [{"key": "FFmpegExtractAudio", "preferredcodec": "mp3"}],
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            info = ydl.extract_info(url, download=False)
            stream_url = info["url"]
            source = discord.FFmpegPCMAudio(stream_url)
            vc.play(source, after=lambda e: print(f"Player error: {e}") if e else None)
            await ctx.send(f"Now playing: {info['title']}")
        except Exception as e:
            await ctx.send(f"Error playing audio: {str(e)}")

# Command to join a voice channel
@bot.command(name="join")
async def join(ctx):
    if ctx.author.voice:
        voice_channel = ctx.author.voice.channel
        await voice_channel.connect()
        await ctx.send(f"Joined {voice_channel.name}")
    else:
        await ctx.send("You must be in a voice channel to use this command!")

# Command to play music
@bot.command(name="play")
async def play(ctx, url: str):
    if ctx.author.voice:
        await play_audio(ctx, ctx.author.voice.channel, url)
    else:
        await ctx.send("You must be in a voice channel to use this command!")

# Command to leave the voice channel
@bot.command(name="leave")
async def leave(ctx):
    if ctx.voice_client:
        await ctx.voice_client.disconnect()
        await ctx.send("Disconnected from the voice channel.")
    else:
        await ctx.send("I am not in a voice channel!")

# Bot event for startup
@bot.event
async def on_ready():
    print(f"Bot logged in as {bot.user}")

# Run the bot
