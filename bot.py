#!/bin/python3

import json
import asyncio
import os, sys
import signal

from loguru import logger
from telethon import TelegramClient, events, Button
from modules.profiles import UserDict
# from video_script import create_video
from modules.auxiliary import config_path, MimeChecker, get_sender_names, sigterm_handler
# import auxiliary as aux
from modules.controller import MainController
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
    await client.start()
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
                file=await client.upload_file(conf['example_file'])
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
        event.message=(await event.get_message()).message
        ctrl : MainController = await MainController.create(event)
        user=ctrl.user
        data=event.data.decode()
        com=data.split('/')
        msg = ctrl.message

        match com[0]:
            case 'm':

                match com[1]:

                    case 'settings':
                        await settings_page(msg,user)

            case 'ch':

                match com[1]:

                    case 'mode':
                        user.mode=user_modes[user_modes.index(user.mode)+1 if user_modes.index(user.mode)<len(user_modes)-1 else 0]
                        await settings_page(msg, user)
                        await event.answer('Режим изменён на '+conf['modes'][user.mode])

                    case 'font':
                        await msg.edit("Выберите шрифт:",buttons=
                            [[Button.inline(text[:-4],"font/"+str(num))] for num,text in enumerate(fonts)]+to_settings)

                    case 'pic_res':
                        await msg.edit("Выберите горизонтальное разрешение картинок в пикселях:", buttons=
                        [[Button.inline(str(res), "pic_res/" + str(res))] for res in conf['allowed_resolutions']['pic']]+
                            to_settings)

                    case 'gif_res':
                        await msg.edit("Выберите горизонтальное разрешение гифок в пикселях:", buttons=
                        [[Button.inline(str(res), "gif_res/" + str(res))] for res in conf['allowed_resolutions']['gif']]+
                            to_settings)

                    case 'gif_fps':
                        await msg.edit("Выберите FPS гифок:", buttons=
                        [[Button.inline(str(res), "gif_fps/" + str(res))] for res in conf['allowed_fps']] +
                            to_settings)

                    case 'reset':
                        user.reload(from_config=True,default_config=True)
                        await settings_page(msg, user)
                        await event.answer("Все настройки успешно сброшены:)")

            case 'choose_action':
                ctrl1 = await ctrl.restore(ctrl.sender)
                match com[1]:

                    case 'pic':
                        logger.trace(f'{ctrl1.sender['username']} choosed pic')
                        # await event.edit("Ты выбрал сделать пикчу")
                        await event.delete()
                        await ctrl1.pic_sequence()

                    case 'gif':
                        logger.trace(f'{ctrl1.sender['username']} gif')
                        await event.delete()
                        await ctrl1.gif_sequence()

            case 'font':
                font = fonts[int(com[1])]
                user.set_font(font)
                await event.answer("Шрифт изменён на "+font[:-4])

            case 'pic_res':
                user.set_pic_res(int(com[1]))
                await event.answer("Разрешение картинок изменено на " + com[1])

            case 'gif_res':
                user.set_gif_res(int(com[1]))
                await event.answer("Разрешение гифок изменено на " + com[1])

            case 'gif_fps':
                user.set_gif_fps(int(com[1]))
                await event.answer("FPS гифок изменён на " + com[1])

        logger.log("INL",get_sender_names(sender)+f' --- {com[0]:8} /  {com[1]:10}')
        await event.answer()

    @client.on(events.NewMessage(pattern=r'^(?!\/)',func=event_filter))
    async def handler(event):
        logger.trace(f'Non-command request')
        ctrl : MainController = await MainController.create(event)

        match ctrl.user.state:

            case "idle":

                if ctrl.message.media:

                    if ctrl.user.mode == "auto" and MimeChecker.is_auto_acceptable(ctrl.message.file):

                        await ctrl.auto_sequence()

                    elif ctrl.user.mode == "pic" and MimeChecker.is_image(ctrl.message.file):

                        await ctrl.pic_sequence()

                    elif ctrl.user.mode == "gif" and MimeChecker.is_video(ctrl.message.file):

                        await ctrl.gif_sequence()

                    else:
                        await event.respond(conf["answers"]["filetype_error"])

                else:
                    logger.log("TEXT", get_sender_names(ctrl.sender)+f' --- {ctrl.message.message}')
                    await event.respond(conf["answers"]["no_image_message"]+conf["answers"]["reminder"])

            case "waiting_for_text":

                if ctrl.message.message:
                    ctrl.user.state.set('idle')
                    await ctrl.pic_sequence()

                else:
                    await ctrl.event.respond(conf["answers"]["text_request"])


    await client.run_until_disconnected()


if __name__=='__main__':
    # Read config
    with open(config_path, encoding='utf-8') as f:
        conf = json.load(f)

    user_modes = conf['modes'].values()

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    client=TelegramClient(conf["directories"]["sessions"]+conf['session_name'], conf['app_id'], conf['app_hash'],loop=loop)
    MainController.set_client(client)

    # client.loop.create_task(client.send_message('RabchikEngineer', 'hello'))

    users = UserDict()
    users_ids = [int(x) for x in os.listdir(conf['directories']['user_configs']) if os.path.isfile(x)]
    fonts = sorted(os.listdir(conf["directories"]["fonts"]))
    to_settings = [[Button.inline("Назад", "m/settings")]]

    log_format = '<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | {message}'
    logger.level("TEXT", no=22, color="<blue>", icon="T")
    logger.level("PIC", no=22, color="<cyan>", icon="P")
    logger.level("GIF", no=22, color="<cyan>", icon="G")
    logger.level("INL", no=22, color="<yellow>", icon="I")
    logger.level("COM", no=22, color="<yellow>", icon="C")
    logger.remove()
    # logger.add(conf["log_filename"], level=2, format=log_format)
    logger.add(sys.stdout, level=10, format=log_format)

    MainController.set_logger(logger)
    MainController.set_users(users)
    MainController.set_loop(loop)
    users.load(users_ids)

    gif_send_watchdog=th.Thread(target=MainController.gif_send_watchdog,args=(loop,),daemon=True)
    gif_send_watchdog.start()

    gif_start_watchdog=th.Thread(target=MainController.gif_start_watchdog,args=(loop,),daemon=True)
    gif_start_watchdog.start()

    signal.signal(signal.SIGTERM, sigterm_handler)

    try:
        # loop.create_task(MainController.gif_watchdog())
        loop.run_until_complete(asyncio.gather(bot(client)))
        # loop.run_forever()

    except KeyboardInterrupt:
        pass
    except ConnectionError:
        logger.info('Saving users...')
        users.save()
        logger.success('Users saved successfully')
        logger.error('Connection error')
    finally:
        logger.info('Waiting for modules...')
        MainController.queues.req_gif.join()
        MainController.queues.done_gif.join()
        logger.success("Modules stop")
        logger.info('Saving users...')
        users.save()
        logger.success('Users saved successfully')

        try:
            loop.run_until_complete(client.send_message(conf["admin_id"], 'Bot stopped...'))
        except ConnectionError:
            pass
        loop.close()
        logger.success('System stopped')
        print('Goodbye:)')


