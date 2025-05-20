from gpiozero import Button
from signal import pause
from datetime import datetime

# --- Edit this to match your BCM pin numbers ---
BUTTON_PINS = [3, 26, 19, 12, 16, 13, 6, 5]
# -----------------------------------------------

def now():
    """Timestamp helper."""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def print_event(pin, state):
    print(f"{now()}  GPIO{pin:<2} {state}")

for pin in BUTTON_PINS:
    btn = Button(pin)
    btn.when_pressed  = lambda p=pin: print_event(p, "ON")
    btn.when_released = lambda p=pin: print_event(p, "OFF")

print("Tester running...")
pause()
