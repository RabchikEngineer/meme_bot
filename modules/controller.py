import asyncio
import json, time
import threading as th

from loguru import logger
from telethon import TelegramClient, events, Button

from modules.auxiliary import config_path, get_sender_names,pretty_file_size, GifQueue,ActiveThreads, MimeChecker
from modules.profiles import UserDict, User
# from concurrent.futures import ThreadPoolExecutor

with open(config_path, encoding='utf-8') as f:
    conf = json.load(f)


class MainController:

    users: UserDict = None
    client: TelegramClient = None
    logger: logger = None
    active_threads=ActiveThreads(th.Lock())
    queues = GifQueue()
    gif_overcount_lock = th.Lock()

    def __init__(self, event):
        self.event: events.newmessage.NewMessage.Event = event
        self.message = event.message
        self.sender: dict = None
        self.user: User = None

    @classmethod
    async def create(cls, event):
        self=cls(event)
        self.sender = (await event.get_sender()).to_dict()
        self.user = self.users.get_or_create(self.sender)
        return self

    @classmethod
    async def restore(cls, new_ctrl):
        user = cls.users.get_or_create(new_ctrl.sender)
        event = user.saved_events.get(new_ctrl.event.message.id)
        self = MainController(event)
        self.sender = (await event.get_sender()).to_dict()
        self.user = user
        return self

    @classmethod
    def set_client(cls, client):
        cls.client = client

    @classmethod
    def set_logger(cls,logger):
        cls.logger = logger

    @classmethod
    def set_loop(cls,loop):
        cls.loop = loop

    @classmethod
    def set_users(cls,users):
        cls.users = users

    @classmethod
    def gif_send_watchdog(cls,loop):
        cls.logger.success("GIF Send watchdog started")
        while True:
            res = cls.queues.done_gif.get()
            print('get item')
            cls.logger.info("Sending GIF...")
            # asyncio.run_coroutine_threadsafe(cls.send_gif(*res),loop)
            future=asyncio.run_coroutine_threadsafe(cls.send_gif(*res),loop)
            print(future.result(),11)
            cls.queues.done_gif.task_done()

    @classmethod
    def gif_start_watchdog(cls,loop):
        cls.logger.success("GIF Start watchdog started")
        while True:
            cls.gif_overcount_lock.acquire()
            cls.gif_overcount_lock.release()
            gif_th = cls.queues.req_gif.get()
            gif_th.start()
            cls.logger.info("GIF Processing started")
            cls.queues.req_gif.task_done()

    @classmethod
    async def send_gif(cls, self, filename, ex_time):
        # await client.send_file(sender['id'], final_filename)
        file = await cls.client.upload_file(filename)
        await self.event.respond(conf["answers"]["done"]+f'\nРазмер: {pretty_file_size(filename)}Mb')
        await self.event.respond(file=file)
        cls.logger.log("GIF",get_sender_names(self.sender) +
                       f' --- done {time.strftime("%Mm %Ss", time.localtime(ex_time))}  {pretty_file_size(filename)}M')

    @classmethod
    async def respond(cls, self, message):
        await self.event.respond(message[1])
        cls.logger.log(message[0],get_sender_names(self.sender) + f' --- {message[1][:20]}')

    def save_event(self, message_id):
        self.user.saved_events.add(message_id,self.event)

    async def auto_sequence(self):


        buttons=[
            Button.inline('Картинку', 'choose_action/pic'),
            Button.inline('Гифку', 'choose_action/gif')
        ]
        if MimeChecker.is_image(self.message.file):
            buttons.pop(1)

        elif MimeChecker.is_video(self.message.file):
            buttons.pop(0)

        ans = await self.event.respond(conf['answers']['choose'],buttons=buttons)
        self.save_event(ans.id)

    async def pic_sequence(self):
        # file_extension=MimeChecker.get_file_extension(self.event.self.message.file)
        filename = f'{conf["directories"]["pictures"]}' \
                   f'{get_sender_names(self.sender)} ' \
                   f'{time.strftime("%d-%m-%Y-%H-%M-%S", time.localtime(time.time()))}'
        # await client.download_media(self.event.self.message.media, file=filename)
        filename= self.user.picmaker.saved_filename or await self.message.download_media(filename)
        self.user.picmaker.set_filename(None)

        if not self.message.message:
            self.user.picmaker.set_filename(filename)
            self.user.state.set("waiting_for_text")
            await self.event.respond(conf["answers"]["text_request"])
            return

        await self.event.respond(conf["answers"]["wait"])
        final_filename = self.user.picmaker.make_picture(self.message.message, filename)
        await self.event.respond(conf["answers"]["done"])  # +(conf["answers"]["reminder"] if not self.message.self.message else "")
        # await client.send_file(sender_id, final_filename)
        self.logger.log("PIC", get_sender_names(self.sender) + " --- " +
                        (self.message.message.replace("\n\n", " ⮓⮓ ").
                        replace("\n"," ⮓ ") if self.message.message != "" else "<Nothing>"))
        await self.event.respond(file=await self.client.upload_file(final_filename))

    async def gif_sequence(self):
        filename = f'{conf["directories"]["gif"]}' \
                   f'{get_sender_names(self.sender)} ' \
                   f'{time.strftime("%d-%m-%Y-%H-%M-%S", time.localtime(time.time()))}'
        # filename = await self.message.download_media(filename, progress_callback=progress_callback)
        await self.event.respond(conf["answers"]["wait_long"])
        filename = await self.message.download_media(filename)
        # final_filename, ex_time = self.user.gifmaker.make_gif(filename)
        gif_th=th.Thread(target=self.user.gifmaker.make_gif, args=(self, self.queues.done_gif, filename))
        # gif_th.start()
        self.queues.req_gif.put(gif_th)
        self.logger.log("GIF", get_sender_names(self.sender) +
                        f' --- start {self.user.gifmaker.resolution}x{self.user.gifmaker.fps}  '
                        f'{pretty_file_size(filename)}M')
        # self.client.loop.create_task(self.user.gifmaker.make_gif(self, self.queues.done_gif, filename))
        # with ThreadPoolExecutor() as pool:
        # final_filename, ex_time = await self.client.loop.run_in_executor(pool,self.user.gifmaker.make_gif_old)
        # print(final_filename, ex_time)



    

