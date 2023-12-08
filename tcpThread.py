import socket
import threading
import time

class ClientThread(threading.Thread):
    def __init__(self, conn, addr, onPacket, onClose):
        threading.Thread.__init__(self)
        self.conn = conn
        self.addr = addr
        self.onPacket = onPacket
        self.onClose = onClose

    def run(self):
        while True:
            try:
                data = self.conn.recv(65535)
                if not data:
                    break
                self.onPacket(self.conn, data, self.addr)
            except socket.timeout:
                continue
            except Exception as ex:
                print(f'Client thread error: {ex}')
                break
        self.onClose(self.conn, self.addr)
        self.conn.close()

class tcpServerThread(threading.Thread):
    def __init__(self, port, onPacket,onClose,onConnect, Listen_for_incoming_connections=1, timeout=1):
        threading.Thread.__init__(self)
        
        self.port = port
        self.tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.tcp_socket.bind(('', port))
        self.tcp_socket.listen(Listen_for_incoming_connections)  # Listen for incoming connections, 1 is the backlog
        
        self.tcp_socket.settimeout(timeout)  # 1초 타임아웃 설정

        self.onPacket = onPacket
        self.onClose = onClose
        self.onConnect = onConnect

        self.termination_requested = False
        
        print(f'tcp server start port = {port}')
        
    def run(self):
        while not self.termination_requested:
            try:
                if self.tcp_socket == None:
                    break
                else:
                    conn, addr = self.tcp_socket.accept()  # Block until a client connects
                    self.handle_client(conn, addr)
            except socket.timeout:
                continue
            except Exception as ex:
                print(f'error : {ex}')
                time.sleep(1)
                
        print('tcp server thread terminated')
                
        self.tcp_socket.close()
        self.tcp_socket = None
    
    def handle_client(self, conn, rinfo):
        print(f'Connected by {rinfo}')

        self.onConnect(conn, rinfo)
        client_thread = ClientThread(conn, rinfo, self.onPacket, self.onClose)
        client_thread.start()

        # while not self.termination_requested:
        #     try:
        #         _data = conn.recv(65535)  # Block until data is received
        #         if not _data:
        #             break  # Connection closed
        #         self.onPacket(conn,_data, rinfo)
        #         # Optionally send data back to the client
        #         # conn.sendall(response_data)
                
        #     except socket.timeout:
        #         continue
        #     except Exception as ex:
        #         print(f'error : {ex}')
        #         break  # Break on any other exception
        # self.onClose(conn, rinfo)
        # conn.close()        
        

    def terminate(self):
        self.termination_requested = True

    def isRunning(self):
        return not self.termination_requested
