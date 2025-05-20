import logging

# -------------------
# Statics
# -------------------

DEBUG = True

# -------------------
# LOGGER
# -------------------

handler = logging.FileHandler('noisy_log.log', mode='a+')
formatter = logging.Formatter("[%(asctime)s] [%(levelname)8s] --- %(message)s (%(filename)s:%(lineno)s)", r"%Y-%m-%d %H:%M:%S")
handler.setFormatter(formatter)

log = logging.getLogger("noisy_logger")
log.addHandler(handler)
log.setLevel(logging.DEBUG if DEBUG else logging.INFO)
