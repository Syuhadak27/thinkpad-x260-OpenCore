# Laporan Perbaikan EFI OpenCore — folder `2026`

Tanggal: 30 Oktober 2026
Lokasi: `/storage/emulated/0/COMPARE`
Status akhir: **config.plist sudah diperbaiki & lolos validasi struktur.**

---

## 1. Ringkasan

Keluhan awal: EFI "OpenCore 2026" tidak bisa boot dengan pesan

```
OC: Configuration requires vault but no vault provided!
```

sedangkan EFI "2024" normal.

Hasil pemeriksaan: **bukan masalah versi OpenCore.** Semua binary di kedua folder
byte-identical (OpenCore 2023). Yang rusak hanya `config.plist` di folder `2026`,
dan kerusakannya bukan cuma soal Vault — config itu kehilangan 4 dari 8 section
wajib OpenCore, sehingga tidak mungkin boot.

Perbaikan: `2026/EFI/OC/config.plist` diganti dengan config lengkap yang sudah
terbukti boot (basis config `2024`), config rusak disimpan sebagai backup.

---

## 2. Bukti: EFI "2026" sebenarnya bukan OpenCore baru

| Item | `2024/EFI` | `2026/EFI` (sebelum perbaikan) |
|---|---|---|
| `OC/OpenCore.efi` | 598.016 B, 20 Jul 2023, md5 `44a58f86…` | **md5 sama persis** |
| `BOOT/BOOTx64.efi` | md5 `200bd096…` | **md5 sama persis** |
| `OC/Drivers/*.efi` (6 file) | — | **md5 sama persis** |
| `OC/Kexts/Lilu.kext` | Lilu **1.6.2** (rilis 2023) | **sama persis** |
| `OC/config.plist` | 48.166 B, lengkap | **23.975 B, tidak lengkap** |

Kesimpulan: OpenCore di folder `2026` adalah build pertengahan 2023
(± 0.9.3/0.9.4). Penamaan folder "2026" menyesatkan — tidak ada binary baru di sana.

Perintah untuk mengecek sendiri:

```bash
md5sum 2024/EFI/OC/OpenCore.efi 2026/EFI/OC/OpenCore.efi
md5sum 2024/EFI/BOOT/BOOTx64.efi 2026/EFI/BOOT/BOOTx64.efi
md5sum 2024/EFI/OC/Drivers/*.efi 2026/EFI/OC/Drivers/*.efi
```

---

## 3. Akar masalah

### 3.1 Section wajib hilang

OpenCore punya 8 section top-level. Config `2026` hanya punya 4:

```
2024 : ACPI, Booter, DeviceProperties, Kernel, Misc, NVRAM, PlatformInfo, UEFI
2026 : ACPI, Kernel, Misc, UEFI          <-- Booter/DeviceProperties/NVRAM/PlatformInfo hilang
```

Rincian yang hilang di config `2026`:

| Section | Yang hilang | Akibat |
|---|---|---|
| `Misc` | hanya berisi `Tools`; `Security`, `Boot`, `Debug`, `Entries`, `Serial` hilang | **Vault tidak terbaca**, picker/policy default tak terkontrol |
| `Booter` | seluruh section (`MmioWhitelist`, `Patch`, `Quirks`) | `AvoidRuntimeDefrag` dll tidak ada → gagal/hang saat boot |
| `DeviceProperties` | seluruh section | `ig-platform-id`, `layout-id`, patch framebuffer hilang → HD 520/Audio mati |
| `Kernel` | hanya `Add`; `Quirks`, `Emulate`, `Patch`, `Scheme` hilang | `AppleXcpmCfgLock` dll tidak ada → hang di ThinkPad Skylake |
| `NVRAM` | seluruh section | tidak ada `boot-args`, `csr-active-config` |
| `PlatformInfo` | seluruh section | **tidak ada SMBIOS** → boot macOS tidak valid |
| `UEFI` | hanya `Drivers`; `Quirks`, `APFS`, `Output`, `Input`, `ProtocolOverrides`, `ReservedMemory` hilang | boot/runtime rusak |
| `ACPI` | hanya `Add`; `Quirks`, `Delete`, `Patch` hilang | quirk tabel ACPI tidak diterapkan |

