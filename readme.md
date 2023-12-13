# Faust

Faust 는 LLM을 서비스 하기 위한 도구입니다.  
huggingface의 transformers 라이브러리를 사용하여 모델을 로드하고, TCP 소켓을 통해 텍스트를 입력받아 모델을 통해 텍스트를 생성하고 다시 TCP 소켓을 통해 텍스트를 전송합니다.  

## 사용법

### vscode luanche.json 설정
```json
{
    "name": "Faust LLMPlayer",
    "type": "python",
    "request": "launch",
    "program": "${workspaceFolder}/faust/app.py",
    "console": "integratedTerminal",
    "cwd": "${workspaceFolder}/faust",
    "justMyCode": false
}
```

### 실행하기  

실행환경 설치  
.env 파일을 생성하고 다음과 같이 실행합니다.  
(sample.env 파일을 참고하세요.)  

```bash
python -m venv .venv
source .venv_faust/bin/activate

pip install -r requirements.txt
```


```bash
python app.py
```

## Protocol

모든 패킷은 다음 구조를 따릅니다:<br>

### 공통헤더

헤더 체크 코드 (unsigned long, 0:4): 모든 패킷은 20231208로 시작합니다.  
명령어 (unsigned char, 4:5): 패킷의 유형을 나타냅니다.  
예약 (unsigned char, 5:8): 명령어에 따라 예약되어 있습니다.  


### 클라이언트 요청

**0x10 명령어**  
텍스트 생성 요청. 데이터는 UTF-8로 인코딩된 텍스트입니다.  
헤더 체크 코드 (unsigned long, 0:4): 20231208로 설정합니다.  
명령어 (unsigned char, 4:5): 0x10으로 설정합니다.  
예약 (unsigned char, 5:6): 0으로 설정합니다.  
데이터 길이 (unsigned short, 6:8 바이트): 이어지는 데이터의 길이 (바이트 단위).<br>
데이터 (bytes , 8: ): 실제 데이터.<br>

**0x20 명령어**    
요청 큐의 길이 요청. 서버는 요청 큐의 현재 길이를 응답합니다.    
헤더 체크 코드 (unsigned long, 0:4): 20231208로 설정합니다.  
명령어 (unsigned char, 4:5): 0x20으로 설정합니다.  
예약 (unsigned char, 5:8): 0으로 설정합니다.  

### 서버 응답
**0x20 응답**  
요청 대기큐 길이 길이 (unsigned short, 6:8 바이트): 이어지는 데이터의 길이 (바이트 단위).  

**0x10 응답**  
생성 시작 알림  
(unsigned char, 5:8): version  

**0x11 응답**  
토큰생성  
(unsigned short, 6:8): 토큰 길이  
(bytes, 8: ): 토큰  


**0x12 응답**  
토콘 생성 완료  
(unsigned char, 6:8): 생성된 전체 토큰 길이  


## 기타

```bash
# port 번호로 프로세스 죽이기
fuser -k 22291/tcp
```