#%%
import socket

import time
import os
from struct import *
from dotenv import load_dotenv
# .env 파일 로드 
load_dotenv()
packetHeaderCheckCode = 20231208

#%%
_port = os.getenv('TCP_PORT')
client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

try :
    client_socket.connect(('localhost', int(_port)))
    
    print(f"connect to port {_port}")
    
    while True:
        input_data = input('input prompt : ')
        
        if input_data == '##exit':
            break
        elif input_data == '##get_qs': # request_queue 의 길이를 얻는다.
            packet = pack('<LBBBB',packetHeaderCheckCode,0x20,0,0,0)
            client_socket.sendall(packet)
        else :
            length = len(input_data)
            packet = pack('<LBBH',packetHeaderCheckCode,0x10,0,length)
            packet += input_data.encode('utf-8')
            client_socket.sendall(packet)
            
            while True:
                header_packet = client_socket.recv(1024)
                
                if len(header_packet) < 8:
                    header_packet += client_socket.recv(8 - len(header_packet))
                
                _checkCode,cmd = unpack("<LB",header_packet[:5])
                
                if _checkCode != packetHeaderCheckCode :
                    print(f'checkcode error : {_checkCode}')
                    break
                else:
                    if cmd == 0x20 :
                        que_length = unpack("<H",header_packet[6:8])[0]
                        print(f'response queue length : {que_length}')
                        break;
                    elif cmd == 0x10:
                        print('start generate text')
                        while True:
                            _data = client_socket.recv(1024)
                            if len(_data) < 8:
                                _data += client_socket.recv(8 - len(_data))
                            _checkCode,cmd = unpack("<LB",_data[:5])
                            
                            if _checkCode != packetHeaderCheckCode :
                                print(f'checkcode error : {_checkCode}')
                                break
                            else:
                                if cmd == 0x11:
                                    length  = unpack("<H",header_packet[6:8])[0]
                                    prompt = b''
                                    if len(header_packet) > 8:
                                        prompt = header_packet[8:]
                                        
                                    while len(prompt) < length:
                                        prompt += client_socket.recv(length - len(prompt))
                                        
                                    prompt = prompt.decode('utf-8')
                                    print(f'generated text : {prompt}')
                                    break;
                                elif cmd == 0x12:
                                    print('end generate text')
                                    break;
                    
        # else :
        #     length = len(input_data)
        #     packet = pack('<LBBH',packetHeaderCheckCode,0x11,0,length)
        #     packet += input_data.encode('utf-8')
        #     client_socket.sendall(packet)
    
    
    # data = client_socket.recv(1024)
    # print('Received', repr(data.decode()))
except Exception as ex:
    print(ex)
finally:
    client_socket.close()

# %%
