#!/bin/python3

# Libs
import json
import time
import asyncio
import os, sys, importlib

from loguru import logger
from telethon import TelegramClient, events, Button
# from square_memes_script import PicMaker
from profiles import User,UserDict
from video_script import create_video
from auxiliary import config_path
import auxiliary as aux

# Variables
user_modes=['pic','gif']

# Read config
with open(config_path, encoding='utf-8') as f:
    conf = json.load(f)



users=UserDict()
users_ids=[int(x) for x in os.listdir(conf['directories']['pic_configs'])]
fonts=os.listdir(conf["directories"]["fonts"])

log_format='<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | {message}'
logger.level("TEXT", no=7, color="<blue>", icon="T")
logger.level("PIC", no=8, color="<cyan>", icon="P")
logger.level("COM", no=11, color="<yellow>", icon="C")
logger.level("INL", no=11, color="<yellow>", icon="I")
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


def get_sender_names(sender):
    return f'{sender.get("username")} {sender.get("first_name")} {sender.get("last_name")} --- '


def buttons_from_dict(dct):
    return [Button.inline(text,data) for text,data in dct.items()]


def progress_callback(current, total):
    print('Downloaded', current, 'out of', total,
          'bytes: {:.2%}'.format(current / total))


users.load(users_ids)


async def bot():
    async with TelegramClient('bot', conf['app_id'], conf['app_hash']) as client:
        await client.start()
        # print('We have logged in as',(await client.get_me()).username)
        logger.success('We have logged in as {username}',username=(await client.get_me()).username)

        @client.on(events.NewMessage(pattern='/'))
        async def handler(event):
            sender = (await event.get_sender()).to_dict()

            user = users.get_or_create(sender)
            # if not user:
            #     user = User(sender['id'])
            #     users.update({user.id:user})

            ans=conf["answers"].get(event.message.message[1:],"")
            act=conf["actions"].get(event.message.message[1:],"")
            buttons=None
            if act:
                if act=="0":
                    users.load(users_ids)
                if act=="1":
                    user.reload()
                if act=="2":
                    ans+=user.get_stats()
                    buttons=buttons_from_dict(conf["buttons"]["settings"])
                # await client.send_message(sender['id'],"some text",)
                if act=="3":
                    users.save()
                if act=="4":
                    user.save()
                if act=="5":
                    buttons=[[Button.text("/settings"),Button.text("/example")],
                             [Button.text("/start"),Button.text("А не придумал")]]
            if act and not ans:
                ans = conf["answers"]["default"]
            if not (ans or act):
                ans=conf["answers"]["wrong_command"]+conf["answers"]["reminder"]
            logger.log("COM", f'{sender.get("username")} {sender.get("first_name")} {sender.get("last_name")} --- ' +
                       event.message.message)
            await event.respond(ans,buttons=buttons)


        @client.on(events.CallbackQuery)
        async def callback(event):
            sender = (await event.get_sender()).to_dict()
            user = users.get_or_create(sender)
            data=event.data.decode()
            com=data.split('/')
            msg = await event.get_message()
            # print(event.data)
            if com[0]=='m':
                if com[1]=='settings':
                    await msg.edit(conf["answers"]["settings"]+user.get_stats(), buttons=
                                   buttons_from_dict(conf["buttons"]["settings"]))
            elif com[0]=='ch':
                if com[1]=='mode':
                    user.mode=user_modes[user_modes.index(user.mode)+1 if user_modes.index(user.mode)<len(user_modes)-1 else 0]
                    await msg.edit(conf["answers"]["settings"] + user.get_stats(), buttons=
                                   buttons_from_dict(conf["buttons"]["settings"]))
                    await event.answer('Режим изменён на '+user.mode)
                if com[1]=='font':
                    await msg.edit("Выберите шрифт:",buttons=
                        [[Button.inline(text,"f/"+str(data))] for data,text in enumerate(fonts)]+
                        [[Button.inline("Назад", "m/settings")]])
            elif com[0]=='f':
                font = fonts[int(com[1])]
                user.set_font(font)
                await event.answer("Шрифт изменён на "+font)

            logger.log("INL",get_sender_names(sender)+data)
            await event.answer()

        @client.on(events.NewMessage(pattern=r'^(?!\/)'))
        async def handler(event):
            message=event.message
            sender = (await event.get_sender()).to_dict()
            user = users.get_or_create(sender)

            if user.state=="idle":

                if message.media:

                    if user.mode == "pic":

                        await event.respond(conf["answers"]["wait"])
                        # print(event.message)
                        sender_id = sender['id']
                        time_now = time.time()
                        file_extension=get_file_extension(event.message.file.mime_type)
                        if file_extension:
                            logger.log("PIC",get_sender_names(sender)+
                                       (message.message.replace("\n\n", " ⮓⮓ ").replace("\n", " ⮓ ") if message.message!="" else "<Nothing>"))
                            filename = f'{conf["directories"]["pictures"]}' \
                                       f'{sender.get("username")} {sender.get("first_name")} {sender.get("last_name")} ' \
                                       f'{time.strftime("%d-%m-%Y-%H-%M-%S", time.localtime(time_now))}{file_extension}'
                            # await client.download_media(event.message.media, file=filename)
                            await message.download_media(filename)
                            final_filename = user.picmaker.make_picture(message.message, filename)
                            await event.respond(conf["answers"]["done"]+(conf["answers"]["reminder"] if not message.message else ""))
                            await client.send_file(sender_id, final_filename)
                        else:
                            await event.respond(conf["answers"]["filetype_error"])

                    elif user.mode == "gif":

                        # filename = f'{conf["directories"]["gif"]}' \
                        #            f'{sender["id"]}'
                        filename = f'{conf["directories"]["gif"]}' \
                                   f'{sender.get("username")} {sender.get("first_name")} {sender.get("last_name")} ' \
                                   f'{time.strftime("%d-%m-%Y-%H-%M-%S", time.localtime(time.time()))}'
                        # filename = await message.download_media(filename, progress_callback=progress_callback)
                        await event.respond(conf["answers"]["wait_long"])
                        filename = await message.download_media(filename)
                        final_filename=user.gifmaker.make_gif(filename)
                        await event.respond(conf["answers"]["done"])
                        await client.send_file(sender['id'], final_filename)

                else:
                    logger.log("TEXT", get_sender_names(sender)+
                               message.message)
                    await event.respond(conf["answers"]["no_text_message"]+conf["answers"]["reminder"])
            # elif user.state=="ch_font":

        await client.run_until_disconnected()


# User(id=1124695321, is_self=False, contact=False, mutual_contact=False, deleted=False, bot=False, bot_chat_history=False,
# bot_nochats=False, verified=False, restricted=False, min=False, bot_inline_geo=False, support=False, scam=False,
# apply_min_photo=True, fake=False, access_hash=-1546900081710505395,
# first_name='Валерий', last_name='Рябченко', username='rabchik_engineer', phone=None, photo=UserProfilePhoto(photo_id=5397880207618193497,
# dc_id=2, has_video=False, stripped_thumb=None), status=UserStatusRecently(), bot_info_version=None, restriction_reason=[],
# bot_inline_placeholder=None, lang_code='ru')

while True:
    try:
        asyncio.run(bot())
    except KeyboardInterrupt:
        print('Остановка программы...')
        users.save()
        break
    except ConnectionError:
        logger.error('Connection error')
