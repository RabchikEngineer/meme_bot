from auxiliary import config_path
import json, os
from square_memes_script import PicMaker
from gif_script import GifMaker


with open(config_path, encoding='utf-8') as f:
    conf = json.load(f)

users_configs_dir = conf['directories']['users_configs']
# pic_configs_dir = conf['directories']['pic_configs']


class User:

    def __init__(self, user_id):
        self.state = UserState('idle')
        self.id = user_id
        self.config, is_new = self._load_config()
        self.picmaker = self._create_picmaker()
        self.gifmaker = self._create_gifmaker()
        self.mode = self.config['mode']
        self.info = self.config['info']

    def reload(self,from_config=False, default_config=False):
        if from_config:
            self.config, _ = self._load_config(default_config)
            self.mode = self.config['mode']
        self.picmaker = self._create_picmaker()
        self.gifmaker = self._create_gifmaker()

    def save(self):
        filename=users_configs_dir + str(self.id)
        self.config['info'] = self.info
        self.config['mode'] = self.mode
        with open(filename, 'w',encoding='utf-8') as f:
            json.dump(self.config,f,indent=2,ensure_ascii=False)

    def set_info(self,sender):
        self.info = self._create_info(sender)

    def set_font(self,font):
        self.config['pic']['font']=font
        self.reload()

    def set_pic_res(self,res):
        self.config['pic']['sizes']['resolution']=res
        self.reload()

    def set_gif_res(self,res):
        self.config['gif']['resolution']=res
        self.reload()

    def set_gif_fps(self,fps):
        self.config['gif']['fps']=fps
        self.reload()

    def get_stats(self):
        return f'\nТекущий режим: {self.mode}\nТекущий шрифт: {self.config["pic"]["font"][:-4]}\n'+\
                'Разрешения:\n    '+\
                f'Картинок - {self.config["pic"]["sizes"]["resolution"]}\n    '+\
                f'Гифок: - {self.config["gif"]["resolution"]}\n'+\
                f'FPS гифок - {self.config["gif"]["fps"]}\n'

    def _load_config(self,default=False):
        filename=users_configs_dir + str(self.id)
        with open((filename if os.path.exists(filename) else conf["default_user_config"])
                  if not default else conf["default_user_config"],encoding='utf-8') as f:
            return json.load(f), os.path.exists(filename)

    def _create_picmaker(self):
        return PicMaker(self.config['pic'])

    def _create_gifmaker(self):
        return GifMaker(self.config['gif'])

    def _create_info(self,sender):
        return {"username":sender.get("username"),
                "first_name":sender.get("first_name"),
                "last_name":sender.get("last_name")}

class UserDict(dict):

    def get_or_create(self, sender_or_id):
        if isinstance(sender_or_id,int):
            sender_id = sender_or_id
            if sender_id in self.keys():
                return self.get(sender_id)
            else:
                user=User(sender_id)
                self.update({sender_id:user})
                return user
        else:
            sender=sender_or_id
            if sender['id'] in self.keys():
                return self.get_and_update(sender)
            else:
                user=User(sender['id'])
                user.set_info(sender)
                self.update({sender['id']:user})
                return user

    def save(self):
        for user in self.values():
            user.save()

    def load(self,ids):
        for user_id in ids:
            self.update({user_id: User(user_id)})

    def get_and_update(self,sender):
        user=self.get(sender['id'])
        user.set_info(sender)
        return user


class UserState:

    def __init__(self,state):
        self.state = state

    def __eq__(self, other):
        return self.state == other

    def set(self,state):
        self.state = state


