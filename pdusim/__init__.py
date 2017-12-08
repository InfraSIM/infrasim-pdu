import os
from common import logger, config


if not os.path.exists("/var/log/pdusim"):
    os.makedirs("/var/log/pdusim")

logger.initialize("pdusim", "file", config.pdusim_default_log)