File `config.plist` lama **tidak corrupt/terpotong**: XML valid dan ditutup
`</plist>` dengan benar. Section-section itu memang tidak pernah ditulis
(kemungkinan hasil generator/AI — cirinya `Comment` = nama file, urutan kext
alfabetis, semua `MinKernel` kosong).

### 3.2 Kenapa muncul pesan Vault

String itu memang ada di binary yang dipakai:

```
OC: Configuration requires vault but no vault provided!
```

Aturan OpenCore: vault hanya diminta kalau `Misc > Security > Vault` **tidak**
bernilai `Optional`. Kalau mode `Basic`/`Secure` aktif tetapi
`EFI/OC/Vault.plist` dan `Vault.sig` tidak ada, boot dihentikan.

- Di config `2024`: `Vault = Optional` → tidak ada vault diminta → normal.
- Di config `2026`: blok `Misc > Security` **tidak ada sama sekali**, dan di
  `EFI/OC/` **tidak ada `Vault.plist`/`Vault.sig`** → OpenCore masuk jalur
  "wajib vault tapi vault tidak disediakan".

Jadi pesan Vault adalah **gejala pertama**, bukan satu-satunya masalah. Bahkan
kalau pesan itu dilewati, config `2026` tetap gagal boot karena tidak punya
SMBIOS, Booter quirks, Kernel quirks, NVRAM, dan DeviceProperties.

### 3.3 Masalah tambahan di config `2026`

- Urutan kext alfabetis → dependency dilanggar:
  `AirportItlwm_BigSur` (index 0) dimuat sebelum `Lilu` (index 6),
  `CPUFriendDataProvider` (3) sebelum `CPUFriend` (32),
  plugin SMC/PS2/RMI dimuat sebelum induknya.
- `AirportItlwm_BigSur` di-enable (config 2024 memakai `AirportItlwm_Ventura`).
- `FeatureUnlock` tanpa `MinKernel` (seharusnya `21.0.0`).
- `ResetNvramEntry.efi` di-disable (tidak praktis saat instalasi).

---

## 4. Perbaikan yang dilakukan

| Aksi | File |
|---|---|
| Backup config rusak | `2026/EFI/OC/config.plist.bak-2026-broken` (md5 `277e9611…`) |
| Ganti config dengan versi lengkap | `2026/EFI/OC/config.plist` (md5 `9b029484…`, sama dengan config `2024` yang sudah boot) |
| Tambah tool validasi | `validate-efi.py` |

Tidak ada file binary/kext/ACPI yang diubah — isinya memang sudah identik dengan
folder `2024`. Jadi perbaikan ini murni mengembalikan skema config yang benar.

### Kenapa pakai config `2024` sebagai basis?

Karena itu satu-satunya config **lengkap** dan sudah terbukti boot di mesin ini.
Isi folder `2026` (OpenCore.efi, kext, ACPI, driver) identik, jadi config itu
kompatibel. Membangun ulang config `2026` dari nol butuh menambah 30+ key yang
hilang — jauh lebih rawan error daripada memakai config yang sudah jalan.

---

## 5. Hasil validasi

### Sebelum (config lama, `config.plist.bak-2026-broken`)

```
Vault        : <MISSING>
SMBIOS       : -
boot-args    : -
WiFi aktif   : AirportItlwm_BigSur.kext

ERROR: section top-level hilang: Booter
ERROR: section top-level hilang: DeviceProperties
ERROR: section top-level hilang: NVRAM
ERROR: section top-level hilang: PlatformInfo
ERROR: Misc > Security hilang (penyebab pesan vault)
ERROR: PlatformInfo > Generic > SystemProductName kosong
ERROR: UEFI > Quirks > RequestBootVarRouting hilang
ERROR: Booter > Quirks > AvoidRuntimeDefrag hilang

WARN : Lilu.kext di index 4 (harusnya awal)
WARN : AirportItlwm_BigSur sebelum Lilu
WARN : CPUFriendDataProvider sebelum CPUFriend
WARN : boot-args tidak diset di NVRAM
HASIL: 8 error struktur
```

