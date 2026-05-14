# 2026년 5월 — AI Agent 기술 트렌드 (검증판)

> Context7 공식 문서 + Exa 실제 아티클 기반으로 재정리

---

## 1. 프로토콜 계층 — 사실상 표준 확정

### 계층 구조

```
┌─────────────────────────────────────────┐
│          비즈니스 로직 / 에이전트 코드         │
├──────────────────┬──────────────────────┤
│   MCP (수직 통합)  │    A2A (수평 협업)      │
│  Agent ↓ Tools   │  Agent ↔ Agent       │
├──────────────────┴──────────────────────┤
│    LangGraph / CrewAI / OpenAI SDK       │
│      (프레임워크 네이티브 오케스트레이션)          │
└─────────────────────────────────────────┘
```

| 프로토콜 | 주관 | 방향 | 2026 상태 |
|---------|------|------|----------|
| MCP | Anthropic → Linux Foundation (AAIF) | Agent → Tools/Data | 월 9,700만 SDK 다운로드, 서버 18,000+ |
| A2A | Google → Linux Foundation (AAIF) | Agent ↔ Agent | v1.0 GA (2026 초), 150+ 조직 지원 |
| AG-UI | 커뮤니티 초안 | Agent → UI | 표준 없음, 2026 현재 작업 중 |

**Agentic AI Foundation (AAIF)** — Anthropic, OpenAI, Block 공동 창립. Google, Microsoft, AWS, Cloudflare 플래티넘 멤버.

---

## 2. MCP — Streamable HTTP 전환 (2025-03-26 spec)

기존 HTTP+SSE 이중 엔드포인트 → 단일 `/mcp` 엔드포인트로 통합. 로드밸런서 sticky session 불필요.

```python
# Context7 공식 문서 검증 코드 — FastMCP 서버
from mcp.server.fastmcp import FastMCP
import httpx

mcp = FastMCP("research-tools")

@mcp.tool()
async def search_papers(query: str, max_results: int = 10) -> str:
    """논문 검색 도구"""
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            "https://api.arxiv.org/query",
            params={"search_query": query, "max_results": max_results}
        )
        return resp.text

@mcp.resource("papers://{paper_id}")
async def get_paper(paper_id: str) -> str:
    """특정 논문 전문 반환"""
    async with httpx.AsyncClient() as client:
        resp = await client.get(f"https://arxiv.org/abs/{paper_id}")
        return resp.text

if __name__ == "__main__":
    # stdio: 로컬 | streamable-http: 프로덕션 (MCP 1.5+)
    mcp.run(transport="streamable-http")
```

```bash
# Streamable HTTP — 단일 엔드포인트 POST (tool call)
curl -X POST https://example.com/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -H "MCP-Protocol-Version: 2025-11-25" \
  -H "MCP-Session-Id: {session_id}" \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"search_papers","arguments":{"query":"LLM agents 2026"}}}'

# GET — 서버 initiated 이벤트 수신
curl -X GET https://example.com/mcp \
  -H "Accept: text/event-stream" \
  -H "MCP-Session-Id: {session_id}"
```

---

## 3. LangGraph — 프로덕션 Supervisor 패턴 (공식 문서 검증)

