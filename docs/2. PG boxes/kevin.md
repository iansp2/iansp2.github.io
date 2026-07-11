---
tags:
  - Proving Grounds
  - Windows

icon: simple/gnometerminal
---


# Kevin

!!! info "Box details"  
    https://portal.offsec.com/machine/kevin-189/overview/details  
    **Difficulty:** Easy  
    **OS:** Windows

## Recon

Nmap output:
```
80/tcp    open  http          GoAhead WebServer
135/tcp   open  msrpc         Microsoft Windows RPC
139/tcp   open  netbios-ssn   Microsoft Windows netbios-ssn
445/tcp   open  microsoft-ds  Windows 7 Ultimate N 7600 microsoft-ds (workgroup: WORKGROUP)
3389/tcp  open  ms-wbt-server Microsoft Terminal Service
3573/tcp  open  tag-ups-1?
49152/tcp open  msrpc         Microsoft Windows RPC
49153/tcp open  msrpc         Microsoft Windows RPC
49154/tcp open  msrpc         Microsoft Windows RPC
49155/tcp open  msrpc         Microsoft Windows RPC
49158/tcp open  msrpc         Microsoft Windows RPC
49160/tcp open  msrpc         Microsoft Windows RPC
```

## Enumeration

Besides the above, nmap also have us the host name kevin and the OS version of Windows 7 Ultimate N 7600. Port 3573 seems to be "Advantage Group UPS Suite", which now seems to be HP Power Manager. Visiting port 80 in our browser, we see a login page for HP Power Management at http://192.168.233.45/index.asp (makes sense).

SMB seems to have null auth enabled, but shares and user enumeration is denied (tested with nxc). 

Port 80 seems like the most promissing surface, so let's focus there. Looking at the source code for the page, we can also see /Contents/index.asp as a path, but visiting it doesn't give us anything if we're not loged in. There are a few interesting js functions that I might revisit again later if I don't find credentials for this page. No version number could be identified for this webpage.

## Foothold and root

Looking for CVEs for Power Manager, we find 4 critical ones (all between 2009 and 2010). A couple of them seem to give us anauthenticated RCE and have public exploits, so let's try them out.  
- CVE-2009-2685: found a POC online (https://github.com/fuzzlove/buffer_overflows/blob/master/HP_Power_Manager_Administration_Universal_Buffer_Overflow.py). Made some edits to the exploit (e.g., changing the shellcode, changing some strings to bytes, etc.) but couldn't get it to work. It did crash the server, which makes me think the system is vulnerable and it's just that I couldn't adapt the POC. I found another POCc(https://github.com/CountablyInfinite/HP-Power-Manager-Buffer-Overflow-Python3) written already for python3 (as opposed to the previous one which was for python2), but still couldn't get it to work. I edited the shellcode and the egghunter bit, but couldn't get it to work.  
- CVE-2009-3999: found a POC online (https://github.com/AC8999/CVE-2009-3999-HP-Power-Manager-4.2-Build-7-Buffer-Overflow) and this one actually generates the shellcode for you (yay). This worked and we directly get a shell as NT Authority.

All the exploits seemed clearly made for this particular box, and yet I could only get 1 out of 3 to work. Not great, I guess. But I think the overall strategy of not fixating on the one that didn't work and instead move on to the next was correct. Given no coding skills and no LLMs allowed for OSCP, a POC basically has to work out of the box for me to leverage it.

## Remediation notes

Don't use software with vulnerabilities from almost 20 years ago, I guess?

## After reading briefing

Two things I missed:
- Default creds would've given me access to enumerate version  
- There was a msf console exploit for this
