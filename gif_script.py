import subprocess
import threading

from modules.auxiliary import config_path
from subprocess import Popen,PIPE
import json,os,platform,time

with open(config_path, 'r', encoding='utf-8') as f:
    conf = json.load(f)

exec_file = "togif.bat" if platform.system() == "Windows" else "./togif.sh"


class GifMaker:

    def __init__(self, config):
        self.resolution=config["resolution"]
        self.fps=config["fps"]

    def make_gif(self, ctrl, queue, filename):
        ctrl.active_threads.inc()
        if ctrl.active_threads == conf['gif_thread_count']:
            ctrl.gif_overcount_lock.acquire()
        end_filename = ''.join(filename.split('.')[:-1])+".gif"
        temp_dir = conf["directories"]["tmp"]
        temp_filename = str(threading.get_native_id())
        print(os.listdir())
        proc = Popen([exec_file, filename, temp_dir, temp_filename, end_filename,str(self.resolution),str(self.fps)],
                     stdout=PIPE, stderr=PIPE, stdin=PIPE,shell=False)
        time1 = time.time()
        try:
            proc.wait(conf['gif_timeout'])
        except subprocess.TimeoutExpired:
            queue.put([ctrl, 'gif_timeout',conf['gif_timeout']])
            return
        finally:
            if ctrl.gif_overcount_lock.locked():
                ctrl.gif_overcount_lock.release()
            ctrl.active_threads.dec()
        if platform.system() == 'Windows':
            print([x.decode("cp1125",errors='ignore') for x in proc.communicate()])
            queue.put([ctrl, filename, 200])
            return
        res = proc.communicate()[1]
        if res:
            ctrl.logger.error(res.decode('utf-8').replace("\n"," "))
        queue.put([ctrl, end_filename, time.time()-time1])