Catatan: daftar file yang direferensikan config lama dan config baru **identik**
(14 SSDT, 41 entry kext, 6 driver `.efi`), jadi semua file memang ada di
`2026/EFI`. Yang salah murni struktur/nilai config, bukan file hilang.

### Sesudah (config hasil perbaikan)

```
== 2026/EFI ==
  Vault              : Optional
  SecureBootModel    : Disabled
  ScanPolicy         : 0
  SMBIOS             : MacBookPro14,1
  boot-args          : keepsyms=1
  Kext enabled       : 36
  WiFi aktif         : ['AirportItlwm_Ventura.kext']

  WARN  : SystemSerialNumber kosong (boot bisa, iServices/serial tidak)
  HASIL : OK - tidak ada error struktur
```

Semua file yang direferensikan config (14 SSDT, 36 bundle kext, 6 driver .efi,
`OpenCore.efi`, `BOOTx64.efi`) dicek ada di folder `2026/EFI` — tidak ada yang
menggantung.

---

## 6. Konfigurasi penting di config hasil perbaikan

| Setting | Nilai | Catatan |
|---|---|---|
| `Misc > Security > Vault` | `Optional` | **ini yang menghilangkan error vault** |
| `Misc > Security > SecureBootModel` | `Disabled` | aman untuk instalasi |
| `Misc > Security > DmgLoading` | `Signed` | |
| `Misc > Security > ScanPolicy` | `0` | semua drive/OS terlihat di picker |
| `Misc > Boot > ShowPicker` | `true` | |
| `Misc > Boot > PickerMode` | `External` | butuh `OpenCanopy.efi` (ada) |
| `Booter > Quirks > AvoidRuntimeDefrag` | `true` | wajib |
| `Booter > Quirks > SetupVirtualMap` | `true` | |
| `Kernel > Quirks > AppleXcpmCfgLock` | `true` | wajib untuk ThinkPad Skylake |
| `Kernel > Quirks > DisableLinkeditJettison` | `true` | untuk Lilu 1.6.x |
| `UEFI > Quirks > RequestBootVarRouting` | `true` | |
| `PlatformInfo > Generic > SystemProductName` | `MacBookPro14,1` | sesuai config yang sudah boot |
| `NVRAM > boot-args` | `keepsyms=1` | tambah `-v` saat debug |
| `UEFI > Drivers` | HfsPlus, OpenRuntime, OpenCanopy, AudioDxe, ToggleSipEntry (ON) + ResetNvramEntry (OFF) | semua versi sama |

Catatan `SystemSerialNumber` masih kosong. Boot & instalasi tetap jalan, tapi
iMessage/iCloud/App Store belum akan bekerja. Nanti isi dengan serial valid
(OCAT "Generate SMBIOS" atau GenSMBIOS + cek ke-3 situs pengecekan serial).

### NVRAM tidak dihilangkan

Config hasil perbaikan tetap memuat section `NVRAM` **penuh**:

- `NVRAM > Add` — 3 GUID: `4D1EDE05…` (`DefaultBackgroundColor`, `UIScale`),
  `4D1FDA02…` (`rtc-blacklist`), `7C436110…` (`boot-args`, `csr-active-config`,
  `prev-lang:kbd`, `run-efi-updater`, `ForceDisplayRotationInEFI`,
  `SystemAudioVolume`).
- `NVRAM > Delete` — 3 GUID / 5 variabel: `UIScale`, `DefaultBackgroundColor`,
  `rtc-blacklist`, `boot-args`, `csr-active-config`.
- `WriteFlash = true`, `LegacyOverwrite = false`.
- `UEFI > Drivers > ResetNvramEntry.efi` = **disabled** → entry "Reset NVRAM"
  **tidak muncul** di picker (permintaan pemilik mesin, lihat §13).

