#!/bin/sh
#
# (c) Copyright 2016 Cloudera, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# We remove any natively installed JDKs, as both Cloudera Manager and Cloudera Director only support Oracle JDKs
sudo yum remove --assumeyes *openjdk*
sudo rpm -ivh "http://archive.cloudera.com/director/redhat/7/x86_64/director/2.5.0/RPMS/x86_64/oracle-j2sdk1.8-1.8.0+update121-1.x86_64.rpm"
sudo ln -s /usr/java/jdk1.8.0_121-cloudera /usr/java/default
sudo ln -s /usr/java/default/bin/java /usr/bin/java

sudo yum install -y git

# spot user
sudo adduser spot
echo spot | sudo passwd spot --stdin
sudo usermod -aG wheel spot


