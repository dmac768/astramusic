import discord
from discord.ext import commands
from pytube import YouTube
import os
import asyncio

# Discord bot token
DISCORD_TOKEN = "TOKEN"

# Intents and bot setup
intents = discord.Intents.default()
intents.messages = True
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# Global queue
song_queue = asyncio.Queue()
current_song = None


def download_audio_stream(youtube_url):
    """Downloads the audio stream from a YouTube URL."""
    try:
        yt = YouTube(youtube_url)
        audio_stream = yt.streams.filter(only_audio=True).first()

        if not audio_stream:
            return None

        print(f"Downloading audio stream: {audio_stream.title}")
        output_file = audio_stream.download(filename="audio_temp.mp4")
        print("Download completed.")
        return output_file
    except Exception as e:
        print(f"Error downloading audio stream: {e}")
        return None


async def play_next(ctx):
    """Plays the next song in the queue."""
    global current_song

    if not song_queue.empty():
        # Get the next song
        youtube_url = await song_queue.get()
        current_song = download_audio_stream(youtube_url)

        if current_song:
            ffmpeg_options = {
                "before_options": "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5",
                "options": "-vn",
            }
            audio_source = discord.FFmpegPCMAudio(current_song, **ffmpeg_options)
            ctx.voice_client.play(
                audio_source, after=lambda e: asyncio.run_coroutine_threadsafe(play_next(ctx), bot.loop)
            )

            await ctx.send(f"Now playing: {YouTube(youtube_url).title}")
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

    # Add the song to the queue
    await song_queue.put(youtube_url)
    await ctx.send(f"Added to queue: {YouTube(youtube_url).title}")

    # If no song is currently playing, start playback
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
            [f"{i + 1}. {YouTube(url).title}" for i, url in enumerate(queue_list)]
        )
        await ctx.send(message)


# Run the bot
bot.run(DISCORD_TOKEN)
