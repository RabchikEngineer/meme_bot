#!/bin/python3

# Libs
import json
import time
import asyncio
import queue
import os, sys, importlib

from loguru import logger
from telethon import TelegramClient, events, Button
# from square_memes_script import PicMaker
from profiles import User,UserDict
from video_script import create_video
from auxiliary import config_path, MimeChecker, get_sender_names
import auxiliary as aux
from controller import MainController
import threading as th


def event_filter(event):
    return event.is_private


def buttons_from_dict(dct):
    return [[Button.inline(text,data)] for text,data in dct.items()]


def progress_callback(current, total):
    print('Downloaded', current, 'out of', total,
          'bytes: {:.2%}'.format(current / total))


async def settings_page(msg,user,text=''):
    await msg.edit(conf["answers"]["settings"] + user.get_stats() + text, buttons=
                   buttons_from_dict(conf["buttons"]["settings"]))


async def bot(client):
    # await client.start()
    # print(await client.get_me())
    # print('We have logged in as',(await client.get_me()).username)
    logger.success('We have logged in as {username}',username=(await client.get_me()).username)
    await client.send_message(conf["admin_id"], 'Bot started')

    @client.on(events.NewMessage(pattern='/',func=event_filter))
    async def handler(event):
        logger.trace(f'Command request')

        sender = (await event.get_sender()).to_dict()
        user = users.get_or_create(sender)

        ans=conf["answers"].get(event.message.message[1:],"")
        act=conf["actions"].get(event.message.message[1:],"")
        buttons=None
        file=None
        if act:
            if act=="0":
                users.load(users_ids)
            elif act=="1":
                user.reload(from_config=True)
            elif act=="2":
                ans+=user.get_stats()
                buttons=buttons_from_dict(conf["buttons"]["settings"])
            # await client.send_message(sender['id'],"some text",)
            elif act=="3":
                users.save()
            elif act=="4":
                user.save()
            elif act=="5":
                buttons=[[Button.text("/example"),Button.text("/settings")],
                         [Button.text("/start"),Button.text("/clear_buttons")]]
            elif act=="6":
                # print(dir(event))
                # print(dir(client))
                file=await client.upload_file(conf['example_file'])
                # event.reply(client.File())
            elif act=="7":
                buttons=Button.clear()
        if act and not ans:
            ans = conf["answers"]["default"]
        if not (ans or act):
            ans=conf["answers"]["wrong_command"]+conf["answers"]["reminder"]
        logger.log("COM", f'{get_sender_names(sender)} --- ' +
                   event.message.message)
        await event.respond(ans,buttons=buttons,file=file)

    @client.on(events.CallbackQuery)
    async def callback(event):
        logger.trace(f'Inline request')
        sender = (await event.get_sender()).to_dict()
        user = users.get_or_create(sender)
        data=event.data.decode()
        com=data.split('/')
        msg = await event.get_message()
        # print(event.data)
        if com[0]=='m':
            if com[1]=='settings':
                await settings_page(msg,user)
        elif com[0]=='ch':

            if com[1]=='mode':
                user.mode=user_modes[user_modes.index(user.mode)+1 if user_modes.index(user.mode)<len(user_modes)-1 else 0]
                await settings_page(msg, user)
                await event.answer('Режим изменён на '+user.mode)

            elif com[1]=='font':
                await msg.edit("Выберите шрифт:",buttons=
                    [[Button.inline(text[:-4],"font/"+str(num))] for num,text in enumerate(fonts)]+to_settings)

            elif com[1]=='pic_res':
                await msg.edit("Выберите горизонтальное разрешение картинок в пикселях:", buttons=
                [[Button.inline(str(res), "pic_res/" + str(res))] for res in conf['allowed_resolutions']['pic']]+
                    to_settings)

            elif com[1]=='gif_res':
                await msg.edit("Выберите горизонтальное разрешение гифок в пикселях:", buttons=
                [[Button.inline(str(res), "gif_res/" + str(res))] for res in conf['allowed_resolutions']['gif']]+
                    to_settings)

            elif com[1]=='gif_fps':
                await msg.edit("Выберите FPS гифок:", buttons=
                [[Button.inline(str(res), "gif_fps/" + str(res))] for res in conf['allowed_fps']] +
                    to_settings)

            elif com[1]=='reset':
                user.reload(from_config=True,default_config=True)
                await settings_page(msg, user)
                await event.answer("Все настройки успешно сброшены:)")

        elif com[0]=='font':
            font = fonts[int(com[1])]
            user.set_font(font)
            await event.answer("Шрифт изменён на "+font[:-4])

        elif com[0]=='pic_res':
            user.set_pic_res(int(com[1]))
            await event.answer("Разрешение картинок изменено на " + com[1])

        elif com[0]=='gif_res':
            user.set_gif_res(int(com[1]))
            await event.answer("Разрешение гифок изменено на " + com[1])

        elif com[0]=='gif_fps':
            user.set_gif_fps(int(com[1]))
            await event.answer("FPS гифок изменён на " + com[1])

        logger.log("INL",get_sender_names(sender)+f' --- {com[0]:8} /  {com[1]:10}')
        await event.answer()

    @client.on(events.NewMessage(pattern=r'^(?!\/)',func=event_filter))
    async def handler(event):
        logger.trace(f'Non-command request')
        ctrl = await MainController.create(event)

        if ctrl.user.state == "idle":

            if ctrl.message.media:


                if ctrl.user.mode == "pic" and MimeChecker.is_image(ctrl.message.file):

                    await ctrl.pic_sequence()

                elif ctrl.user.mode == "gif" and MimeChecker.is_video(ctrl.message.file):

                    await ctrl.gif_sequence()

                else:
                    await event.respond(conf["answers"]["filetype_error"])

                # ctrl.user.state('idle')

            else:
                logger.log("TEXT", get_sender_names(ctrl.sender)+f' --- {ctrl.message.message}')
                await event.respond(conf["answers"]["no_image_message"]+conf["answers"]["reminder"])

        elif ctrl.user.state=="waiting_for_text":

            if ctrl.message.message:
                await ctrl.pic_sequence()
                ctrl.user.state.set('idle')

            else:
                await ctrl.event.respond(conf["answers"]["text_request"])

    while True:
        try:
            await client.run_until_disconnected()
        except ConnectionError:
            logger.error('Connection error')