```python
# Exa 아티클 + Context7 공식 코드 기반 검증
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.sqlite import SqliteSaver  # 개발
# from langgraph.checkpoint.postgres import AsyncPostgresSaver  # 프로덕션
from langgraph.types import Command, interrupt
from langchain_anthropic import ChatAnthropic
from langchain_mcp_adapters.client import MultiServerMCPClient
from pydantic import BaseModel
from typing import TypedDict, Annotated, Literal
import operator, sqlite3

class AgentState(TypedDict):
    messages: Annotated[list, operator.add]
    research_result: str
    score: int
    turn: int

# ── MCP 클라이언트 (Streamable HTTP) ──
async def build_graph():
    async with MultiServerMCPClient({
        "research": {"url": "http://localhost:8001/mcp", "transport": "streamable_http"},
        "code":     {"url": "http://localhost:8002/mcp", "transport": "streamable_http"},
    }) as mcp_client:

        research_tools = mcp_client.get_tools_for_server("research")
        code_tools     = mcp_client.get_tools_for_server("code")

        # ── Supervisor 라우팅 스키마 ──
        class RouteDecision(BaseModel):
            next: Literal["research_agent", "code_agent", "FINISH"]
            reason: str

        supervisor_llm = ChatAnthropic(model="claude-opus-4-7")
        router = supervisor_llm.with_structured_output(RouteDecision)

        def supervisor_node(state: AgentState):
            # MAX_TURNS 초과 시 강제 종료
            if state["turn"] >= 5:
                return {"turn": state["turn"]}
            decision = router.invoke(state["messages"])
            return {"messages": state["messages"] + [{"role": "supervisor", "next": decision.next}], "turn": state["turn"] + 1}

        def route_edge(state: AgentState) -> str:
            if state["turn"] >= 5:
                return "end"
            last = state["messages"][-1]
            return last.get("next", "end") if last.get("next") != "FINISH" else "end"

        # ── 전문 에이전트 노드 ──
        from langgraph.prebuilt import create_react_agent

        research_agent = create_react_agent(
            ChatAnthropic(model="claude-sonnet-4-6"), research_tools
        )
        code_agent = create_react_agent(
            ChatAnthropic(model="claude-sonnet-4-6"), code_tools
        )

        def research_node(state):
            result = research_agent.invoke(state)
            return {"research_result": str(result["messages"][-1].content)}

        def code_node(state):
            return {"messages": code_agent.invoke(state)["messages"]}

        # ── 그래프 조립 ──
        builder = StateGraph(AgentState)
        builder.add_node("supervisor", supervisor_node)
        builder.add_node("research_agent", research_node)
        builder.add_node("code_agent", code_node)
        builder.add_edge(START, "supervisor")
        builder.add_conditional_edges("supervisor", route_edge, {
            "research_agent": "research_agent",
            "code_agent": "code_agent",
            "end": END
        })
        builder.add_edge("research_agent", "supervisor")
        builder.add_edge("code_agent", "supervisor")

        # SqliteSaver → 프로덕션은 AsyncPostgresSaver 교체
        checkpointer = SqliteSaver(sqlite3.connect("agent.db", check_same_thread=False))
        graph = builder.compile(
            checkpointer=checkpointer,
            interrupt_before=["code_agent"]  # 코드 실행 전 human-in-the-loop
        )
        return graph
```

### Human-in-the-loop interrupt (공식 문서 패턴)

```python
from langgraph.types import Command, interrupt

def approval_node(state):
    # 체크포인터 + thread_id 필수
    approved = interrupt({
        "message": "이 액션을 승인하시겠습니까?",
        "payload": state["research_result"]
    })
    return {"approved": approved}

# 실행 → interrupt에서 멈춤
config = {"configurable": {"thread_id": "session-123"}}
result = graph.invoke({"messages": [...]}, config=config)
print(result["__interrupt__"])  # 일시 중단된 페이로드

# 승인 후 재개
resumed = graph.invoke(Command(resume={"action": "approve"}), config=config)
```

---

## 4. Claude Managed Agents API (2026.04 공식 출시)

```python
# Exa + 공식 Anthropic 문서 검증
import anthropic

client = anthropic.Anthropic()

# 서브에이전트 생성
reviewer = client.beta.agents.create(
    name="CodeReviewer",
    model="claude-sonnet-4-6",
    system="코드 리뷰 전문가. 보안 취약점과 코드 품질을 검토한다.",
    tools=[{"type": "agent_toolset_20260401"}]
)

test_writer = client.beta.agents.create(
    name="TestWriter",
    model="claude-sonnet-4-6",
    system="테스트 전문가. pytest 기반 단위/통합 테스트를 작성한다.",
    tools=[{"type": "agent_toolset_20260401"}]
)

# 코디네이터 — 서브에이전트 roster 선언
coordinator = client.beta.agents.create(
    name="EngineeringLead",
    model="claude-opus-4-7",
    system="엔지니어링 리드. 코드 리뷰와 테스트 작성을 위임한다.",
    tools=[{"type": "agent_toolset_20260401"}],
    multiagent={
        "type": "coordinator",
        "agents": [
            {"type": "agent", "id": reviewer.id},
            {"type": "agent", "id": test_writer.id},
        ]
    }
    # SDK가 managed-agents-2026-04-01 beta 헤더 자동 설정
)

# 세션 실행
session = client.beta.agents.sessions.create(agent_id=coordinator.id)
response = client.beta.agents.sessions.run(
    session_id=session.id,
    input="auth.py의 Google OAuth 로직을 리뷰하고 테스트를 작성해줘"
)
```

### 위임 패턴 (비용 최적화)

