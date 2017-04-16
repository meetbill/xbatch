## xbatch-function


<!-- vim-markdown-toc GFM -->
* [run xb](#run-xb)
* [upload](#upload)
* [download](#download)
* [交互模式](#交互模式)
* [二次开发接口](#二次开发接口)
* [同步本地文件到其他服务器](#同步本地文件到其他服务器)

<!-- vim-markdown-toc -->
### run xb

通过执行 xb 命令获取 xb 帮助手册

Execute xb for help

```
xb
```

### upload

上传文件

Usage:xb put local_file remote_dir

### download

下载文件

Usage:xb get remote_file local_dir

### 交互模式

Usage:xb cmd

### 二次开发接口

这种模式是为了可以方便二次开发
```
#/usr/bin/xb arch "commands"

如下
#/usr/bin/xb arch "date"
执行结果后会将所有机器得到的数据放到程序中的 output 变量中
output 是个列表，output 中的每个元素也都是列表，元素的值为每个服务器获取到的值
```
### 同步本地文件到其他服务器

```
#/usr/bin/xb sync local_file
```
执行此程序将会将本地 local_file 文件同步到配置文件中的机器中

此功能是比较实用的，更新多台同样的服务的时候，在一台机器服务更新好后，将此机器的已配置好的配置同步到其他机器
