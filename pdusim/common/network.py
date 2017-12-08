import ctypes
import socket
import struct
import fcntl
import math
import os
from . import logger

SIOCGIFINDEX = 0x8933
SIOCGIFFLAGS = 0x8913
SIOCSIFFLAGS = 0x8914
SIOCGIFHWADDR = 0x8927
SIOCSIFHWADDR = 0x8924
SIOCGIFADDR = 0x8915
SIOCSIFADDR = 0x8916
SIOCGIFNETMASK = 0x891B
SIOCSIFNETMASK = 0x891C
SIOCETHTOOL = 0x8946

# From linux/if.h
IFF_UP = 0x1

# From linux/socket.h
AF_UNIX = 1
AF_INET = 2


class NetworkUtils:
    @staticmethod
    def get_ip_address(ifname):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            ifreq = struct.pack('16sH14s', ifname, AF_UNIX, '\x00'*14)
            res = fcntl.ioctl(s.fileno(), SIOCGIFADDR, ifreq)
            ip = struct.unpack('16sH2x4s8x', res)[2]
            s.close()
            return socket.inet_ntoa(ip)
        except:
            logger.error("Failed to get ip on %s" % ifname)
            return ""

    @staticmethod
    def set_ip_address(ifname, ip):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            bin_ip = socket.inet_aton(ip)
            ifreq = struct.pack('16sH2s4s8s', ifname, socket.AF_INET,
                                '\x00'*2, bin_ip, '\x00'*8)
            fcntl.ioctl(s, SIOCSIFADDR, ifreq)
            s.close()
        except:
            logger.error("Failed to set ip %s on %s" % (ip, ifname))
            print "Failed to set ip %s on %s" % (ip, ifname)

    @staticmethod
    def get_netmask_int(netmask):
        ret = 0
        for n in range(0, netmask):
            ret |= 1 << (31 - n)
        return ret

    @staticmethod
    def get_mask(mask):
        n = 0
        while True:
            if mask == 0:
                break
            mask &= (mask - 1)
            n += 1
        return n

    @staticmethod
    def convert_ip_to_int(ip):
        ip_items = ip.split('.')
        ip_int = 0
        for item in ip_items:
            ip_int = ip_int * 256 + int(item)
        return ip_int

    @staticmethod
    def convert_int_to_ip(ip_int):
        ip_items = ['0', '0', '0', '0']
        for i in range(0, 4):
            ip_items[3-i] = str(ip_int % 256)
            ip_int = int((int(ip_int) - int(ip_items[3-i])) / 256)
        return '.'.join(ip_items)

    @staticmethod
    def link_up(ifname):
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        ifreq = struct.pack("16sh", ifname, 0)
        flags = struct.unpack('16sh',
                              fcntl.ioctl(s.fileno(), SIOCGIFFLAGS, ifreq))[1]

        flags = flags | IFF_UP
        ifreq = struct.pack('16sh', ifname, flags)
        fcntl.ioctl(s.fileno(), SIOCSIFFLAGS, ifreq)
        s.close()

    @staticmethod
    def link_down(ifname):
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        ifreq = struct.pack("16sh", ifname, 0)
        flags = struct.unpack('16sh',
                              fcntl.ioctl(s.fileno(), SIOCGIFFLAGS, ifreq))[1]

        flags = flags & ~IFF_UP
        ifreq = struct.pack('16sh', ifname, flags)
        fcntl.ioctl(s.fileno(), SIOCSIFFLAGS, ifreq)
        s.close()

    @staticmethod
    def link_status(ifname):
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        ifreq = struct.pack("16sh", ifname, 0)
        flags = struct.unpack('16sh',
                            fcntl.ioctl(s.fileno(), SIOCGIFFLAGS, ifreq))[1]
        s.close()
        if flags & IFF_UP:
            return True
        else:
            return False

    @staticmethod
    def get_netmask(ifname):
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        ifreq = struct.pack('16sH14s', ifname, socket.AF_INET, '\x00'*14)
        try:
            res = fcntl.ioctl(s.fileno(), SIOCGIFNETMASK, ifreq)
        except IOError:
            s.close()
            return ""
        netmask = socket.ntohl(struct.unpack('16sH2xI8x', res)[2])
        s.close()
        return 32 - int(round(math.log(ctypes.c_uint32(~netmask).value + 1, 2), 1))

    @staticmethod
    def set_netmask(ifname, netmask):
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        netmask = ctypes.c_uint32(~((2 ** (32 - netmask)) - 1)).value
        nmbytes = socket.htonl(netmask)
        ifreq = struct.pack('16sH2si8s', ifname, socket.AF_INET,
                            '\x00'*2, nmbytes, '\x00'*8)
        fcntl.ioctl(s.fileno(), SIOCSIFNETMASK, ifreq)
        s.close()

    @staticmethod
    def get_net_interfaces():
        return os.listdir("/sys/class/net")