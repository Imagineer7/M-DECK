# M-DECK
## Meshtastic Desktop Environment Client Kit
This is a fork of https://github.com/ssnofall/meshtastic-desktop-application

A Python-based GUI application for interacting with Meshtastic devices, built using flet and the Meshtastic Python API. This project aims to provide a user-friendly desktop alternative to the official Meshtastic clients, eventually offering the same functionality as the iOS, Android, and web clients, in an offline-capable, native desktop form.

---

<img src="img/preview1.png" alt="Meshtastic GUI Preview" width="800"/>

---
## Current Status

![Project Status](https://img.shields.io/badge/status-in%20progress-yellow)

This project is still under development and will continue evolving with time, feedback, and feature requests.

---

## Project Goals

The primary goal of this project is to provide a full-featured, offline-capable desktop client with the same features as the official Meshtastic mobile and web apps.

### Core Objectives

- Offline-first functionality
- Native Windows & Linux support
- Clean and modern UI
- All core Meshtastic Client functions

---

## Getting Started

### Requirements

- Python 3.14
- meshtastic
- flet

### Installation

```bash
git clone https://github.com/Imagineer7/M-DECK.git
cd meshtastic-desktop-application
```
```bash
python3.14 -m venv .venv
```
```bash
#Activate it on Linux/macOS
source .venv/bin/activate
```
```bash
#Activate it on Windows
.venv\Scripts\activate
```
```bash
pip install -r requirements.txt
```

### Running the App
```bash
python main.py
```

### Linux Serial Troubleshooting

If the app can see your Meshtastic USB port but cannot connect, try the following:

1. Add your user to the `dialout` group so it can access serial devices.
```bash
sudo usermod -aG dialout <your-username>
```

2. Log out and log back in, or reboot, then verify the group change.
```bash
groups
```

3. Unplug and replug the LoRa device, reopen the app, scan ports again, and reconnect.

4. If it still fails, check `logs/mdeck.log` for the connection error details.

---

## Current Features
- Serial Connection (USB)
- Network Connection (TCP)
- My Node Information
- Messaging (Primary Channel & Direct Messages)
- Connected Nodes
- Configure Long Name & Short Name

---

## License

GNU General Public License v3.0

> **Disclaimer:** This project is not affiliated with or endorsed by Meshtastic LLC.

---

## Authors
- [snofall](https://github.com/ssnofall)
- [WAPEETY](https://github.com/WAPEETY)
- [Imagineer7](https://github.com/Imagineer7)
