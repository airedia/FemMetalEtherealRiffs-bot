import discord
from discord.ext import commands
import os
from dotenv import load_dotenv
import asyncio
from googleapiclient.discovery import build
from pytube import YouTube
#from pytube.exceptions import AgeRestricted


dotenv_path = os.path.join(os.path.dirname(__file__), 'discord_token.env')
load_dotenv(dotenv_path)
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")

dotenv_path_1 = os.path.join(os.path.dirname(__file__), 'youtube_api_key.env')
load_dotenv(dotenv_path_1)
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")

intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True
bot = commands.Bot(command_prefix='!!', intents=intents)

# Initialize the YouTube Data API client
youtube = build('youtube', 'v3', developerKey=YOUTUBE_API_KEY)

@bot.event
async def on_ready():
    print(f'Logged in {bot.user} | {bot.user.id}')

@bot.command()
async def play(ctx, *, search_query: str):
    print(f"Received !!play command with search query: {search_query}")
    if not ctx.author.voice:
        await ctx.send("You're not connected to a voice channel.")
        return

    voice_channel = ctx.author.voice.channel
    voice_client = ctx.voice_client

    if voice_client is None:
        voice_client = await voice_channel.connect()

    try:
        
        search_query_with_filters = f'{search_query} metal rock'

      
        search_response = youtube.search().list(
            q=search_query_with_filters,
            type='video',
            part='id,snippet',  
            maxResults=10, 
            order='viewCount' 
        ).execute()

       
        if 'items' in search_response:
            
            filtered_results = []
            cover_keywords = ['cover', 'remix', 'version', 'live', '#', ' @']  

            for item in search_response['items']:
                video_title = item['snippet']['title'].lower()
                is_cover = any(keyword in video_title for keyword in cover_keywords)

                if not is_cover:
                    filtered_results.append(item)

            if not filtered_results:
                await ctx.send("No suitable non-cover search results found.")
                return

            video_id = filtered_results[0]['id']['videoId']
            video_url = f'https://www.youtube.com/watch?v={video_id}'

            # Download the audio from the video using pytube
            yt = YouTube(video_url)

            # Check if the video is age-restricted by examining its details
            age_restricted = yt.age_restricted
            if age_restricted:
                await ctx.send("Sorry, the selected video is age-restricted and cannot be played without logging in to YouTube.")
                return

            stream = yt.streams.filter(only_audio=True).first()

            if not stream:
                await ctx.send("Sorry, I couldn't find an audio stream for this video.")
                return

            # Download the audio stream
            audio_file = stream.download()

            # Play the downloaded audio in the voice channel
            voice_client.stop()
            voice_client.play(discord.FFmpegPCMAudio(audio_file))

            # Send a message with song information
            song_title = yt.title
            artist_name = yt.author
            await ctx.send(f"Now playing: {artist_name} - {song_title} {video_url}")
        else:
            await ctx.send("No search results found.")

    except Exception as e:
        await ctx.send(f"An error occurred: {str(e)}")




@bot.command()
async def stop(ctx):
    voice_client = ctx.voice_client
    if voice_client:
        voice_client.stop()

@bot.command()
async def pause(ctx):
    voice_client = ctx.voice_client
    if voice_client and voice_client.is_playing():
        voice_client.pause()

@bot.command()
async def resume(ctx):
    voice_client = ctx.voice_client
    if voice_client and voice_client.is_paused():
        voice_client.resume()

bot.run(DISCORD_TOKEN)
