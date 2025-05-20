from common import log
from gpiozero import LED, Button, PWMLED
from signal import pause
from pathlib import Path
from time import sleep
import pygame
from random import randint
from subprocess import call
from threading import Thread, Timer

pygame.init()

# ------------------------------------------------
# Resources
# ------------------------------------------------

sound_folder = Path(__file__).parent / "resources"

lightsaber_open_sound = pygame.mixer.Sound(str(sound_folder / "lightsaber_open.wav"))
lightsaber_close_sound = pygame.mixer.Sound(str(sound_folder / "lightsaber_close.wav"))
lightsaber_hum_sound = sound_folder / "lightsaber_hum.wav"

starwars_funk = str(sound_folder / "star_wars_funk.wav")

r2d2_scream_sound = pygame.mixer.Sound(str(sound_folder / "r2d2_scream.wav"))
r2d2_woo_sound = pygame.mixer.Sound(str(sound_folder / "r2d2_woooo.wav"))
blaster_sound = pygame.mixer.Sound(str(sound_folder / "blaster.wav"))

# ------------------------------------------------
# GPIO Setup
# ------------------------------------------------

power_button = Button(3, hold_time=3)   # GPIO03 - Pin 05 + GND

lightsaber_switch = Button(26, pull_up=True)
lightsaber_led1 = PWMLED(25)
lightsaber_led2 = PWMLED(24)
lightsaber_led3 = PWMLED(23)

blinky_switch = Button(19, pull_up=True)
blinky_led1 = LED(12)
blinky_led2 = LED(16)

r2d2_scream_button = Button(13)

blaster_button = Button(6)
blaster_leds = LED(7)

disco_switch = Button(5, pull_up=True)
disco_leds = LED(8)

# ------------------------------------------------
# Global State & Constants
# ------------------------------------------------

lightsaber_leds = [lightsaber_led1, lightsaber_led2, lightsaber_led3]
lightsaber_led_sleep_time = 2 / len(lightsaber_leds) / 100  # total seconds / LEDs / steps

GRACE_PERIOD = 0.2  # seconds between switch‑off and animation stop

LIGHTSABER_MODE = False
BLINKY_MODE = False

_lightsaber_stop_timer: Timer | None = None
_blinky_stop_timer: Timer | None = None

# ------------------------------------------------
# Helper functions
# ------------------------------------------------

def shutdown():
    log.info("------- NoiseBox Shutting Down -------")
    call("sudo poweroff", shell=True)
    exit()


# ------------- Lightsaber -------------

def lightsaber_open():
    """Turn on the lightsaber (idempotent)."""
    global LIGHTSABER_MODE, _lightsaber_stop_timer

    # Cancel pending stop if switch bounced
    if _lightsaber_stop_timer and _lightsaber_stop_timer.is_alive():
        _lightsaber_stop_timer.cancel()

    if LIGHTSABER_MODE:
        return  # already running

    log.info("Lightsaber start")
    pygame.mixer.Sound.play(lightsaber_open_sound)
    pygame.mixer.music.load(lightsaber_hum_sound)
    pygame.mixer.music.play(-1)

    # Extend gradually
    for led in lightsaber_leds:
        for i in range(1, 101):
            led.value = i / 100
            sleep(lightsaber_led_sleep_time)

    LIGHTSABER_MODE = True
    Thread(target=_lightsaber_glow, daemon=True).start()


def _lightsaber_glow():
    """Breathing effect (background thread)."""
    while LIGHTSABER_MODE:
        for i in range(80, 100):
            for led in lightsaber_leds:
                led.value = i / 100
            sleep(0.01)
        for i in range(100, 79, -1):
            for led in lightsaber_leds:
                led.value = i / 100
            sleep(0.01)
        sleep(randint(1, 20) / 10)


def _lightsaber_stop():
    """Actually retract and stop audio (runs after grace period)."""
    global LIGHTSABER_MODE
    if not LIGHTSABER_MODE:
        return

    log.info("Lightsaber stop")
    LIGHTSABER_MODE = False

    pygame.mixer.music.stop()
    pygame.mixer.Sound.play(lightsaber_close_sound)

    for led in reversed(lightsaber_leds):
        for i in range(100, 0, -1):
            led.value = i / 100
            sleep(lightsaber_led_sleep_time)
        led.value = 0


def lightsaber_schedule_stop():
    """Schedule lightsaber stop after GRACE_PERIOD."""
    global _lightsaber_stop_timer
    if _lightsaber_stop_timer and _lightsaber_stop_timer.is_alive():
        _lightsaber_stop_timer.cancel()
    _lightsaber_stop_timer = Timer(GRACE_PERIOD, _lightsaber_stop)
    _lightsaber_stop_timer.daemon = True
    _lightsaber_stop_timer.start()


# ------------- Blinky -------------

def blinky_start():
    """Start Blinky (idempotent)."""
    global BLINKY_MODE, _blinky_stop_timer

    if _blinky_stop_timer and _blinky_stop_timer.is_alive():
        _blinky_stop_timer.cancel()

    if BLINKY_MODE:
        return

    log.info("Blinky Start!")
    BLINKY_MODE = True
    blinky_led1.blink()
    sleep(1)
    blinky_led2.blink()


def _blinky_stop():
    global BLINKY_MODE
    if not BLINKY_MODE:
        return

    log.info("Blinky Stop!")
    BLINKY_MODE = False
    blinky_led1.off()
    blinky_led2.on()


def blinky_schedule_stop():
    global _blinky_stop_timer
    if _blinky_stop_timer and _blinky_stop_timer.is_alive():
        _blinky_stop_timer.cancel()
    _blinky_stop_timer = Timer(GRACE_PERIOD, _blinky_stop)
    _blinky_stop_timer.daemon = True
    _blinky_stop_timer.start()

# ------------- Misc callbacks -------------

def r2d2_scream():
    log.info("Whaaaaaa")
    pygame.mixer.Sound.play(r2d2_scream_sound)


def blaster_pew_pew():
    log.info("Pew pew")
    pygame.mixer.Sound.play(blaster_sound)
    for _ in range(10):
        blaster_leds.on()
        sleep(0.05)
        blaster_leds.off()
        sleep(0.05)


def disco_start():
    log.info("DISCO MODE!!!")
    pygame.mixer.music.load(starwars_funk)
    pygame.mixer.music.play(-1)
    disco_leds.on()


def disco_stop():
    log.info("DISCO MODE stop :‑(")
    pygame.mixer.music.stop()
    disco_leds.off()
    if LIGHTSABER_MODE:
        pygame.mixer.music.load(lightsaber_hum_sound)
        pygame.mixer.music.play(-1)


# ------------------------------------------------
# GPIO Callbacks
# ------------------------------------------------

power_button.when_held = shutdown

lightsaber_switch.when_activated = lightsaber_open
lightsaber_switch.when_deactivated = lightsaber_schedule_stop

blinky_switch.when_activated = blinky_start
blinky_switch.when_deactivated = blinky_schedule_stop

r2d2_scream_button.when_activated = r2d2_scream

blaster_button.when_activated = blaster_pew_pew

disco_switch.when_activated = disco_start
disco_switch.when_deactivated = disco_stop

# ------------------------------------------------
# Main loop
# ------------------------------------------------

def main():
    log.info("------- NoiseBox Starting -------")
    pause()


if __name__ == "__main__":
    main()
