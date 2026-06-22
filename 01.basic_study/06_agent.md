# 에이전트 개념과 코드 (AI Agents)

## 1. 에이전트 기초

### 1.1 에이전트란?
- **인식(Perceive)** → **추론(Reason)** → **행동(Act)** 사이클을 반복하는 시스템
- LLM + 도구 + 메모리 + 오케스트레이션 로직의 조합
- 핵심 차이: 단순 LLM 호출 vs 동적 도구 선택과 다단계 실행

### 1.2 에이전트 분류
| 유형 | 특징 | 예시 |
|------|------|------|
| ReAct | 추론+행동 교대 반복 | 검색하며 답변하는 QA |
| Plan-and-Execute | 계획 후 단계별 실행 | 복잡한 데이터 분석 |
| Reflexion | 자기 반성으로 개선 | 코드 디버깅 에이전트 |
| Multi-Agent | 에이전트 간 협업 | 소프트웨어 개발팀 |

---

## 2. ReAct 패턴

### 2.1 ReAct 루프 개념
```
Thought: 현재 상황 분석 및 다음 행동 계획
Action: 도구 호출
Observation: 도구 결과 수신
... 반복 ...
Thought: 충분한 정보 수집됨
Answer: 최종 답변
```

### 2.2 ReAct 직접 구현
```python
from anthropic import Anthropic
import json

client = Anthropic()

# 도구 정의
def calculator(expression: str) -> str:
    try:
        result = eval(expression, {"__builtins__": {}}, {})
        return str(result)
    except Exception as e:
        return f"오류: {e}"

def search(query: str) -> str:
    # 실제론 검색 API 호출, 여기선 더미 데이터
    knowledge = {
        "python": "파이썬은 1991년 귀도 반 로섬이 만든 언어다.",
        "transformer": "트랜스포머는 2017년 Attention Is All You Need 논문에서 제안됐다.",
    }
    for key, val in knowledge.items():
        if key in query.lower():
            return val
    return "관련 정보를 찾을 수 없습니다."

TOOLS = {
    "calculator": calculator,
    "search": search,
}

def react_agent(question: str, max_steps: int = 5) -> str:
    messages = []
    system = """당신은 ReAct 에이전트입니다.

다음 형식으로만 답하세요:
Thought: [현재 상황 분석]
Action: tool_name(argument)

또는 답을 알면:
Thought: [결론]
Answer: [최종 답변]

사용 가능한 도구:
- calculator(expression): 수식 계산. 예: calculator(2**10)
- search(query): 지식 검색. 예: search("transformer")"""

    messages.append({"role": "user", "content": question})

    for step in range(max_steps):
        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=512,
            system=system,
            messages=messages
        )
        reply = response.content[0].text
        messages.append({"role": "assistant", "content": reply})
        print(f"\n--- Step {step+1} ---\n{reply}")

        if "Answer:" in reply:
            return reply.split("Answer:")[-1].strip()

        # Action 파싱
        if "Action:" in reply:
            action_line = [l for l in reply.split('\n') if l.startswith("Action:")][0]
            action_str = action_line.replace("Action:", "").strip()
            try:
                tool_name = action_str.split("(")[0]
                arg = action_str[len(tool_name)+1:-1]
                if tool_name in TOOLS:
                    obs = TOOLS[tool_name](arg)
                    messages.append({"role": "user", "content": f"Observation: {obs}"})
                    print(f"Observation: {obs}")
            except Exception as e:
                messages.append({"role": "user", "content": f"Observation: 도구 실행 실패 - {e}"})

    return "최대 스텝 초과"

# 실행
result = react_agent("2의 15승을 계산하고, 트랜스포머가 무엇인지도 알려줘")
```

---

## 3. Tool Use (Anthropic API)

