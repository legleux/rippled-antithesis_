import logging
import datetime
from pathlib import Path

FORMAT = "%(asctime)s - %(name)s:%(lineno)d - [%(levelname)s] - %(message)s"

class CustomFormatter(logging.Formatter):

    bold_green = "\x1b[31;1m"
    bold_red = "\x1b[31;1m"
    bold_white = "\x1b[37;1m"
    grey = "\x1b[38;20m"
    red = "\x1b[31;20m"
    blue = "\x1b[34;20m"
    magenta = "\x1b[35;20m"
    cyan = "\x1b[36;20m"
    white = "\x1b[37;20m"
    yellow = "\x1b[33;20m"
    reset = "\x1b[0m"
    # format = "%(asctime)s - %(name)s - [%(levelname)s] - %(message)s (%(filename)s:%(lineno)d)"
    format = "%(asctime)s - %(name)s:%(lineno)d - [%(levelname)s] - %(message)s"

    FORMATS = {
        logging.DEBUG: grey + format + reset,
        logging.INFO: reset + format + reset,
        logging.WARNING: yellow + format + reset,
        logging.ERROR: red + format + reset,
        logging.CRITICAL: bold_red + format + reset
    }


    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt)
        formatter.default_msec_format = '%s.%03d'
        return formatter.format(record)


# def formatTime_RFC3339(record, datefmt=None):
#     return (datetime.datetime.fromtimestamp(record.created).astimezone().isoformat(timespec="milliseconds"))

console_level = logging.DEBUG
file_level = logging.DEBUG

if Path("/.dockerenv").is_file():
    logdir=Path("/var/log/workload/")
else:
    logdir=Path(__file__).parent

Path(logdir).mkdir(parents=True, exist_ok=True)
tstamp = datetime.datetime.now().strftime("%Y_%m_%d_%H_%M_%S")

dirname, logfile, suffix = logdir, tstamp, '.log'
logfile = Path(dirname, logfile).with_suffix(suffix)


rootLogger = logging.getLogger()
rootLogger.setLevel(logging.INFO)

console = logging.StreamHandler()
console.setLevel(console_level)
console.setFormatter(CustomFormatter())

file = logging.FileHandler(logfile)
file.setLevel(file_level)
fileFormatter = logging.Formatter(fmt=FORMAT)
fileFormatter.default_msec_format = '%s.%03d'
file.setFormatter(fileFormatter)

rootLogger.addHandler(file)
rootLogger.addHandler(console)

log = logging.getLogger(__name__)

logging.getLogger("urllib3").setLevel(logging.WARNING)
logging.getLogger("requests").setLevel(logging.WARNING)
logging.getLogger("websockets").setLevel(logging.WARNING)
logging.getLogger('asyncio').setLevel(logging.WARNING)