Arti `NVRAM > Delete`: variabel yang terdaftar di situ **dihapus setiap boot**
lalu ditulis ulang oleh `Add`. Ini bukan "mengosongkan NVRAM", dan memang
sengaja begitu supaya `boot-args`/`csr-active-config` lama dari percobaan
sebelumnya tidak nyangkut. Untuk wipe total, lihat §13 (entry picker sudah
dimatikan; pakai `nvram -c` dari macOS atau aktifkan sementara driver-nya).

Yang "dihapus" saat perbaikan hanyalah kondisi rusak sebelumnya: config lama
**tidak punya section NVRAM sama sekali** (tidak ada `Add` maupun `Delete`) dan
`ResetNvramEntry.efi` di-disable. Section `NVRAM` dikembalikan; driver Reset
NVRAM sengaja tetap **disabled** supaya entry-nya tidak tampil (§13). Kalau kamu
ingin `boot-args`/`csr-active-config` yang kamu set dari dalam macOS bertahan
lintas reboot, hapus dua nama itu dari daftar `NVRAM > Delete`; untuk tahap
instalasi sebaiknya dibiarkan seperti sekarang.

---

## 7. Cara memakai validator

```bash
cd /storage/emulated/0/COMPARE
python3 validate-efi.py 2026/EFI
python3 validate-efi.py 2024/EFI
```

Yang dicek:

1. `config.plist` valid sebagai plist.
2. 8 section top-level ada.
3. `Misc > Security` lengkap + konsistensi `Vault` vs `Vault.plist`/`Vault.sig`.
4. Semua SSDT, kext bundle, executable kext, dan driver `.efi` yang direferensikan benar-benar ada.
5. Urutan kext dasar (Lilu paling awal, plugin setelah induk).
6. SMBIOS, `boot-args`, `RequestBootVarRouting`, `AvoidRuntimeDefrag`.

Exit code: `0` = tidak ada error struktur, `2` = ada error.
Tool ini bukan pengganti `ocvalidate` resmi, tapi cukup untuk mendeteksi
config tidak lengkap seperti kasus ini (tanpa perlu PC/Linux x86).

---

## 8. Cara deploy ke USB / ESP

Struktur yang harus ada (folder `2026` sudah siap):

```
EFI/
├── BOOT/
│   └── BOOTx64.efi
└── OC/
    ├── OpenCore.efi
    ├── config.plist          <-- versi hasil perbaikan
    ├── ACPI/*.aml            (14 file)
    ├── Drivers/*.efi         (6 file)
    ├── Kexts/*.kext          (31 bundle)
    └── Resources/            (Audio, Font, Image, Label)
```

Langkah:

1. Backup isi ESP lama (`cp -a EFI EFI.backup`).
2. Copy folder `EFI` hasil perbaikan ke root ESP (harus ada `EFI/BOOT/BOOTx64.efi`).
3. Reset NVRAM **tidak lagi tersedia di picker** (driver `ResetNvramEntry.efi`
   di-disable atas permintaan). Kalau tetap perlu wipe NVRAM, lihat §13.
4. Boot ke installer.

Kalau menyalin dari Android/Termux, pastikan tidak ada file 0 byte / terpotong:

```bash
find 2026/EFI -type f -size 0
```

---

## 9. Kalau nanti mau benar-benar update ke OpenCore baru

Perbaikan hari ini mengembalikan **boot**, bukan memodernkan OpenCore. Binary-nya
masih build 2023. Untuk update sungguhan (butuh koneksi internet ke GitHub
Acidanthera):

1. Unduh **zip rilis lengkap** `OpenCore-x.x.x-RELEASE.zip` (jangan cuma `OpenCore.efi`).
2. Ganti **bersamaan**:
   - `EFI/OC/OpenCore.efi`
   - `EFI/BOOT/BOOTx64.efi`
   - **semua** `EFI/OC/Drivers/*.efi` (terutama `OpenRuntime.efi` — versi-locked)
   - kext ke versi terbaru dari rilis yang sama
   - `EFI/OC/Resources` (dari `OpenCanopy` package)