### 3.1 Tool 정의와 호출
```python
from anthropic import Anthropic
import json

client = Anthropic()

tools = [
    {
        "name": "get_weather",
        "description": "도시의 현재 날씨를 반환한다",
        "input_schema": {
            "type": "object",
            "properties": {
                "city": {
                    "type": "string",
                    "description": "도시명 (예: Seoul, Tokyo)"
                },
                "unit": {
                    "type": "string",
                    "enum": ["celsius", "fahrenheit"],
                    "description": "온도 단위"
                }
            },
            "required": ["city"]
        }
    },
    {
        "name": "calculator",
        "description": "수식을 계산한다",
        "input_schema": {
            "type": "object",
            "properties": {
                "expression": {"type": "string", "description": "계산할 수식"}
            },
            "required": ["expression"]
        }
    }
]

def execute_tool(name: str, inputs: dict) -> str:
    if name == "get_weather":
        city = inputs["city"]
        unit = inputs.get("unit", "celsius")
        return json.dumps({"city": city, "temp": 22, "unit": unit, "condition": "맑음"})
    elif name == "calculator":
        try:
            result = eval(inputs["expression"], {"__builtins__": {}}, {})
            return str(result)
        except Exception as e:
            return f"오류: {e}"
    return "알 수 없는 도구"

def agent_loop(user_message: str):
    messages = [{"role": "user", "content": user_message}]

    while True:
        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=1024,
            tools=tools,
            messages=messages
        )

        messages.append({"role": "assistant", "content": response.content})

        if response.stop_reason == "end_turn":
            # 텍스트 응답만 추출
            for block in response.content:
                if hasattr(block, 'text'):
                    return block.text
            return ""

        if response.stop_reason == "tool_use":
            tool_results = []
            for block in response.content:
                if block.type == "tool_use":
                    print(f"도구 호출: {block.name}({block.input})")
                    result = execute_tool(block.name, block.input)
                    print(f"결과: {result}")
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": result
                    })

            messages.append({"role": "user", "content": tool_results})

answer = agent_loop("서울 날씨 알려주고, 22도를 화씨로 변환해줘")
print(f"\n최종 답변:\n{answer}")
```

---

## 4. 메모리 시스템

### 4.1 메모리 유형
| 유형 | 설명 | 구현 |
|------|------|------|
| 단기(In-Context) | 현재 대화창 내 | 메시지 리스트 |
| 장기(External) | DB/파일에 저장 | JSON, 벡터DB |
| 에피소딕 | 과거 대화 기억 | 요약 + 검색 |
| 시맨틱 | 사실/지식 저장 | 임베딩 + 검색 |

### 4.2 슬라이딩 윈도우 메모리
```python
from collections import deque
from anthropic import Anthropic

client = Anthropic()

class ConversationAgent:
    def __init__(self, max_history: int = 10):
        self.history = deque(maxlen=max_history)
        self.system = "당신은 도움이 되는 AI 어시스턴트입니다."

    def chat(self, user_input: str) -> str:
        self.history.append({"role": "user", "content": user_input})

        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=512,
            system=self.system,
            messages=list(self.history)
        )

        reply = response.content[0].text
        self.history.append({"role": "assistant", "content": reply})
        return reply

agent = ConversationAgent(max_history=10)
print(agent.chat("내 이름은 Alice야"))
print(agent.chat("내 이름이 뭐야?"))  # Alice를 기억해야 함
```

### 4.3 요약 기반 장기 메모리
```python
from anthropic import Anthropic
import json

client = Anthropic()

class LongTermMemoryAgent:
    def __init__(self):
        self.recent_history = []       # 최근 N개 메시지
        self.summary = ""              # 이전 대화 요약
        self.max_recent = 6

    def _summarize(self):
        if len(self.recent_history) < self.max_recent:
            return
        to_summarize = self.recent_history[:-2]  # 마지막 2개 제외
        prompt = f"""이전 요약: {self.summary}

새 대화:
{json.dumps(to_summarize, ensure_ascii=False)}

위 내용을 간결하게 요약하라. 중요한 사실만 포함."""

        response = client.messages.create(
            model="claude-haiku-4-5-20251001",  # 빠른 모델로 요약
            max_tokens=256,
            messages=[{"role": "user", "content": prompt}]
        )
        self.summary = response.content[0].text
        self.recent_history = self.recent_history[-2:]

    def chat(self, user_input: str) -> str:
        self.recent_history.append({"role": "user", "content": user_input})

        system = f"이전 대화 요약:\n{self.summary}" if self.summary else "당신은 AI 어시스턴트입니다."

        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=512,
            system=system,
            messages=self.recent_history
        )
        reply = response.content[0].text
        self.recent_history.append({"role": "assistant", "content": reply})
        self._summarize()
        return reply
```

---

## 5. 멀티에이전트 오케스트레이션

