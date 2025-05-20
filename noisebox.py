from common import log
from gpiozero import LED, Button, PWMLED
from signal import pause
from pathlib import Path
from time import sleep
import pygame
from random import randint
from subprocess import call

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

power_button = Button(3, hold_time=3)   # GPIO03 - Pin 05 + Ground
# Powered LED should be connected between Pin 1 + RGround
# Status LED should be connected between GPIO14 (08) + RGround
# https://th.bing.com/th/id/OIP.2hmDzozDem4i3qrLjrIsmAHaHz?pid=ImgDet&rs=1

lightsaber_switch = Button(26)
lightsaber_led1 = PWMLED(25)
lightsaber_led2 = PWMLED(24)
lightsaber_led3 = PWMLED(23)

blinky_switch = Button(19)
blinky_led1 = LED(12)
blinky_led2 = LED(16)

r2d2_scream_button = Button(13)

blaster_button = Button(6)
blaster_leds = LED(7)

disco_switch = Button(5)
disco_leds = LED(8)

# ------------------------------------------------
# Functions
# ------------------------------------------------

lightsaber_leds = [lightsaber_led1, lightsaber_led2, lightsaber_led3]
lightsaber_led_sleep_time = 2 / len(lightsaber_leds) / 100  # Total seconds / LEDs / steps

LIGHTSABER_MODE = False
DISCO_MODE = False
BLINKY_MODE = False

def shutdown():
    log.info("------- NoiseBox Shutting Down -------")
    call("sudo poweroff", shell=True)
    exit()


def lightsaber_open():
    log.info("Lightsaber start")
    pygame.mixer.Sound.play(lightsaber_open_sound)
    pygame.mixer.music.load(lightsaber_hum_sound)
    pygame.mixer.music.play(-1)
    
    for led in lightsaber_leds:
        for i in range(1, 101):
            led.value = i/100
            sleep(lightsaber_led_sleep_time)
    
    global LIGHTSABER_MODE
    LIGHTSABER_MODE = True
    lightsaber_glow()


def lightsaber_glow():
    while LIGHTSABER_MODE:
        # Glow up
        for i in range(80, 100):
            for led in lightsaber_leds:
                led.value = i/100
            sleep(0.01)
        
        # Glow down
        for i in range(100, 80):
            for led in lightsaber_leds:
                led.value = i/100
            sleep(0.01)
        sleep(randint(1,20)/10)


def lightsaber_close():
    log.info("Lightsaber stop")
    global LIGHTSABER_MODE
    LIGHTSABER_MODE = False
    sleep(0.5)
    pygame.mixer.music.stop()
    pygame.mixer.Sound.play(lightsaber_close_sound)

    for led in reversed(lightsaber_leds):
        for i in range(100, 0, -1):
            led.value = i/100
            sleep(lightsaber_led_sleep_time)
        led.value = 0


def blinky_start():
    log.info("Blinky Start!")
    global BLINKY_MODE
    BLINKY_MODE = True
    blinky_led1.blink()
    sleep(1)
    blinky_led2.blink()


def blinky_stop():
    log.info("Blinky Stop!")
    global BLINKY_MODE
    BLINKY_MODE = False
    blinky_led1.off()
    blinky_led2.on()


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
    log.info("DISCO MODE stop :-(")
    pygame.mixer.music.stop()
    disco_leds.off()
    if LIGHTSABER_MODE:
        pygame.mixer.music.load(lightsaber_hum_sound)
        pygame.mixer.music.play(-1)


# ------------------------------------------------
# Callbacks
# ------------------------------------------------

power_button.when_held = shutdown
lightsaber_switch.when_activated = lightsaber_open
lightsaber_switch.when_deactivated = lightsaber_close
blinky_switch.when_activated = blinky_start
blinky_switch.when_deactivated = blinky_stop
r2d2_scream_button.when_activated = r2d2_scream
blaster_button.when_activated = blaster_pew_pew
disco_switch.when_activated = disco_start
disco_switch.when_deactivated = disco_stop

# ------------------------------------------------
# Running Code
# ------------------------------------------------

def main():
    log.info("------- NoiseBox Starting -------")
    pause()


if __name__ == '__main__':
    main()
    sleep(5)

