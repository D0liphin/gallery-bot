import os, time, asyncio, datetime, sys
import discord
from dotenv import *
from functools import partial

load_dotenv()
dotenvFile = find_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
MONKEY_IMAGE = os.getenv('MONKEY_IMAGE')
GALLERY_CHANNELS = eval(os.getenv('GALLERY_CHANNELS'))
CUSTOM_SETTINGS = eval(os.getenv('CUSTOM_SETTINGS'))
PIECE_IDS = eval(os.getenv('PIECE_IDS'))

async def update_dotenv(key, val, *args):
    if type(val) is not str:
        try: val = val.__str__()
        except: raise Exception("bad value format")
    set_key(dotenvFile, key, val)

    try:
        channel = args[-1]
        guild = channel.guild
        description = ""
        links = GALLERY_CHANNELS[guild.id]
        for link in links.keys():
            description += f"• **{links[link]}** ← {link}\n"
        DOTENV_EMBED = discord.Embed(title=f"𝔾𝕒𝕝𝕝𝕖𝕣𝕚𝕖𝕤", description=description)
        await args[-1].send(embed=DOTENV_EMBED)
    except:
        pass

HELP_TEXT = """
**gallery.modify**
Allows you to modify a piece in the destination channel, using the piece id
__Example__: **gallery.modify 945**

**gallery.advanced_help**
Shows a list of all commands with more detailed information about how to use them

----------------
__**ADMIN ONLY**__
----------------

**gallery.setup**
Set up a gallery
__Example__: **gallery.setup source-channel destination-channel**

**gallery.destroy**
Destroy a gallery (does not delete channels)
__Example__: **gallery.destroy source-channel destination-channel**

**gallery.catchup**
Add all recent images to the connected gallery
"""

ADVANCED_HELP_TEXT = """
`gallery.setup <source channel name> <destination channel name>`

> sets up a gallery from a specified source and specified destination

----------------------------------------------------------------------------

`gallery.catchup <automatic>`

> Adds a gallery entry for all images in the channel not in the gallery (until it reaches where it left off)
> Should be used if the bot disconnects.
> `<automatic>` should be left blank or set to 'verify' if you want to verify each image.
> note: this cannot be cancelled

----------------------------------------------------------------------------

`gallery.settings <setting> <new value>`

> `default_title` : `<new value>` is the title. Use hyphens `-` instead of spaces. e.g.
>     gallery.settings default_title No-Title
>     title = 'No Title'

> `date_format`: `<new value>` is the date format. e.g.
>     gallery.settings date_format DD-MM-YYYY
>     results in something like: '24-10-2020'

> `max_title_length`: `<new value>` is the title length e.g.
>     gallery.settings max_title_length 50  
"""


client = discord.Client()

async def disconnect_bot(args, channel):
    await channel.send(f"disconnecting...")
    await channel.send(f"bye bye :wave:")
    await client.logout()

HELP_EMBED = discord.Embed(description=HELP_TEXT)
ADVANCED_HELP_EMBED = discord.Embed(title="Advanced Help", description=ADVANCED_HELP_TEXT)