### 5.1 오케스트레이터 + 서브에이전트 패턴
```python
from anthropic import Anthropic
import json

client = Anthropic()

# 서브에이전트: 특화된 역할
def researcher_agent(topic: str) -> str:
    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=512,
        system="당신은 연구 전문가입니다. 주어진 주제를 간략하게 조사하고 핵심 정보를 제공합니다.",
        messages=[{"role": "user", "content": f"{topic}에 대해 조사해줘"}]
    )
    return response.content[0].text

def writer_agent(content: str) -> str:
    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=512,
        system="당신은 글쓰기 전문가입니다. 주어진 내용을 읽기 쉬운 형태로 재작성합니다.",
        messages=[{"role": "user", "content": f"다음 내용을 블로그 포스트 형식으로 재작성해줘:\n\n{content}"}]
    )
    return response.content[0].text

def critic_agent(draft: str) -> str:
    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=256,
        system="당신은 편집자입니다. 글의 문제점을 지적하고 개선 방향을 제안합니다.",
        messages=[{"role": "user", "content": f"다음 글을 평가해줘:\n\n{draft}"}]
    )
    return response.content[0].text

# 오케스트레이터: 작업 분배 및 결과 취합
def orchestrator(task: str) -> str:
    print(f"\n[오케스트레이터] 작업 분석: {task}")

    # 1. 연구
    print("\n[연구원 에이전트] 정보 수집 중...")
    research = researcher_agent(task)
    print(f"연구 결과: {research[:200]}...")

    # 2. 작성
    print("\n[작가 에이전트] 초안 작성 중...")
    draft = writer_agent(research)
    print(f"초안: {draft[:200]}...")

    # 3. 검토
    print("\n[편집자 에이전트] 검토 중...")
    feedback = critic_agent(draft)
    print(f"피드백: {feedback[:200]}...")

    return draft

result = orchestrator("AI 에이전트의 미래")
```

### 5.2 병렬 에이전트 (concurrent.futures)
```python
import concurrent.futures
from anthropic import Anthropic

client = Anthropic()

def specialized_agent(task: dict) -> dict:
    role = task["role"]
    question = task["question"]

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=256,
        system=f"당신은 {role} 전문가입니다.",
        messages=[{"role": "user", "content": question}]
    )
    return {"role": role, "answer": response.content[0].text}

def parallel_agents(topic: str) -> list:
    tasks = [
        {"role": "기술", "question": f"{topic}의 기술적 측면은?"},
        {"role": "경제", "question": f"{topic}의 경제적 영향은?"},
        {"role": "윤리", "question": f"{topic}의 윤리적 고려사항은?"},
    ]

    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
        results = list(executor.map(specialized_agent, tasks))

    return results

# 3개 에이전트가 동시에 실행됨
results = parallel_agents("생성형 AI")
for r in results:
    print(f"\n[{r['role']} 전문가]\n{r['answer'][:200]}")
```

---

## 6. 에이전트 평가

### 6.1 평가 지표
```python
# 도구 호출 정확도
def evaluate_tool_calls(expected_tools: list, actual_tools: list) -> float:
    correct = sum(1 for e, a in zip(expected_tools, actual_tools) if e == a)
    return correct / max(len(expected_tools), 1)

# 작업 완료율
def task_completion_rate(tasks: list, completed: list) -> float:
    return sum(1 for t in tasks if t in completed) / len(tasks)
```

---

## 연습문제 풀이 가이드

**레벨 1 (개념 확인)**
- "ReAct 패턴에서 Thought, Action, Observation의 역할은?"
- "멀티에이전트 시스템에서 오케스트레이터가 필요한 이유는?"

**레벨 2 (설계)**
- "코드 작성 에이전트를 설계하라: 어떤 도구가 필요하고, 실패 시 어떻게 복구하나?"
- "에피소딕 메모리와 시맨틱 메모리를 언제 사용하나? 각각 예시를 들어라"

**레벨 3 (코딩)**
- "Anthropic Tool Use API를 사용해 날씨+계산기 도구를 가진 에이전트를 구현하라"
- "오케스트레이터가 연구원→작가→편집자를 순차 실행하는 파이프라인을 구현하라"
- "슬라이딩 윈도우 메모리 에이전트와 일반 에이전트의 10턴 대화 후 메모리 차이를 비교하라"
