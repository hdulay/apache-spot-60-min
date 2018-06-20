# Apache Spot (Incubating) in 60 minutes
This project will build a Cloudera EDH 5.12 cluster on AWS using Cloudera Director. A running Cloudera Director on AWS is a prerequisite. 

service krb5kdc start
service kadmin start

https://wiki.cloudera.com/display/~ben/Kafka+Security+Configurations


# KEYTAB create
-norandkey
xst -k <keytab> -norandkey <princ>
make sure to pass this arg to make sure the ps does change.

# Apache Spot Secured CDH
## Install MIT Kerberos
ec2-54-234-144-118.compute-1.amazonaws.com ( centos 6.7 )
yum -y install krb5-server krb5-libs krb5-auth-dialog krb5-workstation

## disable iptables (firewall)
https://www.linkedin.com/pulse/20140902232716-89781742-disable-firewall-for-aws-ec2-instance
$ sudo service iptables save
$ sudo service iptables stop
$ sudo chkconfig iptables off

sudo vi /var/kerberos/krb5kdc/kdc.conf
```
[kdcdefaults]
 kdc_ports = 88
 kdc_tcp_ports = 88

[realms]
 CLOUDERA.COM = {
  #master_key_type = aes256-cts
  acl_file = /var/kerberos/krb5kdc/kadm5.acl
  dict_file = /usr/share/dict/words
  admin_keytab = /var/kerberos/krb5kdc/kadm5.keytab
  supported_enctypes = arcfour-hmac:normal aes256-cts aes128-cts des3-hmac-sha1 arcfour-hmac des-hmac-sha1 des-cbc-md5 des-cbc-crc
 }
 ```
 https://web.mit.edu/kerberos/krb5-1.12/doc/admin/conf_files/kdc_conf.html#encryption-types

sudo vi /etc/krb5.conf
```
[logging]
 default = FILE:/var/log/krb5libs.log
 kdc = FILE:/var/log/krb5kdc.log
 admin_server = FILE:/var/log/kadmind.log

[libdefaults]
 default_realm = CLOUDERA.COM
 dns_lookup_realm = false
 dns_lookup_kdc = false
 ticket_lifetime = 24h
 renew_lifetime = 7d
 forwardable = true

[realms]
 CLOUDERA.COM = {
  kdc = localhost
  admin_server = localhost
 }

#[domain_realm]
# .example.com = EXAMPLE.COM
# example.com = EXAMPLE.COM
```

sudo kdb5_util create -s
password cloudera

# TLS

Replace the OU, O, L, ST, and C entries with the values for your organization name, location, and country code (US, in the example):
```
sudo $JAVA_HOME/bin/keytool -genkeypair -alias $(hostname -f)-server -keyalg RSA -keystore \
/opt/cloudera/security/pki/$(hostname -f)-server.jks -keysize 2048 -dname \
"CN=$(hostname -f),OU=FCE,O=cloudera.com,L=New York,ST=NY,C=US" \
-storepass cloudera -keypass cloudera
```

```
sudo $JAVA_HOME/bin/keytool -certreq -alias $(hostname -f)-server \
-keystore /opt/cloudera/security/pki/$(hostname -f)-server.jks \
-file /opt/cloudera/security/pki/$(hostname -f)-server.csr -storepass cloudera \
-keypass cloudera
```