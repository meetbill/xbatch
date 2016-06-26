## xbatch-function

+ Interactive mode(default)   

+ cmd mode   

### Interactive mode

Interactive mode, you can bulk upload and download files, you can also execute

commands on a remote host

just run:
```
xb
```
When you select the interactive mode, you can "use sys" and "use ftp" to enter

configuration mode and ftp mode, enter configuration mode and ftp mode can enter

"?" to display help information

### cmd

run'xb -h' to display help information
```
xb -h
```
#### (1)upload

Usage:xb -t upload -s sourcefile -d destination-file

Example:
```
/usr/bin/xb  -t upload   -s /local/file  -d /remote/dir
```
#### (2)download

Usage:xb -t download -s sourcefile -d destination-file

Example:
```
 /usr/bin/xb  -t download -s /remote/file -d /local/dir
```
#### (3)cmd inspection

This mode is mainly used for timing tasks inspection, return results only

recorded in the log, the contents are not displayed on the screen return

Usage:xb -t cmd --cmd commands

Example:
```
/usr/bin/xb -t cmd --cmd ls
```
### the difference of interactive and cmd mode

(1)the interactive mode can select a specific host batch operation, but the 

command line mode may operate all hosts.

