#%%
import torch
from transformers import AutoTokenizer,pipeline

from tcpThread import tcpServerThread

import queue
from struct import *

import time
import os
from dotenv import load_dotenv
# .env 파일 로드 
load_dotenv()

#%%
packetHeaderCheckCode = 20231208

model_name = os.getenv('MODEL_NAME')
print(f'Start loading {model_name}')

start_tick = time.time()

tokenizer = AutoTokenizer.from_pretrained(model_name)

hf_pipeline = pipeline(
    task="text-generation", 
    model=model_name, 
    tokenizer=tokenizer,
    torch_dtype=torch.float16,
    # load_in_8bit=True,
    do_sample=False,
    repeat_penalty=1.15,
    # device_map="auto" # GPU 상황에 맞게 자동으로 설정
    device_map="auto"  # GPU 0사용 설정)
)

print(f'Load time: {time.time() - start_tick}')

model = hf_pipeline.model

__version__ = (0,0,1)
#%%
def generate_text_interactively(prompt, max_length=128,conn=None,_checkCode=packetHeaderCheckCode):
    input_ids = tokenizer.encode(prompt, return_tensors="pt").to(model.device)
    generated = input_ids
    # sentences = set()
    
    if conn != None:
        # conn.sendall("##START##".encode())
        _header_packet = pack('<LBBBB', packetHeaderCheckCode,0x10,*__version__) # 0x10 : start packet
        conn.sendall(_header_packet)
    else:
        print('connection is None')
        return None

    model.eval()
    try :
        with torch.no_grad():
            _gen_text = ''
            for _ in range(max_length):
                outputs = model(generated)
                next_token_logits = outputs.logits[:, -1, :]
                next_token = torch.argmax(next_token_logits, dim=-1, keepdim=True)
                generated = torch.cat([generated, next_token], dim=-1)

                # 현재까지 생성된 텍스트 확인
                # generated_text = tokenizer.decode(generated[0], skip_special_tokens=True)

                # 모든 문장 분리
                # current_sentences = set(generated_text.split('.'))
                # if sentences.intersection(current_sentences):
                #     print('stop generating text : duplicated sentence : ',current_sentences)
                #     break
                # sentences.update(current_sentences)

                # 다음 토큰을 텍스트로 변환하여 출력
                next_token_text = tokenizer.decode(next_token[0], skip_special_tokens=True)
                print(next_token_text)
                _next_token_data = next_token_text.encode('utf-8')
                _header_packet = pack('<LBBH', packetHeaderCheckCode,0x11,0,len(_next_token_data)) # 0x11 : text packet
                conn.sendall(_header_packet + _next_token_data )
                
                _gen_text += next_token_text
                
                current_sentences = _gen_text.split('.')
                if len(current_sentences) > 1:
                    # 마지막 문장이 이전 문잘들과 비교하여 중복되는지 확인
                    if current_sentences[-1] in current_sentences[:-1]:
                        print('stop generating text : duplicated sentence : ',current_sentences[-1])
                        break
                
                
                if next_token.item() == tokenizer.eos_token_id:
                    #end of sentence
                    break
            _header_packet = pack('<LBBH', packetHeaderCheckCode,0x12,0,len(_gen_text)) # 0x12 : end of sentence packet
            conn.sendall(_header_packet)

        return _gen_text
    except Exception as e:
        print(e)
        return None
        
    # OnDone(generated_text)
# #%%
# # 예시 사용
# prompt = "지구의 위성은 무엇이 있을까요?"
# generate_text_interactively(prompt, max_length=20)
# 큐 생성
request_queue = queue.Queue()

#%%
def onPacket(conn, data, rinfo):
    
    while len(data) < 8:
        data += conn.recv(8 - len(data))
    
    _checkCode,cmd = unpack("<LB",data[:5])
    
    
    if _checkCode != packetHeaderCheckCode :
        print(f'checkcode error : {_checkCode}')
        return
    else:
        if cmd == 0x20 : # request_queue 의 길이를 보내준다.
            _packet = pack('<LBBH',packetHeaderCheckCode,cmd,0,request_queue.qsize())
            conn.sendall(_packet)
        elif cmd == 0x10 :
            length  = unpack("<H",data[6:8])[0]
            prompt = b''
            if len(data) > 8:
                prompt = data[8:]
                
            while len(prompt) < length:
                prompt += conn.recv(length - len(prompt))
                
            prompt = prompt.decode('utf-8')
            print(f'add req que prompt : {prompt} remote ip : {rinfo}')
            # 큐에 요청 추가
            request_queue.put({
                'conn':conn,
                'prompt':prompt,
                'rinfo':rinfo
            })
    
def onClose(conn, rinfo):
    print(f'close : {rinfo}')
def onConnect(conn, rinfo):
    print(f'connect : {rinfo}')

_port = os.getenv('TCP_PORT')
_tcpMainIOThread = tcpServerThread(
    onPacket=onPacket,
    onClose=onClose,
    onConnect=onConnect,
    port=int(_port),
    Listen_for_incoming_connections=10,
    timeout=1
)

_tcpMainIOThread.start()

print(f"start listening port {_port} , ctrl + c to stop")

try :
    while True:
        
        req_data = request_queue.get()
        if req_data != None:
            
            print(f'prompt : {req_data["prompt"]}')
            
            _gen_text = generate_text_interactively(
                
                req_data['prompt'],conn=req_data['conn']
                )
            
            print(f'generated_text : {_gen_text}')
            
            # req_data['conn'].sendall("##FIN##".encode())
            # generated_text = generate_text_interactively(prompt['prompt'], max_length=1024)
            # print(f'generated_text : {generated_text}')
            # prompt['conn'].sendall(generated_text.encode())
            
        
        #pipeline 처리 
        pass
            
except KeyboardInterrupt:        
    print('KeyboardInterrupt')        
except Exception as e:
    
    print(e)

_tcpMainIOThread.terminate()

print('server task end')    

#%%

