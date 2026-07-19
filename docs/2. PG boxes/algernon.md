---
tags:
  - PG
  - OffSec
  - Windows

icon: simple/gnometerminal
---


# Algernon

!!! info "Box details"  
    https://portal.offsec.com/machine/algernon-239/overview  
    **Difficulty:** Easy  
    **OS:** Windows

## Enumeration

Nmap output (filtered high ports):  

|Port|Service|
| --- | ----- |
|21|FTP|
|80|HTTPi - IIS default page|
|135|RPC|
|139|NetBios|
|445|SMB|
|5040|RPC?|
|9998|HTTP - SmarterMail|
|17001|.NETSystem.Runtime.Remoting?|


### FTP

FTP has anonymous access enabled:
```
$ ftp anonymous@192.168.237.65

Connected to 192.168.237.65.
220 Microsoft FTP Service
331 Anonymous access allowed, send identity (e-mail name) as password.
Password: 
230 User logged in.
Remote system type is Windows_NT.

ftp> ls
229 Entering Extended Passive Mode (|||49887|)
125 Data connection already open; Transfer starting.
04-29-20  10:31PM       <DIR>          ImapRetrieval
07-19-26  01:24AM       <DIR>          Logs
04-29-20  10:31PM       <DIR>          PopRetrieval
04-29-20  10:32PM       <DIR>          Spool
226 Transfer complete.
```

The only directory with contents is the Log directory. I can find reference to webmail user admin being created and password being set, but I can't see what the password is.

### SMB

Null sessions do not seem to be enabled.

### SmarterMail

Could not enumerate the version for this service. But just decided to go to CVE Details and see what shows up. There are lots of CVEs, quite a few with high severity, and two with public exploits:  
- CVE-2025-52691: file upload  
- CVE-2019-7214: RCE  

## Foothold (and root)

For the first, I found the following PoC: https://github.com/watchtowrlabs/watchTowr-vs-SmarterMail-CVE-2025-52691/. It acts as a scanner, and in our case it does seem like the service is vulnerable. My immediate thought process is to upload a webshell somewhere. Since IIS default page is there in port 80, maybe I can just upload something to C:\inetpub\wwwroot\? Having that said, on the scanner I don't see an easy way to pick upload destination. It's basically just a POST to /api/upload endpoint. Let's look at the other exploit first.

Just looking at the description of the CVE, it definitely seems like we're in the right path. It says one of the requirements we have in order to exploit is TCP port 17001 needs to be open (which we already know it is). I could find this PoC: https://github.com/devzspy/CVE-2019-7214/. Edited the variables for the local and remote IPs and we get a shell. Not only that, it's straight as NT Authority!

I think the important conclusion here is not to get too deep in any particular path, go broad first. I could've spent a lot of time on FTP, SMB, file upload, etc. but luckily moved quickly through multiple things until we get an easy NT Authority shell. For OSCP I think I need to keep the same mindset: keep moving through things quickly and only spend time when you're sure there are no other low-hanging fruits.
