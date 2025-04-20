#!/usr/bin/env python3
import os
import requests
import time
from threading import Thread
from pystray import Icon
from PIL import Image, ImageDraw, ImageFont
from win10toast import ToastNotifier

# — Configuration
URL = "http://192.168.58.103:8000/"
POLL_INTERVAL = 60
LOW_THRESHOLD = 30
HIGH_THRESHOLD = 70
#DEFAULT_ICON = "default.ico"


def fetch_data():
    """Fetch JSON payload and return (battery:float, network:str, status:str)."""
    try:
        r = requests.get(URL, timeout=5)
        r.raise_for_status()
        d = r.json()
        batt = float(d.get("battery", "0%").strip('%'))
        net = d.get("network", "")
        stat = d.get("status", "").lower()
        return batt, net, stat
    except Exception:
        return None, None, None


def load_battery_icon(batt_percentage):
    """
    Load the .ico file matching batt_percentage from ICO_DIR.
    """
    idx = min(max(int(round(batt_percentage)), 0), 100)
    path = os.path.join("Bat Ico", f"{idx}.ico")
    #if not os.path.exists(path):
        #path = os.path.join("Bat Ico", DEFAULT_ICON)
    return Image.open(path)  # Pillow picks the best size from multi-size ICOs


def load_network_icon(network_type):
    """
    Load the .ico file matching batt_percentage from ICO_DIR.
    """
    path = os.path.join("Net Ico", f"{network_type}.ico")
    #if not os.path.exists(path):
        #path = os.path.join("Net Ico", DEFAULT_ICON)
    return Image.open(path)  # Pillow picks the best size from multi-size ICOs


def update_loop(batt_icon, net_icon):
    toaster = ToastNotifier()
    while True:
        batt, net, stat = fetch_data()
        if batt is not None:
            # Update battery icon
            batt_icon.icon = load_battery_icon(batt)
            batt_icon.title = f"Battery: {batt:.0f}% ({stat.capitalize()})"

            # Update network icon
            net_icon.icon = load_network_icon(net)
            net_icon.title = f"Network: {net}"

            # Notifications
            if stat == "discharging" and batt <= LOW_THRESHOLD:
                toaster.show_toast("Battery Low",
                                   f"{batt:.0f}% discharging. Please charge.",
                                   duration=5, threaded=True)
            if stat == "charging" and batt >= HIGH_THRESHOLD:
                toaster.show_toast("Battery High",
                                   f"{batt:.0f}% charging. Consider unplugging.",
                                   duration=5, threaded=True)
        time.sleep(POLL_INTERVAL)


def main():
    # Placeholder images so Icon objects initialize
    empty = Image.new('RGBA', (32, 32), (255, 255, 255, 0))
    batt_icon = Icon("battery", empty, "Battery")
    net_icon = Icon("network", empty, "Network")

    # Start the update loop on a background thread
    Thread(target=update_loop, args=(batt_icon, net_icon), daemon=True).start()

    # Start both tray-icon loops on their own threads to keep them alive
    Thread(target=batt_icon.run, daemon=True).start()
    Thread(target=net_icon.run, daemon=True).start()

    # Prevent main thread from exiting
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        batt_icon.stop()
        net_icon.stop()


if __name__ == "__main__":
    main()
