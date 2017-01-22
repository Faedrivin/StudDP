# StudDP
StudDP is a file downloader for [Stud.IP](http://studip.de/). It uses the
[Stud.IP: Rest.IP](http://studip.github.io/studip-rest.ip/) plugin to download files
when they changed or are not existent on the file system.

## Setup

To set it up, do the following:

Install via pip:
```sh
pip install StudDP
```

######  or alternatively:

```sh
git clone https://github.com/MSchuwalow/StudDP
cd StudDP
pip install -r requirements.txt
```

Note:
If you install manually you will have to run the included scripts as:
```sh
python -m studdp.StudDP
python -m studdp.stopDP
```

#### Modify the config.json:
```json
{
    "username": "",
    "base_address": "https://studip.uos.de/plugins.php/restipplugin",
    "local_path": "~/studip",
    "interval": 1200,
    "last_check": -1,
    "courses_selected": false,
    "courses": []
}
```

* `username` is your StudIP login name.
* `base_address` is the addres up to the root of your Rest.IP plugin. Leave out any trailing slashes.
* `local_path` is your local folder where files should be downloaded to.
* `interval` is the checking interval in seconds (so the default is 20 minutes).
* `last_check` is the last timestamp when checks were performed. This is set automatically.
* `courses_selected` tells the program if you have chosen your courses. This is set automatically.
* `courses` is your list of courses to download. This is set automatically.

## Run

When running for the first time, use:

```sh
StudDP.py
```

To get information about options, use:

```sh
StudDP.py -h

    Usage: StudDP.py [options]

    Options:
      -h, --help       show this help message and exit
      -c, --config     change course selection
      -v, --verbose    print log to stdout
      -d, --daemonize  start as daemon
      -w, --windows    remove characters that are forbidden in windows paths
      -u, --update     update files when they are updated on StudIP
      -p, --password   force password update
```

When running it for the first time, it should prompt you for your StudIP password. It will then be stored in your login keyring. You therefore have to have
a keyring installed.

You will then see a ncurses interface which allows you to select the courses to download:

![](https://cdn.rawgit.com/MSchuwalow/StudDP/develop/Screenshots/Curses.png)

You can later use the -p and -c options to reconfigure your password and courses respectively.

## Running as a daemon

To run it as a daemon, use:

```sh
StudDP.py -d
```

To stop it the daemon, use:

```sh
stopDP
```

## Other information

To view the log use:

```sh
tail -f ~/.studdp/info.log
```

To uninstall use:

```sh
rm -rf StudDP
rm -rf ~/.studdp
```
