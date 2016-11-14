#!/usr/bin/python
#coding=utf8
"""
# Author: Bill
# Created Time : 2016年04月06日 星期三 09时23分41秒

# File Name: init_install.py
# Description:

"""
import os
import commands
def init_install(dir_conf,dir_log,dir_home):
    file_hosts="%s/hosts" %dir_conf
    file_conf="%s/xbatch.conf" %dir_conf
    INITDIR="%s %s/flag  %s %s/bin %s/version" %(dir_log,dir_home,dir_conf,dir_home,dir_home)
    if commands.getstatusoutput("mkdir -p %s 2>/dev/null" % (INITDIR))[0]!=0:
        print "Create Directory Failed"
        sys.exit(1)
    if not os.path.isfile('%s'%file_conf):
        T=open('%s' % file_conf,'w')
        T.write("""[X_batch]
#Author=Bill
Useroot=N
RunMode=M
#请在%s/hosts中指定主机的账户名，密码，端口等信息
#Timeout=3
#sudo=sudo su - root
UseKey=Y
#Key的位置默认是在~/.sshd/id_rsa
#Deployment=N
#ListenFile=/var/log/messages
#ListenTime=60
#ListenChar=Server startup"""%dir_log)
        T.close()
    if not os.path.isfile('%s'%file_hosts):
        T=open('%s'%file_hosts,'w')
        T.write("""[xserver]
#主机地址===端口===登陆账户===登陆密码===su-root密码
#127.0.0.1===22===root===None===None
#[mysqlm]
#[mysqls]
#支持多个主机组
#如果您担心安全问题，在密码列位置，您可以使用...===None===...表示不在配置文件中指定，而是在您执行命令的时候系统会询问您密码。比如以下配置:
#127.0.0.1===22===root===None===None
#locallhost===22222===root===Your-root's-password===su-root的密码,如果没有使用Useroot，此列也可以填写None

#None的特殊指定只能针对密码特别指定，不能在账户名，或者是端口，主机这三列中使用
#比如你想要1.1.1.1重复出现， 那么可以给1.1.1.1定义一个主机名a.com， 然后分别用1.1.1.1 和a.com区分
#注意:在每一个配置中，请不要有空格或者是制表符!
#在所有的配置列中，请用三个等于（===）分割开，并确保有5列！""")
        T.close()
