"""Base logger"""
import datetime
import logging
import os

path = 'log'
isExist = os.path.exists(path)
if not isExist:
    os.makedirs(path)

level = logging.DEBUG
today = datetime.date.today()
logfile = os.path.join("log", today.strftime("%Y-%m-%d") + '.log')

logger = logging.getLogger(__name__)
logger.setLevel(level)

# create file handler which logs even debug messages
fh = logging.FileHandler(logfile)
fh.setLevel(level)

# create console handler with a higher log level
ch = logging.StreamHandler()
ch.setLevel(level)

# create formatter and add it to the handlers
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
fh.setFormatter(formatter)
ch.setFormatter(formatter)

# add the handlers to the logger
logger.addHandler(fh)
logger.addHandler(ch)

logger.info("Logger has been setup")