import threading

from auxiliary import config_path
from subprocess import Popen,PIPE
import json,os,platform,time
import auxiliary as aux
import threading as th

with open(config_path, 'r', encoding='utf-8') as f:
    conf = json.load(f)

exec_file = "togif.bat" if platform.system() == "Windows" else "./togif.sh"


class GifMaker:

    def __init__(self, config):
        self.resolution=config["resolution"]
        self.fps=config["fps"]

    def make_gif(self, ctrl, queue, filename):
        end_filename = ''.join(filename.split('.')[:-1])+".gif"
        print(end_filename)
        temp_dir = conf["directories"]["gif"]
        temp_filename = f'{threading.get_native_id()}.gif'
        proc = Popen([exec_file, filename, temp_dir, temp_filename, end_filename,str(self.resolution),str(self.fps)],
                     stdout=PIPE, stderr=PIPE, stdin=PIPE,shell=False)
        if platform.system() == 'Windows':
            proc.wait(10)
            print([x.decode("cp1125",errors='ignore') for x in proc.communicate()])
            queue.put([ctrl, filename, 200])
            return
        time1 = time.time()
        proc.wait(conf['gif_timeout'])
        queue.put([ctrl, end_filename, time.time()-time1])
