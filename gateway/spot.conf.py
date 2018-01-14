#
#
# https://cloudera.github.io/cm_api/apidocs/v18/
#

import argparse
import os
from cm_api.api_client import ApiResource

def get_node_host(api, cluster, service_name, role_name):
    services = cluster.get_all_services()
    for service in services:
        if service_name in service.name:
            hdfs = service
            roles = hdfs.get_all_roles()
            for role in roles:
                if "SECONDARYNAMENODE" in role.name:
                    continue
                if role_name in role.name:
                    return api.get_host(role.hostRef.hostId).hostname
    return None

def update_spot_ingest(kafka, zk):
    replacements = {
        'database name':'spot',
        'hdfs application path':'/user/spot',
        'kafka ip':kafka,
        'kafka port':'9092',
        'zk ip':zk,
        'zk port':'2181',
        '"driver_memory":"",' : '"driver_memory":"1G",',
        '"spark_exec":"",': '"spark_exec":"3",',
        '"spark_executor_memory":"",' : '"spark_executor_memory":"15G",',
        '"spark_executor_cores":"",' : '"spark_executor_cores":"5",',
        '"spark_batch_size":""' : '"spark_batch_size":"5"',
        '/collector_path/dns/tmp' : '/collector_path/dns/tmp/'
    }
    with open('incubator-spot/spot-ingest/ingest_conf.json') as infile, \
        open('incubator-spot/spot-ingest/ingest_conf.json.new', 'w') as outfile:
        for line in infile:
            for src, target in replacements.iteritems():
                line = line.replace(src, target)
            outfile.write(line)

    os.rename('incubator-spot/spot-ingest/ingest_conf.json.new', \
        'incubator-spot/spot-ingest/ingest_conf.json')

    print "update ingest_conf.json complete"

def update_2_spark2():
    replacements = {
        'spark-submit':'spark2-submit'
    }
    with open('incubator-spot/spot-ml/ml_ops.sh') as infile, \
        open('incubator-spot/spot-ml/ml_ops.sh.new', 'w') as outfile:
        for line in infile:
            for src, target in replacements.iteritems():
                line = line.replace(src, target)
            outfile.write(line)

    os.rename('incubator-spot/spot-ml/ml_ops.sh.new', \
        'incubator-spot/spot-ml/ml_ops.sh')

    with open('incubator-spot/spot-ingest/pipelines/proxy/worker.py') as infile, \
        open('incubator-spot/spot-ingest/pipelines/proxy/worker.py.new', 'w') as outfile:
        for line in infile:
            for src, target in replacements.iteritems():
                line = line.replace(src, target)
            outfile.write(line)

    os.rename('incubator-spot/spot-ingest/pipelines/proxy/worker.py.new', \
        'incubator-spot/spot-ingest/pipelines/proxy/worker.py')

    print "update ml_ops.sh and proxy/worker.py to spark2-submit complete"

def fix_dns_worker():
    replacements = {
        'hadoop fs -get {0} {1}.':'hadoop fs -get {0} {1}'
    }
    with open('incubator-spot/spot-ingest/pipelines/dns/worker.py') as infile, \
        open('incubator-spot/spot-ingest/pipelines/dns/worker.py.new', 'w') as outfile:
        for line in infile:
            for src, target in replacements.iteritems():
                line = line.replace(src, target)
            outfile.write(line)

    os.rename('incubator-spot/spot-ingest/pipelines/dns/worker.py.new', \
        'incubator-spot/spot-ingest/pipelines/dns/worker.py')

    print "fix incubator-spot/spot-ingest/pipelines/dns/worker.py bug complete"
    

