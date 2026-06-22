# 텍스트를 지식그래프로 표현하기

**Part 2. 지식그래프 구축 실전**

- Chapter 02. 지식그래프 구축하기

    - 📒 Clip 01. [실습] 텍스트를 지식그래프로 변환하기

> 위키백과의 텍스트를 LLM을 사용하여 지식그래프로 표현하는 실습입니다.

## 참고자료 (Knowledge Graph Builder)

https://neo4j.com/docs/neo4j-graphrag-python/current/user_guide_kg_builder.html

https://medium.com/neo4j/constructing-knowledge-graphs-with-neo4j-graphrag-for-python-2b3f1a42534d

### 💡 지식그래프 구축을 위한 2가지 접근 방식

### 1) Neo4j GraphRAG의 KG Builder 모듈

Neo4j에서 제공하는 `neo4j-graphrag` 패키지의 [KG Builder](https://neo4j.com/docs/neo4j-graphrag-python/current/user_guide_kg_builder.html) 모듈을 사용하면 간단하게 지식그래프를 구축할 수 있습니다:

```python
from neo4j_graphrag.experimental.pipeline.kg_builder import SimpleKGPipeline

kg_builder = SimpleKGPipeline(
    llm=llm, # an LLMInterface for Entity and Relation extraction
    driver=neo4j_driver,  # a neo4j driver to write results to graph
    embedder=embedder,  # an Embedder for chunks
    from_pdf=True,   # set to False if parsing an already extracted text
)
await kg_builder.run_async(file_path=str(file_path))
# await kg_builder.run_async(text="my text")  # if using from_pdf=False
```

### 2) 직접 LLM 프롬프트 구현한 저수준(low-level) 파이프라인

- 엔티티/관계 추출을 위한 프롬프트 구조 이해
- 관계 방향성(피동형/능동형) 처리 로직 학습
- JSON 출력 형식 정의 및 파싱 경험

```
텍스트 청킹 → LLM 사용한 엔티티 및 관계 추출 → 결과 파싱 → Neo4j 저장 → 중복 병합
```

### 실습에 사용할 위키백과 링크

단백질 위키백과 :
https://ko.wikipedia.org/wiki/%EB%8B%A8%EB%B0%B1%EC%A7%88

버스 위키백과 :
https://ko.wikipedia.org/wiki/%EB%B2%84%EC%8A%A4


## 실습 순서

### 1. 패키지 설치

Python 3.13

```bash
# uv 설치
# Windows (PowerShell)
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"

# macOS / Linux
curl -LsSf https://astral.sh/uv/install.sh | sh
```

```bash
# 방법 1: uv sync 사용 (권장)
uv sync
.venv\Scripts\activate
```

또는

```bash
# 방법 2: requirements.txt 사용
uv venv
.venv\Scripts\activate
uv pip install -r requirements.txt
```

### 2. Neo4j 데이터베이스 및 LLM API 준비

- 데이터베이스 생성 후 URI, username, password 확인(credentials.txt)
- OpenAI API 키 발급: https://platform.openai.com/api-keys


### 3. 환경변수 설정

`.env.example` 파일을 `.env`로 복사하고 본인의 정보로 수정:

```bash
cp .env.example .env
```


### 4. 실행

```bash
python txt2kg.py
```
