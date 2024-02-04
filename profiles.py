from auxiliary import config_path
import json, os
from square_memes_script import PicMaker
from gif_script import GifMaker


with open(config_path, encoding='utf-8') as f:
    conf = json.load(f)

users_configs_dir = conf['directories']['users_configs']
pic_configs_dir = conf['directories']['pic_configs']

class User:

    def __init__(self, user_id):
        self.state='idle'
        self.id = user_id
        self.config, is_new = self._load_config()
        self.picmaker = self._create_picmaker()
        self.gifmaker = self._create_gifmaker()
        self.mode = self.config['mode']
        self.info = self.config['info']

    def reload(self):
        self.config, _ = self._load_config()
        self.picmaker = self._create_picmaker()
        self.gifmaker = self._create_gifmaker()
        self.mode = self.config['mode']

    def save(self):
        filename=pic_configs_dir + str(self.id)
        self.config['info'] = self.info
        with open(filename, 'w',encoding='utf-8') as f:
            json.dump(self.config,f,indent=2,ensure_ascii=False)

    def set_info(self,sender):
        self.info = self._create_info(sender)

    def set_font(self,font):
        self.config['pic']['font']=font
        self.picmaker = self._create_picmaker()

    def get_stats(self):
        return f'\nТекущий режим: {self.mode}\nТекущий шрифт: {self.config["pic"]["font"]}\n'

    def _load_config(self):
        filename=pic_configs_dir + str(self.id)
        with open(filename if os.path.exists(filename) else "default_user_config.json",encoding='utf-8') as f:
            return json.load(f), os.path.exists(filename)

    def _create_picmaker(self):
        return PicMaker(self.config['pic'])

    def _create_gifmaker(self):
        return GifMaker()

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

