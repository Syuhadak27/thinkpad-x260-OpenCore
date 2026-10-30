#!/usr/bin/env python3
# Validator sederhana untuk EFI OpenCore (tanpa perlu ocvalidate / PC).
# Cek: plist valid, section wajib ada, nilai Vault, semua file yang
# direferensikan config benar-benar ada di folder EFI.
#
# Pakai:  python3 validate-efi.py <folder-EFI>
# Contoh: python3 validate-efi.py 2026/EFI

import os
import plistlib
import sys

TOP_LEVEL = ["ACPI", "Booter", "DeviceProperties", "Kernel", "Misc", "NVRAM", "PlatformInfo", "UEFI"]
SECURITY_KEYS = ["AllowSetDefault", "ApECID", "AuthRestart", "BlacklistAppleUpdate",
                 "DmgLoading", "EnablePassword", "ExposeSensitiveData", "HaltLevel",
                 "PasswordHash", "PasswordSalt", "ScanPolicy", "SecureBootModel", "Vault"]

errors, warnings = [], []


def err(msg): errors.append(msg)
def warn(msg): warnings.append(msg)


def main(efi):
    oc = os.path.join(efi, "OC")
    cfg_path = os.path.join(oc, "config.plist")

    if not os.path.isfile(cfg_path):
        print(f"FATAL: {cfg_path} tidak ada")
        return 1

    try:
        with open(cfg_path, "rb") as f:
            cfg = plistlib.load(f)
    except Exception as ex:
        print(f"FATAL: config.plist bukan plist valid: {ex}")
        return 1

    # 1. Section top-level
    for k in TOP_LEVEL:
        if k not in cfg:
            err(f"section top-level hilang: {k}")

    # 2. Misc > Security (sumber error vault)
    sec = cfg.get("Misc", {}).get("Security")
    if sec is None:
        err("Misc > Security hilang -> Vault tidak bisa dibaca (penyebab "
            "'Configuration requires vault but no vault provided')")
    else:
        for k in SECURITY_KEYS:
            if k not in sec:
                err(f"Misc > Security > {k} hilang")
        vault = sec.get("Vault", "<tidak ada>")
        has_vault = os.path.isfile(os.path.join(oc, "Vault.plist")) and \
                    os.path.isfile(os.path.join(oc, "Vault.sig"))
        if vault == "Optional":
            if has_vault:
                warn("Vault=Optional tapi Vault.plist/Vault.sig masih ada (tidak masalah)")
        elif vault in ("Basic", "Secure"):
            if not has_vault:
                err(f"Vault={vault} tapi Vault.plist/Vault.sig tidak ada -> boot berhenti")
            if vault == "Secure" and not sec.get("ApECID"):
                warn("Vault=Secure biasanya butuh penanganan public key khusus")
        else:
            err(f"nilai Vault tidak dikenal: {vault}")

    # 3. File yang direferensikan harus ada
    for entry in cfg.get("ACPI", {}).get("Add", []):
        p = os.path.join(oc, "ACPI", entry.get("Path", ""))
        if entry.get("Path") and not os.path.isfile(p):
            err(f"ACPI.Add -> file tidak ada: {p}")

    for entry in cfg.get("Kernel", {}).get("Add", []):
        bundle = entry.get("BundlePath", "")
        if not bundle:
            continue
        p = os.path.join(oc, "Kexts", bundle)
        if not os.path.isdir(p):
            err(f"Kernel.Add -> bundle tidak ada: {p}")
        exe = entry.get("ExecutablePath", "")
        if exe and not os.path.isfile(os.path.join(p, exe)):
            err(f"Kernel.Add -> executable tidak ada: {p}/{exe}")

    for d in cfg.get("UEFI", {}).get("Drivers", []):
        p = os.path.join(oc, "Drivers", d.get("Path", ""))
        if d.get("Path") and not os.path.isfile(p):
            err(f"UEFI.Drivers -> file tidak ada: {p}")

    for f in ("OpenCore.efi", "BOOTx64.efi"):
        p = os.path.join(oc, f) if f == "OpenCore.efi" else os.path.join(efi, "BOOT", f)
        if not os.path.isfile(p):
            err(f"file wajib tidak ada: {p}")

    # 4. Urutan kext (dependency dasar)
    order = [e["BundlePath"] for e in cfg.get("Kernel", {}).get("Add", []) if e.get("Enabled")]
    for i, b in enumerate(order):
        if b == "Lilu.kext" and i != 0:
            warn(f"Lilu.kext sebaiknya paling awal (sekarang index {i})")
    deps = {
        "WhateverGreen.kext": "Lilu.kext",
        "AppleALC.kext": "Lilu.kext",
        "VirtualSMC.kext": "Lilu.kext",
        "AirportItlwm_BigSur.kext": "Lilu.kext",
        "AirportItlwm_Monterey.kext": "Lilu.kext",
        "AirportItlwm_Ventura.kext": "Lilu.kext",
        "CPUFriend.kext": "Lilu.kext",
        "FeatureUnlock.kext": "Lilu.kext",
        "HibernationFixup.kext": "Lilu.kext",
        "NVMeFix.kext": "Lilu.kext",
        "RTCMemoryFixup.kext": "Lilu.kext",
        "SMCBatteryManager.kext": "VirtualSMC.kext",
        "SMCProcessor.kext": "VirtualSMC.kext",
        "CPUFriendDataProvider.kext": "CPUFriend.kext",
        "VoodooRMI.kext/Contents/PlugIns/RMISMBus.kext": "VoodooRMI.kext",
        "VoodooRMI.kext/Contents/PlugIns/RMII2C.kext": "VoodooRMI.kext",
        "VoodooI2CHID.kext": "VoodooI2C.kext",
    }
    for child, parent in deps.items():
        if child in order and parent in order and order.index(child) < order.index(parent):
            warn(f"urutan kext: {child} dimuat sebelum induknya ({parent})")

    # 5. Info SMBIOS / NVRAM
    gen = cfg.get("PlatformInfo", {}).get("Generic", {})
    if not gen.get("SystemProductName"):
        err("PlatformInfo > Generic > SystemProductName kosong")
    if cfg.get("PlatformInfo", {}).get("Automatic") and not gen.get("SystemSerialNumber"):
        warn("SystemSerialNumber kosong (boot bisa, iServices/serial tidak)")
    nv = cfg.get("NVRAM", {}).get("Add", {}).get("7C436110-AB2A-4BBB-A880-FE41995C9F82", {})
    if not nv.get("boot-args"):
        warn("boot-args tidak diset di NVRAM")
    q = cfg.get("UEFI", {}).get("Quirks", {})
    if "RequestBootVarRouting" not in q:
        err("UEFI > Quirks > RequestBootVarRouting hilang")
    bq = cfg.get("Booter", {}).get("Quirks", {})
    if "AvoidRuntimeDefrag" not in bq:
        err("Booter > Quirks > AvoidRuntimeDefrag hilang")

    # 6. Ringkasan konfigurasi penting
    print(f"== {efi} ==")
    print(f"  Vault              : {sec.get('Vault') if sec else '<MISSING>'}")
    if sec:
        print(f"  SecureBootModel    : {sec.get('SecureBootModel')}")
        print(f"  ScanPolicy         : {sec.get('ScanPolicy')}")
    print(f"  SMBIOS             : {gen.get('SystemProductName', '-')}")
    print(f"  boot-args          : {nv.get('boot-args', '-')}")
    print(f"  Kext enabled       : {len(order)}")
    print(f"  WiFi aktif         : {[b for b in order if b.startswith('AirportItlwm')] or 'tidak ada'}")

    print()
    for w in warnings:
        print(f"  WARN  : {w}")
    for e in errors:
        print(f"  ERROR : {e}")
    if not errors:
        print("  HASIL : OK - tidak ada error struktur (peringatan boleh diabaikan)")
        return 0
    print(f"  HASIL : {len(errors)} error")
    return 2


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Pakai: python3 validate-efi.py <folder-EFI>")
        sys.exit(1)
    sys.exit(main(sys.argv[1]))
