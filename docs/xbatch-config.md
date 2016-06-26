## xbatch-config

modify the configuration file to add the main login configuration of remote host

There are two ways to login to remote host

### (1)Password

config the file /etc/xbatch/hosts

if remote host user is root

the column 5 can be set to None

```
locallhost===22===root===your-root's-password===None
```

### (2)Public Key(promote)

config the file /etc/xbatch/xbatch.conf

modify the configuration file 

add UseKey=Y

```
UseKey=Y
```

config the file /etc/xbatch/hosts

```
locallhost===22===root===None===None
```