def main():
    parser = argparse.ArgumentParser(description='buildes a spot.conf using CM api')
    parser.add_argument('-cm','--clouderaManager',dest='cm',required=True,help='hostname for cloudera manager')
    parser.add_argument('-cn','--clusterName',dest='cn',required=True,help='cluster name')
    parser.add_argument('-g','--gateway',dest='gate',required=True,help='gateway node')
    args = parser.parse_args()

    cm_host = args.cm
    cluster_name = args.cn
    api = ApiResource(cm_host, username="admin", password="admin")

    cluster = api.get_cluster(cluster_name)

    namenode = get_node_host(api, cluster, "HDFS", "NAMENODE")
    datanode = get_node_host(api, cluster, "HDFS", "DATANODE")
    kafka = get_node_host(api, cluster, "KAFKA", "KAFKA_BROKER")
    zk = get_node_host(api, cluster, "ZOOKEEPER", "ZOOKEEPER")
    gateway = "'{0}'".format(args.gate)

    props = []
    props.append(tuple(('UINODE', "{0}".format(gateway))))
    props.append(tuple(('MLNODE', "{0}".format(gateway))))
    props.append(tuple(('GWNODE', "{0}".format(gateway))))
    props.append(tuple(('DBNAME', "'spot'")))

    #hdfs - base user and data source config
    props.append(tuple(('HUSER', "'/user/spot'")))
    props.append(tuple(('NAME_NODE', namenode)))
    props.append(tuple(('WEB_PORT', "50070")))
    props.append(tuple(('DNS_PATH', "${HUSER}/${DSOURCE}/hive/y=${YR}/m=${MH}/d=${DY}/")))
    props.append(tuple(('PROXY_PATH', "${HUSER}/${DSOURCE}/hive/y=${YR}/m=${MH}/d=${DY}/")))
    props.append(tuple(('FLOW_PATH', "${HUSER}/${DSOURCE}/hive/y=${YR}/m=${MH}/d=${DY}/")))
    props.append(tuple(('HPATH', "${HUSER}/${DSOURCE}/scored_results/${FDATE}")))

    #impala config
    props.append(tuple(('IMPALA_DEM', datanode)))
    props.append(tuple(('IMPALA_PORT', "21050")))

    props.append(tuple(('LUSER', "'/home/spot'")))
    props.append(tuple(('LPATH', "${LUSER}/ml/${DSOURCE}/${FDATE}")))
    props.append(tuple(('RPATH', "${LUSER}/ipython/user/${FDATE}")))
    props.append(tuple(('LIPATH', "${LUSER}/ingest")))

    #dns suspicious connects config
    props.append(tuple(('USER_DOMAIN', "'cloudera'")))

    props.append(tuple(('SPK_EXEC', "'3'")))
    props.append(tuple(('SPK_EXEC_MEM', "'2G'")))
    props.append(tuple(('SPK_DRIVER_MEM', "'1G'")))
    props.append(tuple(('SPK_DRIVER_MAX_RESULTS', "'1G'")))
    props.append(tuple(('SPK_EXEC_CORES', "'12'")))
    props.append(tuple(('SPK_DRIVER_MEM_OVERHEAD', "'512M'")))
    props.append(tuple(('SPK_EXEC_MEM_OVERHEAD', "'512M'")))
    props.append(tuple(('SPK_AUTO_BRDCST_JOIN_THR', "'10485760'")))

    props.append(tuple(('LDA_OPTIMIZER', "'em'")))
    props.append(tuple(('LDA_ALPHA', "'1.02'")))
    props.append(tuple(('LDA_BETA', "'1.001'")))

    props.append(tuple(('PRECISION', "'64'")))
    props.append(tuple(('TOL', "'1e-6'")))
    props.append(tuple(('TOPIC_COUNT', "'20'")))
    props.append(tuple(('DUPFACTOR', "'1000'")))

    with open("/etc/spot.conf", "wb") as f:
        f.write('\n'.join('{0}={1}'.format(x[0], x[1]) for x in props))


    print "update spot.conf complete"

    update_spot_ingest(kafka, zk)

    update_2_spark2()

    fix_dns_worker()

    return

if __name__ == "__main__":
    main()
