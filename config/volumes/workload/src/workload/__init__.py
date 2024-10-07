import logging
import datetime
from pathlib import Path

FORMAT = "%(asctime)s.%(msecs)03d [%(levelname)s] %(module)s - [%(filename)s:%(lineno)d] %(message)s"
file_level = console_level = default_level = logging.DEBUG
# datefmt='%Y-%m-%d %H:%M:%S'
# datefmt='%H:%M:%S'

if Path("/.dockerenv").is_file():
    logdir=Path("/var/log/workload/")
else:
    logdir=Path(__file__).parent

Path(logdir).mkdir(parents=True, exist_ok=True)
tstamp = datetime.datetime.now().strftime("%Y_%m_%d_%H_%M_%S")

dirname, logfile, suffix = logdir, tstamp, '.log'
logfile = Path(dirname, logfile).with_suffix(suffix)

logging.basicConfig(
     filename=logfile,
     level=file_level,
     format=FORMAT,
    #  datefmt=datefmt
)

console = logging.StreamHandler()
console.setLevel(console_level)
console.setFormatter(logging.Formatter(FORMAT))
logging.getLogger().addHandler(console)

log = logging.getLogger(__name__)

log.info("Initialized logging!")

logging.getLogger("urllib3").setLevel(logging.WARNING)
logging.getLogger("requests").setLevel(logging.WARNING)
logging.getLogger("websockets").setLevel(logging.WARNING)
logging.getLogger('asyncio').setLevel(logging.WARNING)

# def main() -> int:
#     log.info("am main!")
#     # debug_level = 20
#     # if len(sys.argv) > 1 and sys.argv[1] == "debug":
#     #     debug_level = 10
#     # asyncio.run(run_workload(debug_level))
#     return 0