class Gallery:

    def __init__(self):
        self.commands = {
            'setup':self.setup,
            'update_dotenv': partial(update_dotenv, 'GALLERY_CHANNELS', GALLERY_CHANNELS),
            'disconnect': partial(disconnect_bot),
            'catchup': self.catchup,
            'settings': self.change_settings,
            'destroy': self.destroy,
            'modify': self.modify
        }
        self.settings = ["date_format", "default_title", "max_title_length"]

    async def setup(self, args, channel):
        source_channel = args[0]
        destination_channel = args[1]
        guild = channel.guild
        channel_lookup = {channel.name:channel for channel in guild.channels}
        error_channel, source, destination = None, None, None
        try:

            try: source = channel_lookup[source_channel]
            except: 
                error_channel = source_channel
                raise Exception

            try: destination = channel_lookup[destination_channel]
            except: 
                error_channel = destination_channel
                raise Exception

        except:
            await channel.send(f"**ERROR**\n> '**{error_channel}**' not a valid channel")
            return
        
        try:
            exists = GALLERY_CHANNELS[guild.id][source_channel]
            await channel.send(f"**ERROR**\n> '**{source_channel}**' is already a source channel")
            return
        except: pass

        # actual command bit
        await channel.send(embed=discord.Embed(
            title="setup gallery",
            description=f" source: '**{source}**'\n destination: '**{destination}**'"))
        try: GALLERY_CHANNELS[guild.id][source_channel] = destination_channel
        except: 
            GALLERY_CHANNELS[guild.id] = {}
            GALLERY_CHANNELS[guild.id][source_channel] = destination_channel
        PIECE_IDS[guild.id] = {}
        PIECE_IDS[guild.id][destination.id] = {'previous':0, 'last img':None}
        await update_dotenv('PIECE_IDS', PIECE_IDS)
        await update_dotenv('GALLERY_CHANNELS', GALLERY_CHANNELS)

    async def destroy(self, args, channel):
        source = args[0]
        try:
            channel_lookup = {channel.name:channel for channel in channel.guild.channels}
            destination = channel_lookup[GALLERY_CHANNELS[channel.guild.id][source]]
        except:
            print(sys.exc_info())
            await channel.send(f"**ERROR**\n '**{source}**' doesn't exist")
            return
        try:
            await channel.send(embed=discord.Embed(title="gallery destroyed", description=f"> source: '**{source}**'"))
            del GALLERY_CHANNELS[channel.guild.id][source]
            del PIECE_IDS[channel.guild.id][destination.id]
            await update_dotenv('GALLERY_CHANNELS', GALLERY_CHANNELS)
        except:
            print(sys.exc_info())
            await channel.send(f"**ERROR**\n> '**{source}**' not a valid source channel")

    async def run_command(self, command, args, channel):
        args = args.split(" ")
        #try: 
        #try: 
        await self.commands[command](args, channel)
        #except: await self.commands[command]()
        #except:
        #    await channel.send(f"**ERROR**\n> '**{command}**' not a valid command")

    async def get_reaction(self, msg, usr):
        start_time = time.time()
        await asyncio.sleep(1)
        cached_msg = discord.utils.get(client.cached_messages, id=msg.id)
        while True:
            await asyncio.sleep(1)
            reactions = {reaction.emoji:reaction for reaction in cached_msg.reactions}
            print(reactions)
            if reactions["\N{THUMBS UP SIGN}"].count > 1:
                async for user in reactions["\N{THUMBS UP SIGN}"].users():
                    if user is usr:
                        channel_lookup = {channel.name:channel for channel in msg.channel.guild.channels}
                        destination = channel_lookup[GALLERY_CHANNELS[msg.channel.guild.id][msg.channel.name]]
                        await msg.edit(content="adding...", embed=None)
                        await msg.clear_reactions()
                        await asyncio.sleep(1)
                        return destination
                    else:
                        if not user is client.user:
                            await reactions["\N{THUMBS UP SIGN}"].remove(user)
            elif reactions["\N{THUMBS DOWN SIGN}"].count > 1:
                async for user in reactions["\N{THUMBS DOWN SIGN}"].users():
                    if user is usr:
                        return
                    else:
                        if not user is client.user:
                            await reactions["\N{THUMBS UP SIGN}"].remove(user)

            if time.time() - start_time > 10:
                await msg.edit(content=":boom:\ntimeout", embed=None)
                await msg.clear_reactions()
                await asyncio.sleep(1)
                return

    async def catchup(self, args, channel):
        try: 
            auto = args[0]
            if auto == "verify": auto = False
            else: raise Exception
        except: auto = True

        try:
            number = args[1]
            number = int(number)
            if number > 1000:
                number = 1000
        except: number = 100

        toPrint = ""
        start = time.time()
        messages = await channel.history(limit=number).flatten()
        channel_lookup = {channel.name:channel for channel in channel.guild.channels}
        destination = channel_lookup[GALLERY_CHANNELS[channel.guild.id][channel.name]]
        last_message_id = PIECE_IDS[channel.guild.id][destination.id]['last img']
        messages_to_process = []
        for message in messages:
            if message.id == last_message_id:
                break
            else:
                messages_to_process.append(message)
        messages_to_process.reverse()
        for message in messages_to_process:
            await self.process_message(message, verify=(not auto))
        to_delete = await channel.send(f"`gallery.catchup(auto={auto})`\n`took {round(time.time()-start, 4)}s`")
        await asyncio.sleep(1)
        await to_delete.delete()
        

    async def change_settings(self, args, channel):
        try: setting = args[0]
        except: setting = "nothing_given"
        if setting not in self.settings:
            await channel.send(f"**ERROR**\n> '**{setting}**' not a valid setting")
        
        if "date_format" in setting:
            date_format = args[1].replace(" ", "").split("-")
            try:
                date_format[date_format.index("YYYY")] = "year"
                date_format[date_format.index("MM")] = "month"
                date_format[date_format.index("DD")] = "day"
            except:
                await channel.send(f"**ERROR**\n> '**{args[1]}**' not a valid format, try something more like: YYYY-MM-DD")
            try: CUSTOM_SETTINGS[channel.guild.id]['date'] = date_format
            except: 
                CUSTOM_SETTINGS[channel.guild.id] = {}
                CUSTOM_SETTINGS[channel.guild.id]['date'] = date_format
            await channel.send(f"updated date_format to '{date_format}'")
        
        if "default_title" in setting:
            newTitle = args[1]
            newTitle = newTitle.replace("\-", chr(8869)).replace("-", " ").replace(chr(8869), "-")
            try: CUSTOM_SETTINGS[channel.guild.id]['title'] = newTitle
            except: 
                CUSTOM_SETTINGS[channel.guild.id] = {}
                CUSTOM_SETTINGS[channel.guild.id]['title'] = newTitle
            await channel.send(f"updated default_title to '{newTitle}'")

        if "max_title_length" in setting:
            newTitleLength = int(args[1])
            try: CUSTOM_SETTINGS[channel.guild.id]['title length'] = newTitleLength
            except: 
                CUSTOM_SETTINGS[channel.guild.id] = {}
                CUSTOM_SETTINGS[channel.guild.id]['title length'] = newTitleLength
            await channel.send(f"updated max_title_length to '{newTitleLength}'")
        
        await update_dotenv('CUSTOM_SETTINGS', CUSTOM_SETTINGS)

    def get_date_str(self, message):
        date = datetime.date.today()
        date = date.__str__()
        date_info = {'year':date[:4], 'month':date[5:7], 'day':date[8:10]}
        try: date_format = CUSTOM_SETTINGS[message.channel.guild.id]['date']
        except: date_format = ['year', 'month', 'day']
        return f"{date_info[date_format[0]]}-{date_info[date_format[1]]}-{date_info[date_format[2]]}"

    def generate_id(self, guildID, channelID):
        PIECE_IDS[guildID][channelID]['previous'] += 1
        return str(PIECE_IDS[guildID][channelID]['previous'])

    async def process_message(self, message, verify=True):
        guildID = message.channel.guild.id
        try: title = CUSTOM_SETTINGS[guildID]['title']
        except: title = "untitled"
        destination = None

        for embed in message.embeds:
            
            
            qEmbed = discord.Embed(title="Add to gallery?", description=f":thumbsup: | yes\n\n:thumbsdown: | no")
            # if has video
            if not (not embed.video): # not (not empty) -> not (not false) -> False 
                print(f"embed.video: {not embed.video}")
                videourl = embed.video.url
                imageurl = None
                qEmbed.set_thumbnail(url="https://i.imgur.com/YEbSf8n.png")#here
            else:
                imageurl = embed.image.url
                qEmbed = discord.Embed(title="Add to gallery?", description=f":thumbsup: | yes\n\n:thumbsdown: | no")
                print(imageurl, not imageurl)
                if not (not imageurl):
                    qEmbed.set_thumbnail(url=imageurl)
                else:
                    imageurl = embed.thumbnail.url
                    qEmbed.set_thumbnail(url=imageurl)
                    if not imageurl:
                        break


            if verify:
                askmsg = await message.channel.send(embed=qEmbed)
                await askmsg.add_reaction(emoji="\N{THUMBS UP SIGN}")
                await askmsg.add_reaction(emoji="\N{THUMBS DOWN SIGN}")
                destination = await gallery.get_reaction(askmsg, message.author)
            else: 
                channel_lookup = {channel.name:channel for channel in message.channel.guild.channels}
                destination = channel_lookup[GALLERY_CHANNELS[message.channel.guild.id][message.channel.name]]


        for attachment in message.attachments:
            
            qEmbed = discord.Embed(title="Add to gallery?", description=f"**error**\n:thumbsup: | yes\ :thumbsdown: | no")

            has_video = False
            for extension in [".webm", ".mkv", ".avi", ".wmv", ".mov", ".mp4", ".mpeg", ".mpeg", ".m4v", ".svi", ".flv"]:
                if extension in attachment.url:
                    has_video = True
                    print(f"has video")

            if has_video:
                videourl = attachment.url
                imageurl = None
                qEmbed.set_thumbnail(url="https://i.imgur.com/YEbSf8n.png")#here

            elif type(attachment.width) is int:
                imageurl = attachment.url
                qEmbed.set_thumbnail(url=imageurl)
            
            if type(attachment.width) is int:
                if verify:
                    askmsg = await message.channel.send(embed=qEmbed)
                    await askmsg.add_reaction(emoji="\N{THUMBS UP SIGN}")
                    await askmsg.add_reaction(emoji="\N{THUMBS DOWN SIGN}")
                    destination = await gallery.get_reaction(askmsg, message.author)
                else: 
                    channel_lookup = {channel.name:channel for channel in message.channel.guild.channels}
                    destination = channel_lookup[GALLERY_CHANNELS[message.channel.guild.id][message.channel.name]]

        if destination != None:
            # make the embed
            try: 
                title = message.content.replace("\n", " ").split(" ")
                for part in title:
                    if "http" in part:
                        title.remove(part)
                title = ' '.join(title)
                if title.replace(" ", "") == "":
                    try: title = CUSTOM_SETTINGS[guildID]['title']
                    except: title = "untitled"
                qEmbed.description=f"**{title}**\n:thumbsup: | yes\ :thumbsdown: | no"
            except: pass
            try: titleLength = CUSTOM_SETTINGS['title length']
            except: titleLength = 30
            if len(title) > titleLength: title = title[:titleLength + 1]

            piece_id = gallery.generate_id(guildID, destination.id)
            resultEmbed = discord.Embed(title=f"{title}", description=f"{gallery.get_date_str(message)} | id: `{piece_id}`")
            resultEmbed.set_author(
                name=f"{message.author.name}",
                icon_url=message.author.avatar_url)
            if imageurl != None: resultEmbed.set_image(url=imageurl)
            else:
                resultEmbed.set_thumbnail(url="https://i.imgur.com/YEbSf8n.png")
                resultEmbed.add_field(name="video link", value=videourl)
            
            gallery_msg = await destination.send(embed=resultEmbed)
            PIECE_IDS[guildID][destination.id][piece_id] = {'msg id': gallery_msg.id, 'usr id': message.author.id}
            PIECE_IDS[guildID][destination.id]['last img'] = message.id
            await update_dotenv('PIECE_IDS', PIECE_IDS)
            

        try: await askmsg.delete()
        except: pass


    async def modify(self, args, channel):
        #get msgr
        last_msgs = await channel.history(limit=5).flatten()
        last_msg = None
        msgr = None
        for msg in last_msgs:
            if msg.author != client.user:
                msgr = msg.author
                last_msg = msg
                break
        if msgr == None:
            await channel.send(f"**ERROR**\n> something went wrong...")
            return

        piece_id = args[0]
        try: 
            destination_channel_name = GALLERY_CHANNELS[channel.guild.id][channel.name]
            channel_lookup = {channel.name:channel for channel in channel.guild.channels}
            destination_channel = channel_lookup[destination_channel_name]
            print(destination_channel.id)
            to_modify = await destination_channel.fetch_message(PIECE_IDS[channel.guild.id][destination_channel.id][piece_id]['msg id'])
        except: 
            print(sys.exc_info())
            await channel.send(f"**ERROR**\n> no id entered, or the id does not exist")
            return
        is_admin = channel.permissions_for(msgr)
        print(is_admin)
        if PIECE_IDS[channel.guild.id][to_modify.channel.id][piece_id]['usr id'] != msgr.id:
            await channel.send(f"**ERROR**\n> you can't edit someone elses post!")
            return
        
        howto_msg = None
        modify_description="""
        **gallery.delete**
        deletes the gallery entry

        **gallery.title** 
        changes the title of the gallery entry
        __Example__: **gallery.title New Title** 

        **gallery.cancel**
        cancels operation
        typing anything other than these commands (in this channel) also cancels
        this message will time out in 20 seconds
        """
        modifyEmbed = discord.Embed(description=modify_description)
        howto_msg = await channel.send(embed=modifyEmbed)

        start_time = time.time()
        while True:
            await asyncio.sleep(0.5)
            msg = discord.utils.get(await channel.history(limit=3).flatten(), author=msgr)
            if last_msg.id == msg.id:
                pass
            else:
                print(last_msg.id, msg.id)

                if msg.content == "gallery.delete":
                    await howto_msg.delete()
                    await to_modify.delete()
                    await channel.send(f"deleted gallery entry with id: `{piece_id}`")
                    return

                elif "gallery.title " in msg.content:
                    newTitle = msg.content.replace("gallery.title ", "")
                    original_embed = to_modify.embeds[0]
                    original_embed.title = newTitle
                    await channel.send(f"changed title of gallery entry with id: `{piece_id}` to '{newTitle}'")
                    await to_modify.edit(embed=original_embed)
                    await howto_msg.delete()
                    return

                else:
                    await howto_msg.edit(content=":boom:\ncancelled", embed=None)
                    await asyncio.sleep(1)
                    await howto_msg.delete()
                    return

            if time.time() - start_time > 20:
                await howto_msg.edit(content=":boom:\ntimeout", embed=None)
                await asyncio.sleep(1)
                await howto_msg.delete()
                return

            


