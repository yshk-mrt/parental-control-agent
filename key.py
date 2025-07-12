from pynput import keyboard
from datetime import datetime
from rich.console import Console

console = Console()
logfile = open("keystrokes.log", "a", encoding="utf-8")

def on_press(key):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
    try:
        k = key.char
    except AttributeError:
        k = str(key)
    line = f"{ts}\t{k}"
    console.print(line, style="cyan")
    logfile.write(line + "\n")

with keyboard.Listener(on_press=on_press) as listener:
    console.print("[bold green]Recording…  Press ESC to stop[/]")
    listener.join()