import asyncio

from modules.auxiliary import config_path, get_sender_names,pretty_file_size, GifQueue,ActiveThreads
import json, time
import threading as th
# from concurrent.futures import ThreadPoolExecutor

with open(config_path, encoding='utf-8') as f:
    conf = json.load(f)



class MainController:

    users = None
    client = None
    logger = None
    active_threads=ActiveThreads()
    queues = GifQueue()
    gif_overcount_lock = th.Lock()
    in_work = th.Lock()

    def __init__(self ,event):
        self.event = event
        self.message = event.message
        self.sender=None
        self.user=None

    @classmethod
    async def create(cls,event):
        self=MainController(event)
        self.sender = (await event.get_sender()).to_dict()
        self.user = self.users.get_or_create(self.sender)
        return self

    @classmethod
    def set_client(cls, client):
        cls.client = client

    @classmethod
    def set_logger(cls,logger):
        cls.logger = logger

    @classmethod
    def set_users(cls,users):
        cls.users = users

    # @classmethod
    # def set_queue(cls,queues.done_gif):
    #     cls.queues.done_gif = queues.done_gif

    @classmethod
    def gif_send_watchdog(cls,loop):
        cls.logger.success("GIF Send watchdog started")
        while True:
            res = cls.queues.done_gif.get()
            if res[1]=='gif_timeout':
                cls.logger.warning(f"GIF Timeout after {res[2]} seconds")
                asyncio.run_coroutine_threadsafe(
                    cls.respond(res[0],['GIF',conf["answers"]['gif_timeout'].format(res[2])]), loop)
                cls.queues.done_gif.task_done()
                continue
            cls.logger.info("Sending GIF...")
            asyncio.run_coroutine_threadsafe(cls.send_gif(*res),loop)
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



    

