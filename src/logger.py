import time
import logging


logger = logging.getLogger(__name__)


def init_logger():
    
    try:
        import shutil
        shutil.move("flaw.log", f"logs/{int(time.time())}.log")
        open('flaw.log', 'w').close()
    except:
        open('flaw.log', 'w').close()
    

    FORMAT = '%(asctime)s %(message)s'
    logging.basicConfig(format=FORMAT, filename="flaw.log")