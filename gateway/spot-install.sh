#!/bin/bash
# RUN ON THE GATEWAY NODE, PLEASE PROVIDE CM HOST
# usage: ./spot-install.sh cm-hostname
CM=$1


# start #######################################################################
echo spot | sudo -S echo "establish sudo"

# spot home ###################################################################
sudo -u hdfs hdfs dfs -mkdir -p /user/spot
sudo -u hdfs hdfs dfs -chown -R spot:spot /user/spot

# get git and wget ############################################################
sudo yum -y install git wget

# get pip #####################################################################
cd
wget --no-check-certificate https://bootstrap.pypa.io/get-pip.py
sudo -H python get-pip.py

# cloudera manager python api #################################################
sudo pip install cm-api

# get spot ####################################################################
cd
git clone -b SPOT-181_ODM https://github.com/apache/incubator-spot
cd incubator-spot
## the work after this commit is requires a kerberized cluster
#git checkout 5c18a1df33dedaf2cc0d2bc2ebd0491a6c227014

# update spot.conf and ingest_conf.json, $CM is the CM hostname ###############
cd
sudo python spot.conf.py -cm $CM -cn 'apache-spot' -g $(hostname)
sudo chown spot:spot /etc/spot.conf
sudo chown spot:spot incubator-spot/spot-ingest/ingest_conf.json
sudo chown spot:spot incubator-spot/spot-ml/ml_ops.sh
chmod +x incubator-spot/spot-ml/ml_ops.sh
mv incubator-spot/spot-ingest/pipelines/proxy/bluecoat.py incubator-spot/spot-ingest/pipelines/proxy/bluecoat.py-old
cp bluecoat.py incubator-spot/spot-ingest/pipelines/proxy/

# spot setup hdfs #############################################################
cd
cd incubator-spot/spot-setup
./hdfs_setup.sh

# get kafka python ############################################################
cd
sudo -H pip install kafka-python

# get watchdog python #########################################################
cd
sudo -H pip install watchdog

# prereqs #####################################################################
cd
sudo yum -y groupinstall "Development Tools"
sudo yum install -y glib2-devel
sudo yum -y install gtk2-devel gtk+-devel bison qt-devel qt5-qtbase-devel graphite2-devel

# vm doesn't have the correct version of automake #############################
cd
wget http://ftp.gnu.org/gnu/automake/automake-1.14.tar.gz
tar xvzf automake-1.14.tar.gz
cd automake-1.14
sudo ./configure
sudo make
sudo make install

# install nfdump for netflow data #############################################
cd
git clone https://github.com/Open-Network-Insight/spot-nfdump.git 
cd spot-nfdump
./install_nfdump.sh # without sudo
sudo ./install_nfdump.sh # with sudo

# manually get and install libpcap-devel ######################################
# https://www.rpmfind.net/linux/rpm2html/search.php?query=libpcap-devel
cd
wget https://www.rpmfind.net/linux/centos/7.5.1804/os/x86_64/Packages/libpcap-devel-1.5.3-11.el7.x86_64.rpm
sudo yum install -y libpcap-devel-1.5.3-11.el7.x86_64.rpm

# install Wireshark ###########################################################
cd
wget  https://www.wireshark.org/download/src/all-versions/wireshark-2.2.9.tar.bz2
tar xvf wireshark-2.2.9.tar.bz2
cd wireshark-2.2.9
sudo ./configure --with-gtk2 --disable-wireshark
echo spot | sudo -S echo "re-establish sudo"
sudo make
echo spot | sudo -S echo "re-establish sudo"
sudo make install

# download jar for spark streaming for proxy ##################################
echo spot | sudo -S echo "re-establish sudo"
cd
cd incubator-spot/spot-ingest/common
wget https://repo1.maven.org/maven2/org/apache/spark/spark-streaming-kafka-0-8-assembly_2.11/2.0.0/spark-streaming-kafka-0-8-assembly_2.11-2.0.0.jar

#### spot ingest ##############################################################
# download sample data
echo spot | sudo -S echo "re-establish sudo"
cd
mkdir data
cd data
sudo mkdir -p /collector_path/flow 
sudo mkdir -p /collector_path/dns
sudo mkdir -p /collector_path/proxy
sudo mkdir -p /collector_path/dns/dns_staging/
sudo mkdir -p /collector_path/dns/tmp
sudo chown -R spot:spot /collector_path
wget https://s3-us-west-2.amazonaws.com/apachespot/public_data_sets/flow_aws/nfcapd_aws_utc_an.tar.gz
wget https://s3-us-west-2.amazonaws.com/apachespot/public_data_sets/dns_aws/dns_pcap_synthetic_sample.zip
wget http://log-sharing.dreamhosters.com/bluecoat_proxy_big.zip


#### spot ml ##################################################################
cd
echo spot | sudo -S echo "re-establish sudo"
wget https://github.com/sbt/sbt/releases/download/v1.0.4/sbt-1.0.4.tgz
tar xvf sbt-1.0.4.tgz
sudo ln -s /home/spot/sbt/bin/sbt /usr/bin/sbt
cd incubator-spot/spot-ml
sbt "set test in assembly := {}" clean assembly
sbt assembly

###### spot oa ################################################################
echo spot | sudo -S echo "re-establish sudo"
cd
sudo yum -y install python-devel
sudo pip install ipython
cd incubator-spot/spot-oa
sudo pip install -r requirements.txt
sudo pip install --upgrade urllib3 # had to do this
sudo pip uninstall --yes graphql-core
sudo pip install graphql-core==1.1.0 # role back to 1.1.0
# iploc
tar xvf iploc.tar.gz
mv iploc.csv incubator-spot/spot-oa/context
# impyla cant write to dirs
hdfs dfs -chmod -R 777 .

###### spot ui ################################################################
# install npm
cd
echo spot | sudo -S echo "re-establish sudo"
curl --silent --location https://rpm.nodesource.com/setup_8.x | sudo bash -
sudo yum -y install nodejs

# spot ui install
cd
cd incubator-spot/spot-oa/ui
# sudo npm update
npm install browserify uglify-js
npm run build-all
npm install
cd
cd incubator-spot/spot-oa
./runIpython.sh

## Start flow-ingestion  ######################################################
cd
cd incubator-spot/spot-ingest/
python master_collector.py -t flow -w 1 -id tflow > flow.collector.out 2>&1 & echo $! >flow.collector.pid
python worker.py -t flow -i 0 --topic tflow > flow.worker.out 2>&1 & echo $! >flow.worker.pid

## Start proxy-ingestion  #######################################################
cd
cd incubator-spot/spot-ingest/
python master_collector.py -t proxy -w 1 -id tproxy > proxy.collector.out 2>&1 &
python worker.py -t proxy -i 0 -p 1 --topic tproxy > proxy.worker.out 2>&1 &

## Start dns-ingestion  #######################################################
cd
cd incubator-spot/spot-ingest/
python master_collector.py -t dns -w 1 -id tdns > dns.collector.out 2>&1 &
python worker.py -t dns -i 0 --topic tdns > dns.worker.out 2>&1 &

echo "Spot install finished"