#!/bin/python3

# Libs
import json
import time
import asyncio
import os, sys

from loguru import logger
from telethon import TelegramClient, events
from square_memes_script import make_picture
from video_script import create_video

# Variables
config_path = 'config.json'

# Read config
with open(config_path, encoding='utf-8') as f:
    conf = json.load(f)

log_format='<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | {message}'
logger.level("TEXT", no=7, color="<blue>", icon="T")
logger.level("PIC", no=8, color="<cyan>", icon="P")
logger.level("COM", no=11, color="<yellow>", icon="C")
logger.remove()
logger.add(conf["log_filename"], level=2, format=log_format)
logger.add(sys.stdout, level=2, format=log_format)

def get_file_extension(mime_type):
    extension=None
    type_list=mime_type.split('/') # image/jpeg image/webp video/mp4 application/x-tgsticker
    if type_list[0]=='image':
        extension='.jpg'
    if type_list[0]=='video':
        extension='.mp4'
    return extension


async def bot():
    async with TelegramClient('bot', conf['app_id'], conf['app_hash']) as tgclient:
        await tgclient.start()
        # print('We have logged in as',(await tgclient.get_me()).username)
        logger.success('We have logged in as {username}',username=(await tgclient.get_me()).username)

        @tgclient.on(events.NewMessage(pattern='/'))
        async def handler(event):
            sender = (await event.get_sender()).to_dict()
            ans=conf["answers"].get(event.message.message[1:])
            if not ans:
                ans=conf["answers"]["wrong_command"]+conf["answers"]["reminder"]
            logger.log("COM", f'{sender.get("username")} {sender.get("first_name")} {sender.get("last_name")} --- ' +
                       event.message.message)
            await event.respond(ans)

        @tgclient.on(events.NewMessage(pattern='^(?!\/)'))
        async def handler(event):
            message=event.message
            sender = (await event.get_sender()).to_dict()
            if message.media:
                await event.respond(conf["answers"]["wait"])
                # print(event.message)
                sender_id = message.peer_id.user_id
                time_now = time.time()
                file_extension=get_file_extension(event.message.file.mime_type)
                if file_extension:
                    logger.log("PIC",f'{sender.get("username")} {sender.get("first_name")} {sender.get("last_name")} --- '+
                               (message.message.replace("\n\n", " ⮓⮓ ").replace("\n", " ⮓ ") if message.message!="" else "<Nothing>"))
                    filename = f'pictures/' \
                               f'{sender.get("username")} {sender.get("first_name")} {sender.get("last_name")} ' \
                               f'{time.strftime("%d-%m-%Y-%H-%M-%S", time.localtime(time_now))}{file_extension}'
                    # await tgclient.download_media(event.message.media, file=filename)
                    await message.download_media(filename)
                    final_file = make_picture(message.message, filename)
                    await event.respond(conf["answers"]["done"]+(conf["answers"]["reminder"] if not message.message else ""))
                    await tgclient.send_file(sender_id, final_file)
                    # await choise_list(event)
                else:
                    await event.respond(conf["answers"]["filetype_error"])
                    # cond='choice'
            else:
                logger.log("TEXT", f'{sender.get("username")} {sender.get("first_name")} {sender.get("last_name")} --- '+
                           message.message)
                await event.respond(conf["answers"]["no_text_message"]+conf["answers"]["reminder"])

        await tgclient.run_until_disconnected()


# User(id=1124695321, is_self=False, contact=False, mutual_contact=False, deleted=False, bot=False, bot_chat_history=False, bot_nochats=False, verified=False, restricted=False, min=False, bot_inline_geo=False, support=False, scam=False, apply_min_photo=True, fake=False, access_hash=-1546900081710505395, first_name='Валерий', last_name='Рябченко', username='rabchik_engineer', phone=None, photo=UserProfilePhoto(photo_id=5397880207618193497, dc_id=2, has_video=False, stripped_thumb=None), status=UserStatusRecently(), bot_info_version=None, restriction_reason=[], bot_inline_placeholder=None, lang_code='ru')

try:
    asyncio.run(bot())
except KeyboardInterrupt:
    print('Остановка программы...')
