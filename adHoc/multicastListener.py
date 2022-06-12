import socket, time, threading


def multicastListener():
    s = socket.socket(socket.AF_INET6, socket.SOCK_DGRAM)
    #set socket to ipv6 multicast mode
    #set socket reuse address
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    
    s.settimeout(100)
    port = 5555
    s.bind(('', port))
    hostname = socket.gethostname()
    counter = 0
    while True:
        data, addr = s.recvfrom(4096)
        if data.decode().split('-')[0] == "neighbor" and data.decode().split('-')[1] == "request":
            counter += 1
            print("Recebido pedido de vizinho ... IP: " + data.decode().split('-')[2] + str(counter))
            msg = "neighbor-reply-"+hostname
            s.sendto(msg.encode(), addr)
        else:
            print("PACOTE OUT OF CONTEXT" + data.decode())


            

def main():
    multicastListener()

if __name__ == "__main__":
    main()