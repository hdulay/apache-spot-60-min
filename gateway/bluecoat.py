#
# Licensed to the Apache Software Foundation (ASF) under one or more
# contributor license agreements.  See the NOTICE file distributed with
# this work for additional information regarding copyright ownership.
# The ASF licenses this file to You under the Apache License, Version 2.0
# (the "License"); you may not use this file except in compliance with
# the License.  You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

import argparse
import re
import shlex

from pyspark import SparkContext
from pyspark.streaming import StreamingContext
from pyspark.streaming.kafka import KafkaUtils
from pyspark.sql import HiveContext
from pyspark.sql.types import *

rex_date = re.compile("\d{4}-\d{2}-\d{2}")

proxy_schema = StructType([
                                    StructField("p_date", StringType(), True),
                                    StructField("p_time", StringType(), True),
                                    StructField("clientip", StringType(), True),
                                    StructField("host", StringType(), True),
                                    StructField("reqmethod", StringType(), True),
                                    StructField("useragent", StringType(), True),
                                    StructField("resconttype", StringType(), True),
                                    StructField("duration", IntegerType(), True),
                                    StructField("username", StringType(), True),
                                    StructField("authgroup", StringType(), True),
                                    StructField("exceptionid", StringType(), True),
                                    StructField("filterresult", StringType(), True),
                                    StructField("webcat", StringType(), True),
                                    StructField("referer", StringType(), True),
                                    StructField("respcode", StringType(), True),
                                    StructField("action", StringType(), True),
                                    StructField("urischeme", StringType(), True),
                                    StructField("uriport", StringType(), True),
                                    StructField("uripath", StringType(), True),
                                    StructField("uriquery", StringType(), True),
                                    StructField("uriextension", StringType(), True),
                                    StructField("serverip", StringType(), True),
                                    StructField("scbytes", IntegerType(), True),
                                    StructField("csbytes", IntegerType(), True),
                                    StructField("virusid", StringType(), True),
                                    StructField("bcappname", StringType(), True),
                                    StructField("bcappoper", StringType(), True),
                                    StructField("fulluri", StringType(), True),
                                    StructField("y", StringType(), True),
                                    StructField("m", StringType(), True),
                                    StructField("d", StringType(), True),
                                    StructField("h", StringType(), True)])


def main():
    
    # input Parameters
    parser = argparse.ArgumentParser(description="Bluecoat Parser")
    parser.add_argument('-zk','--zookeeper',dest='zk',required=True,help='Zookeeper IP and port (i.e. 10.0.0.1:2181)',metavar='')
    parser.add_argument('-t','--topic',dest='topic',required=True,help='Topic to listen for Spark Streaming',metavar='')
    parser.add_argument('-db','--database',dest='db',required=True,help='Hive database whete the data will be ingested',metavar='')
    parser.add_argument('-dt','--db-table',dest='db_table',required=True,help='Hive table whete the data will be ingested',metavar='')
    parser.add_argument('-w','--num_of_workers',dest='num_of_workers',required=True,help='Num of workers for Parallelism in Data Processing',metavar='')
    parser.add_argument('-bs','--batch-size',dest='batch_size',required=True,help='Batch Size (Milliseconds)',metavar='')
    args = parser.parse_args()

    # start collector based on data source type.
    bluecoat_parse(args.zk,args.topic,args.db,args.db_table,args.num_of_workers,args.batch_size)


def spot_decoder(s):

    if s is None:
        return None
    return s


def split_log_entry(line):
    lex = shlex.shlex(line)
    lex.quotes = '"'
    lex.whitespace_split = True
    lex.commenters = ''
    return list(lex)

