import discord
from discord.ext import commands
import os
import asyncio
import subprocess
import json

# Discord bot token
DISCORD_TOKEN = "YOUR_DISCORD_BOT_TOKEN"

# Intents and bot setup
intents = discord.Intents.default()
intents.messages = True
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# Global variables for queue and current song
song_queue = asyncio.Queue()
current_song = None


async def download_audio_stream(youtube_url):
    """Downloads the audio stream from a YouTube URL using yt-dlp."""
    try:
        # Get video metadata
        result = subprocess.run(
            ["yt-dlp", "--print-json", "--no-warnings", youtube_url],
            capture_output=True,
            text=True,
        )

        if result.returncode != 0 or not result.stdout.strip():
            print(f"Error: yt-dlp failed to fetch metadata for URL: {youtube_url}")
            return None, None

        video_info = json.loads(result.stdout)
        title = video_info.get("title", "Unknown Title")

        # Download the audio stream
        output_file = f"audio_temp_{hash(youtube_url)}.mp3"
        subprocess.run(
            [
                "yt-dlp",
                "-x",
                "--audio-format",
                "mp3",
                "-o",
                output_file,
                youtube_url,
            ],
            check=True,
        )
        print(f"Download completed: {title}")
        return output_file, title

    except Exception as e:
        print(f"Error downloading audio stream: {e}")
        return None, None


async def play_next(ctx):
    """Plays the next song in the queue."""
    global current_song

    if not song_queue.empty():
        youtube_url = await song_queue.get()
        audio_file, title = await download_audio_stream(youtube_url)

        if audio_file:
            current_song = audio_file
            ffmpeg_options = {
                "before_options": "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5",
                "options": "-vn",
            }
            audio_source = discord.FFmpegPCMAudio(audio_file, **ffmpeg_options)
            ctx.voice_client.play(
                audio_source,
                after=lambda e: asyncio.run_coroutine_threadsafe(play_next(ctx), bot.loop),
            )
            await ctx.send(f"Now playing: {title}")
        else:
            await ctx.send("Failed to play the next song.")
    else:
        current_song = None
        await ctx.send("The queue is empty!")


@bot.command()
async def join(ctx):
    """Command to join the voice channel."""
    if ctx.author.voice:
        channel = ctx.author.voice.channel
        await channel.connect()
        await ctx.send(f"Joined {channel}")
    else:
        await ctx.send("You need to be in a voice channel to use this command!")


@bot.command()
async def leave(ctx):
    """Command to leave the voice channel."""
    if ctx.voice_client:
        await ctx.voice_client.disconnect()
        await ctx.send("Disconnected from the voice channel.")
    else:
        await ctx.send("I'm not in a voice channel!")


@bot.command()
async def play(ctx, youtube_url):
    """Command to queue and play a YouTube URL."""
    global current_song

    await song_queue.put(youtube_url)
    await ctx.send(f"Added to queue: {youtube_url}")

    if not ctx.voice_client.is_playing() and current_song is None:
        await play_next(ctx)


@bot.command()
async def skip(ctx):
    """Command to skip the current song."""
    if ctx.voice_client and ctx.voice_client.is_playing():
        ctx.voice_client.stop()
        await ctx.send("Skipping the current song.")
    else:
        await ctx.send("No song is currently playing.")


@bot.command()
async def queue(ctx):
    """Command to show the current queue."""
    if song_queue.empty():
        await ctx.send("The queue is empty!")
    else:
        queue_list = list(song_queue._queue)  # Access the queue
        message = "Current Queue:\n" + "\n".join(
            [f"{i + 1}. {url}" for i, url in enumerate(queue_list)]
        )
        await ctx.send(message)


# Run the bot
bot.run(DISCORD_TOKEN)
