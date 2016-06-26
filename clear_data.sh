#!/bin/bash

X_BATCH_PATH=/opt/X_operations/X_batch
rm -f ${X_BATCH_PATH}/conf/hosts
find  ${X_BATCH_PATH}/bin -type f -name '*pyc' -exec rm -f {} \;
find  ${X_BATCH_PATH}/flag -type f  -exec rm -f {} \;
find  ${X_BATCH_PATH}/version -type f  -exec rm -f {} \;
rm -f ${X_BATCH_PATH}/logs/*
touch ${X_BATCH_PATH}/flag/test ${X_BATCH_PATH}/version/test
cat >/etc/xbatch/hosts<<EOF
[xserver]
#主机地址===端口===登陆账户===登陆密码===su-root密码
#[mysqlm]
#[mysqls]
#支持多个主机组
#如果您担心安全问题，在密码列位置，您可以使用...===None===...表示不在配置文件中指定，而是在您执行命令的时候系统会询问您密码。比如以下配置:
#127.0.0.1===22===root===None===None
#locallhost===222===root===your-root's-password===su-root的密码,如果没有使用Useroot，此列也可以填写None
#比如你想要1.1.1.1重复出现， 那么可以给1.1.1.1定义一个主机名a.com， 然后分别用1.1.1.1 和a.com区分
#None的特殊指定只能针对密码特别指定，不能在账户名，或者是端口，主机这三列中使用
#注意:在每一个配置中，请不要有空格或者是制表符!
#在所有的配置列中，请用三个等于（===）分割开，并确保有5列！
EOF
