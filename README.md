# ThinkPad X260 - OpenCore - Sequoia

> **OpenCore Source & Guide:** [Dortania OpenCore Install Guide](https://dortania.github.io/OpenCore-Install-Guide/) | OpenCore 1.0.4
> Original EFI Base: ThinkPad X260 6th Gen Skylake

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

## What's Works

- [x] Full Graphics Acceleration
- [x] WiFi & Bluetooth (via itlwm + HeliPort)
- [x] Audio, Mic, Camera
- [x] Keyboard, Fn Keys, Backlight
- [x] Trackpad + Gestures
- [x] Battery Indicator & Power Management
- [x] Sleep / Wake / Lid
- [x] All USB Ports

## IMPORTANT - WiFi Fix for Sequoia 15.x

Di macOS Sequoia, `AirportItlwm.kext` tidak stabil dan akan muncul `Wi-Fi: No hardware installed`.

**Fix yang work di repo ini (sudah di-apply di EFI ini):**

1.  Gunakan `itlwm.kext v2.3.0 Stable` (bukan AirportItlwm)
2.  Di `config.plist` > `Kernel > Add` : 
    - `itlwm.kext` = **Enabled**
    - `IOSkywalkFamily.kext` = **Disabled**
    - `IO80211FamilyLegacy.kext` = **Disabled**
3.  Reset NVRAM setelah ganti kext (Tekan Spasi di OpenCore Picker > Reset NVRAM)
4.  Gunakan `HeliPort.app` untuk konek WiFi (ada di folder HeliPort repo ini)

Jika HeliPort muncul `itlwm is not running` berarti NVRAM belum di-reset.

## Cara Konek WiFi & Auto Start

App HeliPort sudah ada di repo ini: `HeliPort/HeliPort.app`

1.  Copy `HeliPort.app` ke `/Applications`
2.  Buka dan konek ke WiFi kamu

**Biar Auto Start di Sequoia:**

HeliPort versi baru tidak ada setting `Launch at login` di dalam Preferences (hanya ada setting update).

Caranya pakai Login Items macOS:
`System Settings` > `General` > `Login Items` > klik `+` > pilih `HeliPort` > Open

Sekarang tiap boot, HeliPort auto jalan di menu bar dan auto konek.

## Installation

1.  Download EFI dari repo ini
2.  Copy ke partisi EFI USB Installer
3.  Set BIOS: Security > Secure Boot Disabled, Config > Thunderbolt Disabled
4.  Boot via F12 > Install macOS

## Credits

- Dortania Team
- OpenIntelWireless Team (itlwm & HeliPort)
- Acidanthera

Enjoy Sequoia on X260!