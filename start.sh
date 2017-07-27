#!/bin/bash
#Author=Bill
#coding:utf-8
export LANG=zh_CN.UTF-8
g_DIR_CUR=$(pwd)
g_DIR_PACK=${g_DIR_CUR}/Packages
g_DIR_XBATCH=${g_DIR_PACK}/X_batch
g_DIR_SOFT=${g_DIR_PACK}/soft
#{{{Check root 
if [ `id -u` -ne 0 ]
then
	echo "Must be as root install!"
	exit 1
fi
#}}}
echo  "Installing..."
DIR_INSTALL=/opt/X_operations/X_batch
DIR_CONF=/etc/xbatch
#{{{Python版本
function PythonVersion()
{

	cat <<EOFver|python
#coding:utf-8
import sys,time
ver=float(sys.version[:3])
if ver<=2.4:
	print "强烈警告! 您使用的python版本过低,建议升级python版本到2.6以上.\n可以使用yum update python更新"
	time.sleep(3)
EOFver
}
#}}}
#{{{InstallLocalYum
function InstallLocalYum()
{
	cd ${g_DIR_SOFT}
	YUM_BAK=/opt/yum_bak

	if [ -d ${YUM_BAK} ]
	then
		cp -rf /etc/yum.repos.d/* ${YUM_BAK}
	else
		mkdir -p ${YUM_BAK}
		cp -rf /etc/yum.repos.d/* ${YUM_BAK}
	fi
	
	rm -rf /etc/yum.repos.d/*
	cp ./xbatch.repo  /etc/yum.repos.d/
	tar -zxf packages_xbatch.tar.gz -C /opt
	return 0
}
#}}}
#{{{InstallTOOL
#
function InstallTOOL()
{
	rpm  -qa|grep gcc -q
	if  [ $? -ne 0 ]
	then
		yum  install -y gcc
	fi
	rpm  -qa|grep python-devel -q
	if [ $? -ne 0 ]
	then
		echo "install python-devel"
		yum install -y python-devel
	fi
	return 0
}
#}}}
#{{{InstalEnv
function InstalEnv()
{
	##判断是否有paramiko
cat<<EOF|python
import os
import sys
try:
    import paramiko
except AttributeError:
    print
    os.system("""sed  -i '/You should rebuild using libgmp/d;/HAVE_DECL_MPZ_POWM_SEC/d'  /usr/lib64/python*/site-packages/Crypto/Util/number.py       /usr/lib/python*/site-packages/pycrypto*/Crypto/Util/number.py""")
except:
    sys.exit(1)
EOF

##################################################################
if [ $? -ne 0 ]
then
    echo "当前没有paramiko"
	cat<<EOFcrypto|python
import sys
try:
	import Crypto
except:
	sys.exit(1)
EOFcrypto
	if [ $? -ne 0 ]
	then
		echo "没有crypto，现在需要安装"
		cd ${g_DIR_SOFT}
		tar xf pycrypto-2.6.1.tar.gz
		cd pycrypto-2.6.1
		python setup.py  install
		if  [ $? -ne 0 ]
		then
			echo "安装pycropto失败，请检查系统是否有GCC编译环境,如果没有gcc环境，请安装: yum  install -y gcc 或者联系Q群:456335218"
			exit
		else
			echo "安装pycropto完成"
		fi
	fi
	echo "开始安装paramiko..."
	cd ${g_DIR_SOFT}
	tar xf paramiko-1.9.0.tar.gz
	cd paramiko-1.9.0
	python setup.py install
	if [ $? -ne 0 ]
	then
		echo "安装paramiko失败，请检查系统是否有gcc环境和python-devel环境"
	else
		echo "安装paramiko完成"
	fi
else
	echo "paramiko已经就绪"
fi
####################################################################
cat<<EOFhashlib|python
import sys
try:
	import hashlib
except:
	sys.exit(1)
EOFhashlib
if [ $? -ne 0 ]
then
	echo "系统没有hashlib,正在安装"
	cd ${g_DIR_SOFT}
	unzip  hashlib-20081119.zip
	cd hashlib-20081119
	python setup.py install
	if [ $? -ne 0 ]
	then
		echo "安装hashlib失败，请检查系统环境"
		exit
	else
		echo "安装hashlib成功"
		cd ../../bin
	fi
fi

###############################################################
}

#}}}
#{{{RmLocalYum
function RmLocalYum()
{
	YUM_BAK=/opt/yum_bak
	rm -rf /etc/yum.repos.d/*
	cp -rf ${YUM_BAK}/* /etc/yum.repos.d/
	rm -rf ${YUM_BAK}
}
#}}}
#{{{InstallXbatch
function InstallXbatch()
{
	cd ${g_DIR_CUR}
    if [[ -d "/opt/X_operations/X_batch/" ]]
    then
        /bin/rm -rf /opt/X_operations/X_batch/
    fi
	mkdir -p ${DIR_INSTALL}
    mkdir -p ${DIR_CONF}
	cp -fr ./Packages/X_batch/* ${DIR_INSTALL} 2>/dev/null
	cp ./Packages/conf/* ${DIR_CONF}
    chmod 777 ${DIR_INSTALL}/bin/xbatch.py
    if [[ -f "/usr/bin/xb" ]]
    then
        unlink /usr/bin/xb
        ln -s ${DIR_INSTALL}/bin/xbatch.py /usr/bin/xb
    else
        ln -s ${DIR_INSTALL}/bin/xbatch.py /usr/bin/xb
    fi
	touch ${DIR_INSTALL}/flag/installed
    echo "Install [OK] ,please config the hosts file(/etc/xbatch/hosts)"
	return 0
}
#}}}
# main
function main()
{
	PythonVersion
	InstallLocalYum
	InstallTOOL
	InstalEnv
	RmLocalYum
	InstallXbatch
}
main
