#!/usr/bin/env python3

import argparse
from functools import partial
import logging
from scapy.all import *
import sys


def setup_logging(level):
    log.setLevel(level.upper())

    stdout_handler = logging.StreamHandler(sys.stdout)
    stdout_handler.setLevel(level.upper())
    stdout_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    stdout_handler.setFormatter(stdout_formatter)
    log.addHandler(stdout_handler)


def arp_monitor_callback(rcv_packet, intf, oui, arp_addr, self_mac):
    if ARP in rcv_packet:
        ether = rcv_packet[Ether]
        arp = rcv_packet[ARP]
        if arp.op == 1 and arp.hwsrc.startswith(oui) and arp.psrc == arp_addr:
            log.info('Received:')
            rcv_packet.show()

            pkt_ether = Ether(src=self_mac, dst=ether.src)
            pkt_arp = ARP(op='is-at', hwlen=6, plen=4, hwsrc=self_mac, psrc=arp.pdst, hwdst=arp.hwsrc, pdst=arp.psrc)
            snd_packet = pkt_ether / pkt_arp
            log.info('Sending:')
            snd_packet.show()
            sendp(snd_packet, iface=intf)
            sys.exit(0)


def do_arp(interface, oui, arp_addr):
    self_mac = get_if_hwaddr(interface)
    self_ip = get_if_addr(interface)
    log.info(f'{interface} mac: {self_mac}  ip: {self_ip}')

    part = partial(arp_monitor_callback, intf=interface, oui=oui, arp_addr=arp_addr, self_mac=self_mac)
    sniff(iface=interface, prn=part, filter='arp', store=0)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('--verbosity', default='info', choices=['debug', 'info', 'warn', 'error'], help='log level')
    parser.add_argument('--interface', default='eth2', help='Interface the Arris modem is connected to.')
    parser.add_argument('--arris-oui', default='00:10:18', help='Organizationally Unique Identifier for the Arris modem.')
    parser.add_argument('--arris-arp-addr', default='192.168.0.1', help='IP address the Arris modem is using for ARP.')
    args = parser.parse_args()

    log = logging.getLogger(__name__)
    setup_logging(args.verbosity)

    if args.interface not in get_if_list():
        log.error(f'Error. Unknown interface: {args.interface}')
        log.error(f'Available interfaces: {get_if_list()}')
        sys.exit(1)

    do_arp(args.interface, args.arris_oui, args.arris_arp_addr)
