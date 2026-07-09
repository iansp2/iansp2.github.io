---
tags:
  - HTB
  - Linux
  - Chrome
  - Browser extension

icon: simple/gnometerminal
---


# Browsed

!!! info "Box details"  
    https://app.hackthebox.com/machines/Browsed
    **Difficulty:** Medium
    **OS:** Linux

> ippsec video: [youtube.com](https://www.youtube.com/watch?v=duyqJWbzQQk)  
> 0xdf blog: [0xdf.gitlab.io](https://0xdf.gitlab.io/2026/03/28/htb-browsed.html)


## Enumeration

nmap shows just 2 ports open:
``` text
22/tcp open  ssh
80/tcp open  http

```
Browsing to port 80, we can find a website where you can upload file extensions and they say they will test it. I assume there's a script that installs and executes whatever browser extension I give it. Doign some digging on browser extension attacks:  
- https://hacktricks.wiki/en/pentesting-web/browser-extension-pentesting-methodology/index.html  
- https://spaceraccoon.dev/universal-code-execution-browser-extensions/

A lot of it is about how the extension can install without the user's consent, which is not relevant to us here (since I assume the script will install whatever we give it). There's also somethings about how to calculate the correct signature, but looking at the examples the web app provides, they don't have signatures - so I think I can skip that. So they thing is to figure out what I need to submit that will give me something interesting (preferably RCE, but possibly cookies to access the website as admin).

Example extension they give:

``` text
$ tree 

fontify/
├── content.js
├── manifest.json
├── popup.html
├── popup.js
└── style.css
```

Looking for Github PoCs we find this one: https://github.com/mttaggart/crux. I changed the const SERVER_HOST for my listening ip, compress everything into a zip (as per the box's instructions), and upload.


## Foothold

## Privilege Escalation

## Root

## Remediation notes

