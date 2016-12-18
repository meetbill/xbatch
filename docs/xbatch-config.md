## xbatch-config

* [(1)Password](#1password)
* [(2)Public Key(promote)默认](#2public-keypromote默认)

modify the configuration file to add the main login configuration of remote host

There are two ways to login to remote host

### (1)Password

config the file /etc/xbatch/hosts

if remote host user is root

the column 5 can be set to None

```
locallhost===22===root===your-root's-password===None
```

### (2)Public Key(promote)默认

config the file /etc/xbatch/xbatch.conf

modify the configuration file 

add UseKey=Y

```
UseKey=Y
```

修改需要管理的主机信息，配置文件为 /etc/xbatch/hosts

config the file /etc/xbatch/hosts

```
locallhost===22===root===None===None
```
