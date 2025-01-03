import pathlib,json,os,queue
import threading

config_path = 'config.json'

with open(config_path, encoding='utf-8') as f:
    conf = json.load(f)


def create_dir(path):
    pathlib.Path(path).mkdir(parents=True, exist_ok=True)


def create_dirs(paths):
    for path in paths:
        create_dir(path)


def pretty_file_size(filename):
    return round(os.path.getsize(filename)/1024**2,2)


def get_sender_names(sender):
    return f'{sender.get("username")} {sender.get("first_name")} {sender.get("last_name")}'


class MimeChecker:

    image_types = [['image'],['application/x-tgsticker']]
    video_types = [['video','gif'],[]]

    @classmethod
    def get_file_extension(cls,mime_type):
        if not isinstance(mime_type,str):
            mime_type = mime_type.mime_type
        extension = None
        type_list = mime_type.split('/')  # image/jpeg image/webp video/mp4 application/x-tgsticker
        if cls.is_image(mime_type):
            extension = '.jpg'
        if cls.is_video(mime_type):
            extension = '.mp4'
        return extension

    @classmethod
    def is_auto_acceptable(cls,mime_type):
        return cls.is_image(mime_type) or cls.is_video(mime_type)

    @classmethod
    def is_image(cls,mime_type):
        if not isinstance(mime_type,str):
            mime_type = mime_type.mime_type
        type_list=mime_type.split('/')
        return type_list[0] in cls.image_types[0] or mime_type in cls.image_types[1]

    @classmethod
    def is_video(cls,mime_type):
        if not isinstance(mime_type,str):
            mime_type = mime_type.mime_type
        type_list=mime_type.split('/')
        return type_list[0] in cls.video_types[0] or mime_type in cls.video_types[1]


class Queues:

    def __init__(self,names):
        for name in names:
            exec(f'self.{name}=None')

    def set(self,name,q):
        self.name=q


class GifQueue:
    req_gif=queue.Queue()
    done_gif=queue.Queue()


class ActiveThreads:
    n=0


    def __init__(self, lock: threading.Lock):
        self.in_work=lock

    def update_lock(self):
        if self.n>0:
            self.in_work.acquire()
        else:
            self.in_work.release()

    def wait_for_completion(self):
        self.in_work.acquire()
        self.in_work.release()

    def inc(self):
        self.n+=1
        self.update_lock()

    def dec(self):
        self.n-=1
        self.update_lock()

    def __gt__(self, other):
        return self.n>other

    def __lt__(self, other):
        return self.n<other

    def __eq__(self, other):
        return self.n==other



class ThreadWithStop(threading.Thread):

    def stop(self):
        raise SystemExit


def sigterm_handler(*args):
    raise KeyboardInterrupt


create_dirs(conf['directories'].values())