gallery = Gallery()

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    strippedMsg = message.content.replace("`", "")
    strippedMsg += " "
    guildID = message.channel.guild.id

    if "gallery.help" in strippedMsg:
        HELP_EMBED.set_author(
            name=f"Help Page",
            icon_url=client.user.avatar_url)
        await message.channel.send(embed=HELP_EMBED)

    elif "gallery.advanced_help" in strippedMsg:
        await message.channel.send(embed=ADVANCED_HELP_EMBED)
    
    # if bot is mentioned
    elif client.user in message.mentions:
        await message.channel.send(":face_with_symbols_over_mouth: **don't ping me!!**\nTo get list of commands type `gallery.help`")

    elif strippedMsg[:len("gallery.")] == "gallery.":
        command = strippedMsg[len("gallery."):strippedMsg.index(" ")]
        args = strippedMsg[strippedMsg.index(" ")+1:]
        await gallery.run_command(command, args, message.channel)

    
    elif message.channel.name in GALLERY_CHANNELS[guildID].keys():
        #check for image embed
        
        await gallery.process_message(message)



@client.event
async def on_disconnect():
    await update_dotenv('GALLERY_CHANNELS', GALLERY_CHANNELS)


@client.event
async def on_ready():
    for guild in client.guilds:
        guild_roles = guild.roles
        guild_rolenames = [role.name for role in guild_roles]
        if 'gallery admin' not in guild_rolenames:
            await guild.create_role(name='gallery admin')

client.run(TOKEN)