3. **Jangan** mencampur binary baru dengan `OpenRuntime.efi` lama → hang/error aneh.
4. Migrasi config: buka `2024/EFI/OC/config.plist` di **OCAT (OpenCore Auxiliary Tools)**.
   OCAT menandai key baru/berubah dan bisa "upgrade" skema. Simpan hasilnya.
5. Validasi wajib sebelum boot:
   ```bash
   Utilities/ocvalidate/ocvalidate EFI/OC/config.plist     # harus "No issues found"
   python3 validate-efi.py EFI
   ```
6. Jangan memakai `config.plist.bak-2026-broken` sebagai basis apa pun.

Aturan penting lain: **config dan binary harus berasal dari generasi yang sama.**
Config 0.9.3 dipakai dengan OpenCore 1.0.x akan melewatkan key wajib baru dan
bisa memunculkan error yang mirip-mirip vault.

---

## 10. Troubleshooting kalau masih gagal

1. **Pastikan yang terpakai benar-benar config baru.** Cek di ESP:
   `md5sum /path/ESP/EFI/OC/config.plist` harus `9b0294841663b13c997f5a42698430d2`.
2. Kalau pesan vault masih muncul → config di ESP masih yang lama, atau nilainya
   `Basic`/`Secure`. Jangan tambal dengan membuat `Vault.plist`; set
   `Misc > Security > Vault = Optional` (vault hanya untuk verifikasi integritas,
   bukan keamanan, dan harus di-generate ulang setiap config berubah).
   Kalau tetap mau vault: `Utilities/CreateVault/create_vault.sh` → hasilkan
   `Vault.plist` + `Vault.sig` di `EFI/OC/`.
3. Aktifkan log untuk melihat titik henti:
   ```
   Misc > Debug > AppleDebug        = true
   Misc > Debug > Target            = 67   (file log di ESP: EFI/OC/opencore-*.log)
   Misc > Debug > DisplayLevel      = 2147483650
   NVRAM > boot-args                = keepsyms=1 -v
   ```
   Setelah berhasil boot, kembalikan `Target = 3` agar ESP tidak penuh log.
4. Cek `SecureBootModel = Disabled` dan `ScanPolicy = 0`.
5. HP/ThinkPad: jika hang sebelum picker, coba `Booter > Quirks > EnableWriteUnprotector = true`
   (sudah aktif), `SetupVirtualMap = true` (sudah aktif), dan `RebuildAppleMemoryMap`.

---

## 11. Catatan WiFi per versi macOS

Di config hasil perbaikan hanya **`AirportItlwm_Ventura.kext`** yang enable.
Sesuaikan dengan target instalasi:

| macOS | Kext yang enable |
|---|---|
| Big Sur (11) | `AirportItlwm_BigSur.kext` |
| Monterey (12) | `AirportItlwm_Monterey.kext` |
| Ventura (13) | `AirportItlwm_Ventura.kext` (default sekarang) |
| Sonoma (14) / Sequoia (15) | `AirportItlwm` tidak didukung → pakai `itlwm.kext` + HeliPort |

Selalu enable **hanya satu** dari kext WiFi tersebut, dan taruh setelah `Lilu`.

---

## 12. Checklist sebelum boot

- [x] `config.plist` valid & 8 section lengkap
- [x] `Misc > Security` lengkap, `Vault = Optional`
- [x] `SecureBootModel = Disabled`, `ScanPolicy = 0`
- [x] Semua SSDT/kext/driver yang direferensikan ada
- [x] `Lilu` paling awal, plugin setelah induk
- [x] `Booter > AvoidRuntimeDefrag = true`, `Kernel > AppleXcpmCfgLock = true`
- [x] `PlatformInfo > SystemProductName` terisi
- [x] `ResetNvramEntry.efi` disabled (entry "Reset NVRAM" tidak tampil, §13)
- [ ] `SystemSerialNumber` diisi (opsional untuk instalasi, wajib untuk iServices)
- [ ] `OpenCore.efi` + `OpenRuntime.efi` versi baru (kalau nanti update)

