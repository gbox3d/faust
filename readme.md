# Faust

Faust 는 LLM을 서비스 하기 위한 도구입니다.  
huggingface의 transformers 라이브러리를 사용하여 모델을 로드하고, TCP 소켓을 통해 텍스트를 입력받아 모델을 통해 텍스트를 생성하고 다시 TCP 소켓을 통해 텍스트를 전송합니다.  


## 기타

```bash
# port 번호로 프로세스 죽이기
fuser -k 22291/tcp
```