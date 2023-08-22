import discord
import asyncio
import requests
import config
from a2s import players
from a2s import info
from bs4 import BeautifulSoup
from datetime import datetime


intents = discord.Intents.all()
intents.members = True

client = discord.Client(intents=intents)


@client.event
async def on_ready():
    print(f'{client.user} has connected to Discord!')

    # show activity bot
    activity = discord.Activity(
        name='Eye of Sayhigh', type=discord.ActivityType.playing)
    await client.change_presence(activity=activity)


@client.event
async def on_message(message):
    if message.author == client.user:
        return

    # funcion show player name and time on server
    if message.content.startswith('!s'):
        serverName = message.content.split()[1]
        try:
            # show server from battlemetrics
            destination = requests.get(
                f"https://www.battlemetrics.com/servers/ark?q={serverName}&sort=score")
            soup = BeautifulSoup(destination.content, 'html.parser')

            all_servername_raw = soup.find_all("a")
            global all_server_list
            all_server_list = {}
            list_number = 0

            for serverList in all_servername_raw:
                if serverList.get("title"):
                    list_number += 1
                    all_server_list[list_number] = [
                        (serverList.get("title"), serverList.get("href"))]

            server_list = (
                "```\n## Multiple servers found. Specify the server name or enter a number.\n\n")

            for number, name in all_server_list.items():
                server_list += (f"\n({number}) - { name[0][0]}")
            await message.channel.send(server_list+"```")
        except:
            pass

        try:
            # wait message from user
            response = await client.wait_for(
                'message',
                timeout=30,
                check=lambda m: m.author == message.author
            )
            server_selection = int(response.content)
        except asyncio.TimeoutError:
            print("time out")

        try:
            # get server IPAddress from user selected server
            server = all_server_list[server_selection]
            destination = requests.get(
                f"https://www.battlemetrics.com{server[0][1]}")
            soup = BeautifulSoup(destination.content, 'html.parser')
            find_ip = soup.find(class_="css-1i1egz4")

            data = []

            for element in find_ip:
                span_elements = element.find_all("span")
                for span in span_elements:
                    data.append(span.get_text())
            ipAddress = data[1]
            server_ip = ipAddress.split(":")
            server_ip = (server_ip[0], int(server_ip[1]))
        except UnboundLocalError:
            pass

        try:
            players = players(address=server_ip)
            server_info = info(address=server_ip)
            await message.channel.send(f"```fix\n{server_info.server_name}\nMap: {server_info.map_name}\nPlayers: {server_info.player_count}/{server_info.max_players}```")
            player_list = []
            # add player data to player_list
            for player in players:
                player_name = player.name
                player_duration = player.duration
                hours, remainder = divmod(player_duration, 3600)
                minutes, seconds = divmod(remainder, 60)
                time_str = f"{int(hours)}::{int(minutes)}::{int(seconds)}"
                formatted_duration = datetime.strptime(
                    time_str, '%H::%M::%S').time()
                player_list.append((formatted_duration, player_name))
            show_player_list = "```ini\n[Online Time]          [Name]\n"
            for duration, name in player_list:
                show_player_list += (
                    f"\n [{duration}]           {name:<24}")

            await message.channel.send(show_player_list+"```")
        except Exception as e:
            print(e)

    # funcion show info player from id steam
    if message.content.startswith('!id'):
        id_steam = message.content.split()[1]
        try:
            response = requests.get(
                f'https://api.steampowered.com/ISteamUser/GetPlayerSummaries/v0002/?key={config.STEAM_API_KEY}&steamids={id_steam}&format=json')
            response_json = response.json()
            player = response_json['response']['players'][0]

            # get player data
            name = player.get('personaname', 'Unknown')
            profile_url = player.get('profileurl', '')
            last_online = player.get('lastlogoff', 0)
            time_since_last_online = datetime.utcnow().timestamp() - last_online
            status = 'Online' if player.get(
                'personastate', 0) == 1 else 'Offline'
            game_id = player.get('gameid', 0)
            last_played_game = ''
            if game_id != 0:
                response = requests.get(
                    f'https://api.steampowered.com/ISteamUserStats/GetUserStatsForGame/v0002/?appid={game_id}&key={config.STEAM_API_KEY}&steamid={id_steam}&format=json')
                response_json = response.json()
                last_played_game = response_json.get(
                    'playerstats', {}).get('gameName', '')

            await message.channel.send(f"""```ini\n
[Name]             : {name}
[Profile]          : {profile_url}
[Status]           : {status}
[Last Online]      : {time_since_last_online // 3600} hours ago
[Last Played Game] : {last_played_game}```""")
        except Exception as e:
            print(e)


client.run(config.BOT_KEY)