---

## 13. Entry "Reset NVRAM" di picker dimatikan

Permintaan: entry **Reset NVRAM** jangan muncul di picker OpenCore.

Perubahan (hanya 1 nilai, di `2026/EFI/OC/config.plist`):

```
UEFI > Drivers
  Path      = ResetNvramEntry.efi
  Enabled   = true  ->  false        <-- diubah
  LoadEarly = false
```

Efek:

- Entry **"Reset NVRAM"** tidak lagi ditampilkan di picker (entry itu dibuat
  oleh driver `ResetNvramEntry.efi`; driver nonaktif = tidak ada entry).
- File `EFI/OC/Drivers/ResetNvramEntry.efi` **tetap ada** di folder — hanya
  tidak dimuat. Tidak ada fungsi lain yang terpengaruh.
- `ToggleSipEntry.efi` tetap aktif, jadi entry **Toggle SIP** masih muncul.
- `NVRAM > Add` / `NVRAM > Delete` **tidak berubah**; `NVRAM > Delete` tetap
  menghapus `boot-args`/`csr-active-config`/`rtc-blacklist`/`UIScale`/
  `DefaultBackgroundColor` setiap boot seperti sebelumnya (itu bukan "reset
  NVRAM", itu overwrite variabel tertentu).
- Validasi ulang: `python3 validate-efi.py 2026/EFI` → `OK`, 0 error.

### Kalau nanti perlu wipe NVRAM

Urutan pilihan:

1. Dari macOS: `sudo nvram -c` lalu reboot (paling bersih, tanpa ubah config).
2. Sementara aktifkan lagi entry-nya: set `Enabled = true` pada
   `UEFI > Drivers > ResetNvramEntry.efi`, simpan, boot, pilih **Reset NVRAM**,
   lalu kembalikan ke `false`.
3. Alternatif "sembunyikan tanpa mematikan": set `Misc > Boot > HideAuxiliary = true`.
   Entry Reset NVRAM/Toggle SIP (entry auxiliary) hanya muncul kalau kamu tekan
   **Space** di picker. Catatan: cara ini juga menyembunyikan Recovery dan
   Time Machine sampai Space ditekan.

Yang **tidak** disarankan: menghapus file `ResetNvramEntry.efi` dari folder
`Drivers`. Bisa, tapi menghilangkan opsi pemulihan darurat dan bikin bingung
saat troubleshooting; menonaktifkan lewat config sudah cukup.

---

## 14. Entry "Toggle SIP" — apa itu

`ToggleSipEntry.efi` menambahkan entry **Toggle SIP** di picker. Fungsinya:
menyalakan/mematikan **SIP (System Integrity Protection)** dengan cepat, tanpa
mengedit `config.plist`. Caranya: driver membaca lalu menulis variabel NVRAM
`csr-active-config`. Bukti dari binary-nya:

```
BEP: ToggleSip failed to read csr-active-config, aborting!
Toggle SIP (0x%X:%a)
BEP: Specified value 0x%X will not disable SIP!
```

SIP sendiri adalah fitur keamanan macOS yang melindungi file sistem, kext,
NVRAM, dan proses debug dari perubahan. `csr-active-config` = bitmask saklar
SIP:

| Nilai | Arti (umum) |
|---|---|
| `0x00000000` | SIP aktif penuh (paling aman) |
| `0x00000003` | SIP nonaktif (nilai klasik) |
| `0x00000067` | SIP nonaktif + unsigned kexts (umum di Big Sur+) |
| `0x00000077` / `0xFF` | lebih permisif lagi (untuk kebutuhan khusus) |

Status di config `2026`:

```
NVRAM > Add  > 7C436110…  > csr-active-config = 00000000   → SIP AKTIF penuh
NVRAM > Delete > 7C436110… > [boot-args, csr-active-config] → dihapus tiap boot
UEFI > Drivers > ToggleSipEntry.efi = enabled               → entry muncul
UEFI > Drivers > ToggleSipEntry Arguments = ""              → nilai bawaan driver
```

Konsekuensi penting: karena `csr-active-config` ada di `NVRAM > Delete` **dan**
ditulis ulang `0x0` oleh `NVRAM > Add`, hasil toggle akan **di-reset ke SIP
aktif pada boot berikutnya**. Kalau mau toggle/perubahan SIP bertahan, hapus
`csr-active-config` dari `NVRAM > Delete` (dan sesuaikan `Add`-nya).

Saran: untuk instalasi biasa biarkan SIP **aktif**. SIP hanya perlu dimatikan
kalau panduan/alat tertentu memintanya (root patching/OCLP, kext unsigned
tertentu, debug AMFI). Kalau entry Toggle SIP tidak diinginkan, set
`UEFI > Drivers > ToggleSipEntry.efi > Enabled = false` — sama seperti
ResetNvramEntry, entry langsung hilang dari picker.

---

## 15. Isi picker saat ini (snapshot config 2026)

Tampilan: **OpenCanopy grafis** (`PickerMode = External`, `OpenCanopy.efi` ON)
dengan tema `Acidanthera\GoldenGate` (folder
`Resources/Image/Acidanthera/GoldenGate` ada, 22 ikon), resolusi `Max`,
`PickerAudioAssist = false` (VoiceOver mati), chime `Auto` via `AudioDxe.efi`.
`ShowPicker = true`, `Timeout = 5` detik → otomatis boot entri default.

### Entry yang pasti tampil (dari driver)

| Entry | Sumber | Status |
|---|---|---|
| **Toggle SIP** | `ToggleSipEntry.efi` | tampil (icon Tool) |
| Reset NVRAM | `ResetNvramEntry.efi` | **tidak tampil** (driver OFF) |
| OpenShell / EFI Shell | `Misc > Tools` | tidak ada (array kosong, `OpenShell.efi` juga tidak ada) |

### Entry boot (hasil scan disk, `ScanPolicy = 0`)

| Kategori | Tampil? | Keterangan |
|---|---|---|
| macOS terpasang (APFS) | ya | APFS built-in + `EnableJumpstart = true` |
| Installer macOS / USB installer | ya | |
| Recovery macOS | ya | entry auxiliary, terlihat karena `HideAuxiliary = false` |
| Snapshot Time Machine | ya | auxiliary |
| Windows Boot Manager | ya, kalau ada | |
| Linux / EFI loader lain | ya, kalau ada | `ScanPolicy = 0` memindai semua device & filesystem |
| Volume HFS+ | ya | via `HfsPlus.efi` |
| Volume FileVault | ya | muncul ikon Lock/Password |

`Misc > Entries` dan `BlessOverride` kosong, jadi tidak ada entry custom.
`LauncherOption = Disabled`, jadi OpenCore tidak menambahkan entry dirinya ke
boot menu firmware (hanya entry yang sudah ada).

### Perilaku keyboard

- `Ctrl+Enter` = set entri terpilih sebagai default (`AllowSetDefault = true`)
- `Space` = menampilkan entry auxiliary — saat ini tidak perlu karena
  `HideAuxiliary = false`
- `PollAppleHotKeys = true` → hotkey ala Apple aktif: `Cmd+R` (Recovery),
  `Cmd+S`, `Cmd+V`, dan **`Cmd+Opt+P+R` (reset NVRAM)**.

Catatan: entry "Reset NVRAM" sudah disembunyikan, tapi hotkey
`Cmd+Opt+P+R` masih bisa mereset NVRAM selama `PollAppleHotKeys = true`. Kalau
ingin benar-benar tidak ada jalan reset NVRAM dari picker, set
`Misc > Boot > PollAppleHotKeys = false` (efek samping: hotkey `Cmd+R`/`Cmd+V`
ikut mati).

Kalau ingin tampilan teks (bukan grafis): `Misc > Boot > PickerMode = Builtin`
(OpenCanopy tidak dipakai).
