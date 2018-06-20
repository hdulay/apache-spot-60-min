
# https://jon.oberheide.org/blog/2008/10/15/dpkt-tutorial-2-parsing-a-pcap-file/
import dpkt

f = open('dns_test01_00100_20160707221101.pcap')
pcap = dpkt.pcap.Reader(f)

pcap.setfilter('udp dst port 53')

count = 0
for ts, pkt in pcap:
    eth = dpkt.ethernet.Ethernet(pkt)
    ip = eth.data
    udp = ip.data
    dns = dpkt.dns.DNS(udp.data)
    print "dns[{}] dns.qd[{}] an[{}] an.type[{}] an.rdata[{}] ns[{}] op[{}]"\
        .format(\
            dns, \
            dns.qd, \
            dns.an, \
            dns.an[0].type if len(dns.an) > 0 else None, \
            dns.an[0].rdata if len(dns.an) > 0 else None, \
            dns.ns, \
            dns.op,)
    count = count + 1
    if count > 20:
        break

count = 0
for ts, buf in pcap:
    eth = dpkt.ethernet.Ethernet(buf)
    ip = eth.data
    tcp = ip.data
    if len(tcp.data) > 0:
        try:
            http = dpkt.http.DNS(tcp.data)
            print "{} {} {}".format(http.method, http.uri, http.version)
            print http.headers
            count = count + 1
        except:
            None
    if count > 10:
        break

    tcp = ip.data

    if tcp.dport == 80 and len(tcp.data) > 0:
        http = dpkt.http.Request(tcp.data)
        print http.uri

    count = count + 1
    if count > 10:
        break