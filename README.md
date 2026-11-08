# ThinkPad X260 - OpenCore - Sequoia

> **OpenCore Source & Guide:** [Dortania OpenCore Install Guide](https://dortania.github.io/OpenCore-Install-Guide/) | OpenCore 1.0.4
> Original EFI Base: ThinkPad X260 6th Gen Skylake

> **Download macOS Sequoia Installer (from this repo):**
> [📥 macOS Sequoia - Google Drive](https://drive.google.com/file/d/1x5jg_bDay35TtsH0kR7J_OW9Ticzzknx/view?usp=drivesdk)

EFI ini sudah tested work di Lenovo ThinkPad X260 untuk **macOS Ventura, Sonoma & Sequoia 15.x**.

## Screenshots Sequoia

![ss_1](ss_1.png)
![ss_2](ss_2.png)

## Laptop Specs

- **Model:** Lenovo ThinkPad X260
- **CPU:** Intel Core i5-6300U / i7-6600U (Skylake)
- **GPU:** Intel HD Graphics 520
- **RAM:** 8GB / 16GB DDR4
- **WiFi:** Intel Dual Band Wireless-AC 8260 (Stock) - Works with itlwm
- **Audio:** Realtek ALC293
- **Trackpad:** Synaptics with Gestures

## Download

- **EFI:** Download dari repo ini (Code > Download ZIP)
- **macOS Sequoia Installer:** [Google Drive Link](https://drive.google.com/file/d/1x5jg_bDay35TtsH0kR7J_OW9Ticzzknx/view?usp=drivesdk)

## What's Works

- [x] Full Graphics Acceleration
- [x] WiFi & Bluetooth (via itlwm + HeliPort)
- [x] Audio, Mic, Camera
- [x] Keyboard, Fn Keys, Backlight
- [x] Trackpad + Gestures
- [x] Battery & Power Management
- [x] Sleep / Wake

## IMPORTANT - WiFi Fix for Sequoia 15.x

Di Sequoia, `AirportItlwm.kext` bikin `Wi-Fi: No hardware installed`.

**Fix yang work di EFI ini:**

1. Pakai `itlwm.kext v2.3.0 Stable`
2. Di config.plist: `itlwm` = Enabled, `IOSkywalkFamily` & `IO80211FamilyLegacy` = Disabled
3. Reset NVRAM (Spasi di OpenCore Picker > Reset NVRAM)
4. Pakai `HeliPort.app` untuk konek WiFi (ada di repo ini)

## Cara Konek WiFi & Auto Start

1. Copy `HeliPort.app` ke `/Applications`
2. Buka dan konek WiFi

**Auto Start di Sequoia:**
`System Settings` > `General` > `Login Items` > `+` > Add `HeliPort`

## Credits

- Dortania Team
- OpenIntelWireless (itlwm & HeliPort)

Enjoy Sequoia on X260!