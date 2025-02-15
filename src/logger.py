import os
import time
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


def init_logger():
    directory = f"logs/{datetime.today().strftime('%Y/%m/%d')}"
    
    if not os.path.exists(directory):
        os.makedirs(directory)

    file_path = f"{directory}/{int(time.time())}.log"
    open(file_path, 'w').close()
    

    FORMAT = '%(asctime)s %(message)s'
    logging.basicConfig(format=FORMAT, filename=file_path)