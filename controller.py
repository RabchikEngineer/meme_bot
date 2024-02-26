import asyncio
import os.path

from auxiliary import config_path, get_sender_names
from profiles import UserDict
import json, time


with open(config_path, encoding='utf-8') as f:
    conf = json.load(f)





class MainController:

    users = UserDict()
    client = None
    logger = None

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
        final_filename, ex_time = self.user.gifmaker.make_gif(filename)
        await self.event.respond(conf["answers"]["done"])
        # await client.send_file(sender['id'], final_filename)
        self.logger.log("GIF", get_sender_names(self.sender) + f' --- {time.strftime("%Mm %Ss", time.localtime(ex_time))}')
        await self.event.respond(file=await self.client.upload_file(final_filename))





