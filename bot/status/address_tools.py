#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Stolen and modified from https://github.com/Dinnerbone/mcstatus

"Address tools"

__all__ = ['ip_type', 'parse_address', 'lookup', 'find_ip']

from typing import Union
import socket
from urllib.parse import urlparse
from ipaddress import ip_address

import dns.resolver

# ip_type, parse_address, and lookup stolen from
# https://github.com/Dinnerbone/mcstatus
# with modifications

def ip_type(address: str) -> Union[int, None]:
    "Returns what version of ip a given address is."
    try:
        return ip_address(address).version
    except ValueError:
        return None

def parse_address(address: str) -> tuple:
    "Return tuple (address, port) from address string."
    tmp = urlparse('//'+address)
    if not tmp.hostname:
        raise ValueError(f"Invalid address '{address}'")
    return tmp.hostname, tmp.port

def lookup(address: str, default_port: int=80, format_host: str='{}',
           qname: str='A') -> tuple:
    "Look up address and return ip after sucessful lookup."
    host, port = parse_address(address)
    if port is None:
        port = default_port
        try:
            answers = dns.resolver.resolve(format_host.format(host), qname)
            if len(answers):
                answer = answers[0]
                if hasattr(answer, 'address'):
                    host = str(answer.address).rstrip('.')
                if hasattr(answer, 'port'):
                    port = int(answer.port)
        except Exception:# pylint: disable=broad-except
            pass
    return host, port

# Stolen from WOOF (Web Offer One File), Copyright (C) 2004-2009 Simon Budig,
# avalable at http://www.home.unix-ag.org/simon/woof
# with modifications

# Utility function to guess the IP (as a string) where the server can be
# reached from the outside. Quite nasty problem actually.

def find_ip() -> str:
    "Utility function to guess the IP where the server can be found from the network."
    # we get a UDP-socket for the TEST-networks reserved by IANA.
    # It is highly unlikely that there is special routing used
    # for these networks, hence the socket later should give us
    # the ip address of the default route.
    # We're doing multiple tests, to guard against the computer being
    # part of a test installation.
    
    candidates = []
    for test_ip in ('192.0.2.0', '198.51.100.0', '203.0.113.0'):
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.connect((test_ip, 80))
            ip_addr = sock.getsockname()[0]
            sock.close()
        if ip_addr in candidates:
            return ip_addr
        candidates.append(ip_addr)
    return candidates[0]