```python
# Parallelization: 독립 서브태스크 동시 실행
# Specialization: 도메인별 시스템 프롬프트 + 전용 툴셋
# Escalation: 복잡한 서브태스크만 Opus로 에스컬레이션

# 비용 지침 (Exa 검증):
# - 고비용 추론: claude-opus-4-7 (오케스트레이터, 분석)
# - 중간: claude-sonnet-4-6 (일반 작업)
# - 대량 처리: claude-haiku-4-5 (검색, 추출) → Sonnet 대비 3배 저렴
```

---

## 5. 3대 SDK 아키텍처 비교 (Exa 검증)

| | Claude Agent SDK | OpenAI Agents SDK | Google ADK |
|--|--|--|--|
| **핵심 패러다임** | tool-use-first, 서브에이전트를 도구로 호출 | explicit handoff | 계층형 에이전트 트리 |
| **언어** | Python, TypeScript | Python, TypeScript | Python, TypeScript, Java, Go |
| **멀티모달** | 텍스트/이미지 | 텍스트/이미지/음성 | 텍스트/이미지/오디오/비디오 |
| **MCP 지원** | 네이티브 | 네이티브 | 어댑터 |
| **A2A 지원** | 계획 중 | 미지원 | 네이티브 (Google Cloud) |
| **선택 기준** | 깊은 OS 접근, 개발자 도구 | 경량, LLM-agnostic | GCP 엔터프라이즈, 멀티언어 |

---

## 6. A2A — Agent Card 패턴

```python
# A2A v1.0 (Linux Foundation, 2026 초 GA) — Exa 검증
from a2a.server import A2AServer
from a2a.types import AgentCard, AgentCapability, AgentSkill

agent_card = AgentCard(
    name="ResearchAgent",
    version="1.0.0",
    description="학술 논문 조사 전문 에이전트",
    # Agent Card = 디지털 명함. 내부 구현 비노출.
    capabilities=[AgentCapability.STREAMING, AgentCapability.PUSH_NOTIFICATIONS],
    skills=[
        AgentSkill(id="search_papers", name="논문 검색", input_modes=["text"]),
        AgentSkill(id="summarize",     name="논문 요약",  input_modes=["text"]),
    ],
    # OAuth 2.0 내장 (A2A 스펙)
    security_schemes={"oauth2": {"type": "oauth2", "flows": {...}}}
)

server = A2AServer(agent=my_research_agent, card=agent_card)
server.run(port=8080)
# Agent Card: GET /.well-known/agent.json 자동 노출

# 다른 에이전트에서 A2A 호출
from a2a.client import A2AClient

async with A2AClient.from_agent_card_url(
    "https://research.example.com/.well-known/agent.json"
) as client:
    # 태스크 라이프사이클 관리 (stateful)
    task = await client.create_task({
        "skill_id": "search_papers",
        "input": {"query": "LangGraph multi-agent 2026", "max_results": 20}
    })
    result = await client.wait_for_completion(task.id)
```

> **주의**: A2A는 MCP보다 약 18개월 늦게 출발. 2026년 현재 공개 A2A 호환 에이전트 ~200개 vs MCP 서버 5,000+.
> 단일 프레임워크 내부 작업은 LangGraph 네이티브 오케스트레이션이 적합, 팀/조직 경계를 넘을 때 A2A 도입.

---

## 7. 현재 프로젝트 관련성 체크

| 항목 | 현재 상태 | 2026 트렌드 갭 |
|------|----------|--------------|
| LangGraph + Gemini | ✅ 사용 중 | `interrupt()` / `Command(resume=...)` 적용 여부 확인 |
| 체크포인터 | Django Session 자체 구현 | `AsyncPostgresSaver` 교체 고려 (roadmap.md §2) |
| MCP | 미적용 | Researcher 도구를 MCP 서버로 노출 시 외부 연동 가능 |
| A2A | 미적용 | 현재 단일 배포 → 도입 불필요, 미래 멀티팀 확장 시 고려 |
| Human-in-the-loop | APPROVE 로직 자체 구현 | LangGraph `interrupt()` 패턴으로 표준화 가능 |

---

## Sources

1. The AI Agent Protocol Stack: MCP, A2A & What Comes Next
2. LangGraph + MCP: Multi-Agent Workflows 2026 Guide
3. MCP vs A2A: When to Use Each Protocol
4. Multi-Agent Systems Hit Production
5. Building Production-Ready Multi-Agent Systems with Claude Agent SDK
6. Anthropic Managed Agents API 공식 문서
7. Context7 — LangGraph 공식 문서 (interrupt, checkpointer)
8. Context7 — MCP 공식 스펙 (FastMCP, Streamable HTTP)
