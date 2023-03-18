from common import log
from gpiozero import LED, Button, PWMLED
# from signal import pause
def pause(): pass
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

lightsaber_open_sound = pygame.mixer.Sound(sound_folder / "lightsaber_open.wav")
lightsaber_close_sound = pygame.mixer.Sound(sound_folder / "lightsaber_close.wav")
lightsaber_hum_sound = sound_folder / "lightsaber_hum.wav"

starwars_funk = sound_folder / "star_wars_funk.wav"

r2d2_scream_sound = pygame.mixer.Sound(sound_folder / "r2d2_scream.wav")
r2d2_woo_sound = pygame.mixer.Sound(sound_folder / "r2d2_woooo.wav")
blaster_sound = pygame.mixer.Sound(sound_folder / "blaster.wav")

# ------------------------------------------------
# GPIO Setup
# ------------------------------------------------

power_button = Button(3, hold_time=3)   # GPIO03 - Pin 05 + Ground
# Powered LED should be connected between Pin 1 + RGround
# Status LED should be connected between GPIO14 (08) + RGround

lightsaber_switch = Button(26)          # GIPO26 - Pin 39 + Ground
lightsaber_led1 = PWMLED(21)            # GPIO21 - Pin 40 + RGround
lightsaber_led2 = PWMLED(4)             # GPIO04 - Pin 07 + RGround
lightsaber_led3 = PWMLED(17)            # GPIO17 - Pin 11 + RGround

blinky_switch = Button(27)              # GPIO27 - Pin 13 + Ground
blinky_led1 = LED(22)                   # GPIO22 - Pin 15 + RGround
blinky_led2 = LED(5)                    # GPIO05 - Pin 29 + RGround

r2d2_scream_button = Button(6)          # GPIO06 - Pin 31 + Ground

blaster_button = Button(13)             # GPIO13 - Pin 33 + Ground
blaster_leds = LED(19)                  # GPIO19 - Pin 35 + RGround

disco_switch = Button(23)               # GPIO23 - Pin 16 + Ground
disco_leds = LED(18)                    # GPIO18 - Pin 12 + RGround

# ------------------------------------------------
# Functions
# ------------------------------------------------

lightsaber_leds = [lightsaber_led1, lightsaber_led2, lightsaber_led3]
lightsaber_led_sleep_time = 2 / len(lightsaber_leds) / 100  # Total seconds / LEDs / steps

LIGHTSABER_MODE = False
DISCO_MODE = False
BLINKY_MODE = False

def shutdown():
    call("sudo poweroff", shell=True)


def lightsaber_open():
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
    global BLINKY_MODE
    BLINKY_MODE = True
    blinky_led1.blink()
    sleep(1)
    blinky_led2.blink()


def blinky_stop():
    global BLINKY_MODE
    BLINKY_MODE = False
    blinky_led1.off()
    blinky_led2.on()


def r2d2_scream():
    pygame.mixer.Sound.play(r2d2_scream_sound)


def blaster_pew_pew():
    pygame.mixer.Sound.play(blaster_sound)
    for _ in range(20):
        blaster_leds.on()
        sleep(0.05)
        blaster_leds.off()
        sleep(0.05)


def disco_start():
    pygame.mixer.music.load(starwars_funk)
    pygame.mixer.music.play(-1)


def disco_stop():
    pygame.mixer.music.stop()


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
    #lightsaber_open()
    disco_start()
    sleep(45)
    #lightsaber_close()


if __name__ == '__main__':
    main()
    sleep(5)

