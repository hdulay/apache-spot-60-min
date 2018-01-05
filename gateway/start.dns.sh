#!/bin/bash
# start ingest

### send dns data
cd
unzip -o data/dns_pcap_synthetic_sample.zip -d data/dns
cp data/dns/*.pcap /collector_path/dns

## wait 5 min
echo "waiting 5 for dns collector and worker to populate data"
sleep 5m

## spot ml
cd
cd incubator-spot/spot-ml
./ml_ops.sh 20160707 dns 1000 200

## spot oa
cd
cd incubator-spot/spot-oa/oa
python2.7 start_oa.py -d 20160707 -t dns -l 3000