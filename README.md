# 1Password Importer for LastPass CSV Exports

When I was trying to import a LastPass CSV into 1Password, it did some weird things (like setting the name to the notes field!). So, I created a script that reads items from a LastPass-exported CSV and adds them to 1Password via the CLI tool.

This script makes a few assumptions about your items:
* **No attachments** (LP doesn't include them in exports, make sure to get them before deleting your account!).
* Currently only supports **secure notes, logins, databases and servers** (they are what I needed). Support for more types can be added pretty easily. See lines 8-55 of `main.py`.
* **Folder names with double quotes or commas may break things.** Tags are placed into the 1PW command without escaping, so I've no idea how this may break.
* Forward slashes in folder names are converted to ampersands (`&`) as they indicate nested tags in 1PW. This can be changed on line 59 of `main.py`.
* Non-login items are denoted by a URL of `http://sn` (LP provides no clearer distinction between logins and other items).
* Any secure note starting with `NoteType:` is a special type of secure note (e.g. database, server) and will be parsed as such.
  * The line beginning with `Notes:` indicates the beginning of free text for these special types and no other fields will be read.

To run it, clone this repo, sign in to `op` ([you'll need to set it up if you haven't already](https://1password.com/downloads/command-line/)) and run the script with `python3 main.py`. This has been tested on Linux, but is likely to work on MacOS, maybe on Windows (but definitely WSL). Note that a temporary file **with sensitive data**, `tmp.json`, is created. It should be removed automatically at the end of the script (or if you interrupt with Ctrl+C) unless the script crashes.