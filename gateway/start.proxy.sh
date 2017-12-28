#!/bin/bash
# start ingest

### send proxy data
cd
rm -f /collector_path/proxy/*
unzip data/bluecoat_proxy_big.zip -d /collector_path/proxy > proxy.gen.out 2>&1 &

# wait for proxy collector and worker to finish
sleep 5m


## spot ml
cd
cd incubator-spot/spot-ml
./ml_ops.sh 20050405 proxy 1000 200

## spot oa
cd
cd incubator-spot/spot-oa/oa
python2.7 start_oa.py -d 20050405 -t proxy -l 3000