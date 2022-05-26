#!/bin/python3

# Libs
import json
import datetime, time
import asyncio
import os

from telethon import TelegramClient, events
from square_memes_script import make_picture
from video_script import create_video

# Variables
config_path = 'bot_config.json'
presets_path = 'presets.json'
admin_list=['rabchik_engineer','shishka933','Timventor','vija_tyan']
# admin_list=[]

# Read config
with open(config_path, 'r') as f:
    conf = json.load(f)

with open(presets_path, 'r') as f:
    vid_presets = json.load(f)

cond = ''
choise = ''
pic_num=1

async def picture_req(event):
    global pic_num
    pic_num += 1
    await event.respond(f'Отправь фото {pic_num}')


async def choise_list(event):
    global cond
    sender = await event.get_sender()
    sender_dict = sender.to_dict()
    sender_username=sender_dict['username']
    if sender_username in admin_list:
        await event.respond('Выбери функцию:\n1 - Квадрат\n2 - Видосик')
    else:
        await event.respond('Выбери функцию:\n1 - Квадрат')
    cond = 'choise'

async def vid_presets_list(event):
    global cond
    await event.respond(f'Выберите шаблон из предложенных\n\n{get_pres_list(vid_presets)}\nили напишите 0 для того чтобы использовать свой вариант, или 1 чтобы выйти')
    cond = '2_1'

def get_pres_list(dict):
    msg = ''
    for i in dict.keys():
        msg += f'{i}\n'
    return msg


async def bot():
    async with TelegramClient('bot', conf['app_id'], conf['app_hash']) as tgclient:
        await tgclient.start()

        @tgclient.on(events.NewMessage(pattern='/start'))
        async def handler(event):
            await event.respond('Этот бот делает мемасики, для списка комманд пиши\n/commands')

        @tgclient.on(events.NewMessage(pattern='/commands'))
        async def handler(event):
            await choise_list(event)

        @tgclient.on(events.NewMessage())
        async def handler(event):
            if event.message.message != '/start' and event.message.message != '/commands':
                global cond
                global choise
                global pic_num

                if cond == 'choise':
                    cond = event.message.message
                    if not cond in ['1','2']:
                        print(cond)


                if cond == '1':
                    await event.respond('Кидай фотку с подписью')
                    cond = '1_1'
                elif cond == '1_1':
                    if event.message.media:
                        await event.respond('Секунду...')
                        sender_id = int(str(event.message.peer_id)[str(event.message.peer_id).find('=') + 1:-1])
                        time_now = time.time()
                        sender = await event.get_sender()
                        sender = sender.to_dict()
                        file_name = f'pictures/{sender.get("username")} {sender.get("first_name")} {sender.get("last_name")} {time_now}.jpg'
                        await tgclient.download_media(event.message.media, file=file_name)
                        with open('commands.log', 'a') as f:
                            f.write(str(datetime.datetime.today())[:-7] + ' ' + file_name + '\n')
                        final_file = make_picture(event.message.message, file_name)
                        await event.respond('Держи:)')
                        await tgclient.send_file(sender_id, final_file)
                        await choise_list(event)
                    else:
                        await event.respond('Я не принимаю сообщения без фоток')
                        await choise_list(event)
                elif cond == '2':
                    await vid_presets_list(event)
                elif cond == '2_1':
                    choise=event.message.message
                    if choise=='0':
                        pass
                    if choise=='1':
                        await choise_list(event)
                    else:
                        if not choise in vid_presets:
                            await vid_presets_list(event)
                        else:
                            cond='2_2'
                            pic_num=0
                            await picture_req(event)
                elif cond=='2_2':
                    if event.message.media:
                        path=f'videos/{vid_presets[choise]["folder"]}/{pic_num}.png'
                        print(path)
                        await tgclient.download_media(event.message,file=path)
                    if pic_num<len(vid_presets[choise]['vid_durations']):
                        await picture_req(event)
                    else:
                        await event.respond('Секунду...') #data = {'x': 400, 'y': 400, 'vid_durations': [3, 3, 3], 'folder': 'test_folder', 'audio_dipl': 0}
                        path=create_video(vid_presets[choise])
                        sender = await event.get_sender()
                        sender = sender.to_dict()
                        with open('commands.log', 'a') as f:
                            f.write(str(datetime.datetime.today())[:-7] + ' ' +f'{sender.get("username")} {sender.get("first_name")} {sender.get("last_name")} {time.time()}'+ path + '\n')
                        sender = await event.get_sender()
                        sender = sender.to_dict()
                        await event.respond('Держи:)')
                        await tgclient.send_file(sender['id'],path)
                        cond='choise'
                        await choise_list(event)
                else:
                    await event.respond('Неправильное сообщение')
                    await choise_list(event)

                #

        await tgclient.run_until_disconnected()


# User(id=1124695321, is_self=False, contact=False, mutual_contact=False, deleted=False, bot=False, bot_chat_history=False, bot_nochats=False, verified=False, restricted=False, min=False, bot_inline_geo=False, support=False, scam=False, apply_min_photo=True, fake=False, access_hash=-1546900081710505395, first_name='Валерий', last_name='Рябченко', username='rabchik_engineer', phone=None, photo=UserProfilePhoto(photo_id=5397880207618193497, dc_id=2, has_video=False, stripped_thumb=None), status=UserStatusRecently(), bot_info_version=None, restriction_reason=[], bot_inline_placeholder=None, lang_code='ru')

asyncio.run(bot())
