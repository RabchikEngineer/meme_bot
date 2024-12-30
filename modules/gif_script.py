import subprocess
import threading

from modules.auxiliary import config_path
from subprocess import Popen,PIPE
import json,platform,time
import asyncio

with open(config_path, 'r', encoding='utf-8') as f:
    conf = json.load(f)

exec_file = "scripts/togif.bat" if platform.system() == "Windows" else "scripts/togif.sh"


class GifMaker:

    def __init__(self, config):
        self.resolution=config["resolution"]
        self.fps=config["fps"]
        self.ctrl=None


    def handle_error(self,error_type,ctrl,timeout=None):
        if error_type=="timeout":
            ctrl.logger.warning(f"GIF Timeout after {timeout} seconds")
            asyncio.run_coroutine_threadsafe(
                ctrl.respond(ctrl, ['GIF', conf["answers"]['gif_timeout'].format(timeout)]), ctrl.loop)
        else:
            ctrl.logger.error(f"GIF Conversion error")
            asyncio.run_coroutine_threadsafe(
                ctrl.respond(ctrl, ['GIF', conf["answers"]['gif_error']]), ctrl.loop)


    def make_gif(self, ctrl, queue, filename):
        self.ctrl = ctrl
        ctrl.active_threads.inc()
        if ctrl.active_threads == conf['gif_thread_count']:
            ctrl.gif_overcount_lock.acquire()
        end_filename = ''.join(filename.split('.')[:-1])+".gif"
        temp_dir = conf["directories"]["tmp"]
        temp_filename = str(threading.get_native_id())

        proc=None
        try:
            proc = Popen(
                [exec_file, filename, temp_dir, temp_filename, end_filename, str(self.resolution), str(self.fps)],
                stdout=PIPE, stderr=PIPE, stdin=PIPE, shell=False)
            time1 = time.time()
            proc.wait(conf['gif_timeout'])
            if proc.returncode!=0:
                raise Exception
        except subprocess.TimeoutExpired:
            self.handle_error("timeout",ctrl, timeout=conf["gif_timeout"])
            return
        except:
            ctrl.logger.error(proc.communicate()[1].decode('utf-8').replace("\n", " "))
            self.handle_error("other",ctrl)
            return
        finally:
            if ctrl.gif_overcount_lock.locked():
                ctrl.gif_overcount_lock.release()
            ctrl.active_threads.dec()

        res = proc.communicate()[1]
        if res:
            ctrl.logger.trace(res.decode('utf-8').replace("\n"," "))

        queue.put([ctrl, end_filename, time.time()-time1])