#2005-04-12 21:03:45 74603 192.16.170.46 503 TCP_ERR_MISS 1736 430 GET http www.yahoo.com / - - NONE 192.16.170.42 - "Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.7.6) Gecko/20050317 Firefox/1.0.2" DENIED none - 192.16.170.42 SG-HTTP-Service - server_unavailable "Server unavailable: No ICAP server is available to process request."
def proxy_parser(proxy_fields):
    
    proxy_parsed_data = []

    # re-order fields.
    p_date = proxy_fields[0]  # 0
    p_time = proxy_fields[1]  # 1
    clientip = proxy_fields[3]  # 2
    host = proxy_fields[10]  # 3
    reqmethod = proxy_fields[8]  # 4
    useragent = proxy_fields[17]  # 5
    resconttype = proxy_fields[16]  # 6
    duration = int(proxy_fields[2])  # 7
    username = proxy_fields[13]  # 8
    authgroup = proxy_fields[15]  # 9
    exceptionid = ""  # 10
    filterresult = proxy_fields[18]  # 11
    webcat = proxy_fields[21]  # 12
    referer = proxy_fields[18]  # 13
    respcode = proxy_fields[4]  # 14
    action = proxy_fields[5]  # 15
    urischeme = proxy_fields[9]  # 16
    uriport = 80 #proxy_fields[11]  # 17
    uripath = proxy_fields[11] if len(proxy_fields[11]) > 1 else ""  # 18
    uriquery = proxy_fields[12] if len(proxy_fields[12]) > 1 else ""  # 19
    uriextension = ""  # 20
    serverip = proxy_fields[21]  # 21
    scbytes = int(proxy_fields[6])  # 22
    scbytes = scbytes if scbytes < 2147483647 else 2147483647
    csbytes = int(proxy_fields[7])  # 23
    csbytes = csbytes if csbytes < 2147483647 else 2147483647
    virusid = proxy_fields[23]  # 24
    bcappname = ""  # 25
    bcappoper = ""  # 26
    full_uri = "{0}{1}{2}".format(host,uripath,uriquery)  # 27
    date = proxy_fields[0].split('-')  # not loaded into hive
    year = date[0]  # 28
    month = date[1].zfill(2)  # 29
    day = date[2].zfill(2)  # 30
    hour = p_time.split(":")[0].zfill(2)  # 31

    # Spot ordered fields
    proxy_parsed_data = [p_date, p_time, clientip, host, reqmethod, useragent, resconttype,
                            duration, username, authgroup, exceptionid, filterresult, webcat,
                            referer, respcode, action, urischeme, uriport, uripath, uriquery,
                            uriextension, serverip, scbytes, csbytes, virusid, bcappname,
                            bcappoper, full_uri, year, month, day, hour]

    return proxy_parsed_data


def save_data(rdd,sqc,db,db_table,topic):

    if not rdd.isEmpty():

        df = sqc.createDataFrame(rdd,proxy_schema)        
        sqc.setConf("hive.exec.dynamic.partition", "true")
        sqc.setConf("hive.exec.dynamic.partition.mode", "nonstrict")
        hive_table = "{0}.{1}".format(db,db_table)
        df.write.format("parquet").mode("append").insertInto(hive_table)

    else:
        print("------------------------LISTENING KAFKA TOPIC:{0}------------------------".format(topic))


def bluecoat_parse(zk,topic,db,db_table,num_of_workers,batch_size):
    
    app_name = topic
    wrks = int(num_of_workers)

    # create spark context
    sc = SparkContext(appName=app_name)
    ssc = StreamingContext(sc,int(batch_size))
    sqc = HiveContext(sc)

    tp_stream = KafkaUtils.createStream(ssc, zk, app_name, {topic: wrks}, keyDecoder=spot_decoder, valueDecoder=spot_decoder)

    proxy_data = tp_stream.map(lambda row: row[1])\
        .flatMap(lambda row: row.split("\n"))\
        .filter(lambda row: rex_date.match(row))\
        .map(lambda row: row.strip("\n").strip("\r").replace("\t", " ").replace("  ", " "))\
        .map(lambda row:  split_log_entry(row))\
        .filter(lambda row: len(row) > 23)\
        .map(lambda row: proxy_parser(row))

    saved_data = proxy_data.foreachRDD(lambda row: save_data(row,sqc,db,db_table,topic))
    ssc.start()
    ssc.awaitTermination()


if __name__ == '__main__':
    main()