if __name__=='__main__':
    # Variables
    user_modes = ['pic', 'gif']


    # Read config
    with open(config_path, encoding='utf-8') as f:
        conf = json.load(f)


    loop = asyncio.get_event_loop()
    asyncio.set_event_loop(loop)

    client=TelegramClient(conf['session_name'], conf['app_id'], conf['app_hash'],loop=loop)
    client.start()
    MainController.set_client(client)

    # client.loop.create_task(client.send_message('RabchikEngineer', 'hello'))

    users = UserDict()
    gif_queue = queue.Queue()
    users_ids = [int(x) for x in os.listdir(conf['directories']['users_configs']) if os.path.isfile(x)]
    fonts = os.listdir(conf["directories"]["fonts"])
    to_settings = [[Button.inline("Назад", "m/settings")]]

    log_format = '<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | {message}'
    logger.level("TEXT", no=22, color="<blue>", icon="T")
    logger.level("PIC", no=22, color="<cyan>", icon="P")
    logger.level("GIF", no=22, color="<cyan>", icon="G")
    logger.level("INL", no=22, color="<yellow>", icon="I")
    logger.level("COM", no=22, color="<yellow>", icon="C")
    logger.remove()
    logger.add(conf["log_filename"], level=2, format=log_format)
    logger.add(sys.stdout, level=10, format=log_format)

    MainController.set_logger(logger)
    MainController.set_users(users)
    MainController.set_queue(gif_queue)
    users.load(users_ids)

    gif_watchdog=th.Thread(target=MainController.gif_watchdog,args=(loop,),daemon=True)
    gif_watchdog.start()

    try:
        # loop.create_task(MainController.gif_watchdog())
        loop.create_task(bot(client))
        loop.run_forever()
    except KeyboardInterrupt:
        pass
    finally:
        print('Сохранение пользователей...')
        users.save()
        print('Остановка программы...')
        gif_queue.join()
        loop.run_until_complete(client.send_message(conf["admin_id"], 'Bot stopped...'))
        loop.close()
        logger.success('System stopped')
        print('Goodbye:)')

# User(id=1124695321, is_self=False, contact=False, mutual_contact=False, deleted=False, bot=False, bot_chat_history=False,
# bot_nochats=False, verified=False, restricted=False, min=False, bot_inline_geo=False, support=False, scam=False,
# apply_min_photo=True, fake=False, access_hash=-1546900081710505395,
# first_name='Валерий', last_name='Рябченко', username='rabchik_engineer', phone=None, photo=UserProfilePhoto(photo_id=5397880207618193497,
# dc_id=2, has_video=False, stripped_thumb=None), status=UserStatusRecently(), bot_info_version=None, restriction_reason=[],
# bot_inline_placeholder=None, lang_code='ru')


