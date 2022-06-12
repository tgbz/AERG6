import socket, time, threading

def multicastTester():
    s = socket.socket(socket.AF_INET6, socket.SOCK_DGRAM)
    #set socket to ipv6 multicast mode
    s.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_MULTICAST_HOPS, 100)
    s.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_MULTICAST_LOOP, False)
    s.settimeout(100)
    mCast = 'ff02::1'
    port = 5555
    s.bind(('', port))
    hostname = socket.gethostname()
    counter = 0
    try: 
        while True:
            print("A enviar multicast...")
            msg="neighbor-request-"+hostname+"-"+str(counter)
            counter += 1
            print(msg)
            s.sendto(msg.encode(), (mCast, port))
            print("A espera de receber info...")
            data, addr = s.recvfrom(4096)
            if data.decode().split('-')[0] == "neighbor" and data.decode().split('-')[1] == "reply":
                print("Recebido reply de  ... hostaname: " + data.decode().split('-')[2])
            else:
                print("PACOTE OUT OF CONTEXT" + data.decode())
            time.sleep(2)
    except Exception as e:
        print(e)
        
                
def main():
    multicastTester()
if __name__ == "__main__":
    main()
             