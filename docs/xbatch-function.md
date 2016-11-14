## xbatch-function

* [Interactive mode](#interactive-mode)
* [cmd](#cmd)
	* [(1)upload](#1upload)
	* [(2)download](#2download)
	* [(3)cmd inspection](#3cmd-inspection)
	* [(4)二次开发接口](#4二次开发接口)

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
the interactive mode can select a specific host batch operation, but the command line mode may operate all hosts.

#### (4)二次开发接口

这种模式是为了可以方便二次开发
```
#/usr/bin/xb -x "commands"

如下
#/usr/bin/xb -x "date"
执行结果后会将所有机器得到的数据放到程序中的 output 变量中

output = Excute_arch(servers_allinfo,option.exe)
print output

output 是个列表，output 中的每个元素也都是列表，元素的值为每个服务器获取到的值 
```
