#!/bin/bash
echo "running netflow"
chmod +x start.flow.sh && ./start.flow.sh
echo "running dns"
chmod +x start.dns.sh && ./start.dns.sh
echo "running proxy"
chmod +x start.proxy.sh && ./start.proxy.sh