from datetime import datetime
import socket, time
import struct

sock = socket.socket(socket.AF_INET6, socket.SOCK_DGRAM)

sock.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_MULTICAST_LOOP, True)


while True:

    sock.sendto("hello world".encode('utf-8'), ("ff02::abcd:1", 8080))
    print("message Sent")
    time.sleep(.5)