## xbatch-function


* [run xb](#run-xb)
* [upload](#upload)
* [download](#download)
* [交互模式](#交互模式)
* [二次开发接口](#二次开发接口)

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
