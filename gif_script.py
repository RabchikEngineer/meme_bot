from auxiliary import config_path
from subprocess import Popen,PIPE
import json,os,platform
import auxiliary as aux

with open(config_path, 'r', encoding='utf-8') as f:
    conf = json.load(f)

exec_ext=".bat" if platform.system() == "Windows" else ".sh"

class GifMaker:

    def __init__(self):
        pass

    def make_gif(self,filename):
        end_filename = ''.join(filename.split('.')[:-1])+".gif"
        proc = Popen(['togif'+exec_ext, filename, end_filename], stdout=PIPE, stderr=PIPE, stdin=PIPE,shell=True)
        if platform.system() == 'Windows':
            proc.wait(5)
            print([x.decode("cp1125",errors='ignore') for x in proc.communicate()])
            return filename
        proc.wait(120)
        return end_filename

