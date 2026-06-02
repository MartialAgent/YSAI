# DAG 기반 멀티에이전트 연구 지형도

**작성일:** 2026-05-09  
**목적:** 연구 범위 설정 및 기여 지점 식별을 위한 문헌 정리

---

## 1. 핵심 연구 키워드 5개

```
1. DAG-Structured Multi-Agent Orchestration   — 구조
2. LLM-as-Judge / Agent Evaluation            — 평가
3. Error Propagation in Agentic Pipelines     — 신뢰성
4. Human-in-the-Loop (HITL) Agent Systems     — 개입
5. Agent Observability & Execution Tracing    — 시각화
```

각 키워드는 독립된 연구 분야이면서 DAG 에이전트를 중심으로 교차합니다.

```
                    ┌─────────────────────────┐
                    │  DAG Multi-Agent System  │
                    └────────────┬────────────┘
             ┌──────────┬────────┴────────┬──────────┐
             ▼          ▼                 ▼          ▼
          평가       신뢰성             HITL        시각화
      (LLM-Judge) (Error Prop.)    (Oversight)  (Tracing)
```

---

## 2. 키워드별 최신 연구 · 한계 · 가능성

---

### 2-1. DAG-Structured Multi-Agent Orchestration

**연구 내용**

| 논문 | 연도 | 핵심 내용 |
|------|------|----------|
| DynTaskMAS: Dynamic Task Graph-driven Framework for Parallel LLM-based MAS (arXiv:2503.07675) | ICAPS 2025 | DAG 자동 생성 및 비동기 병렬 실행 스케줄링, 실행 시간 21~33% 단축 |
| From Agent Loops to Structured Graphs: A Scheduler-Theoretic Framework (arXiv:2604.11378) | 2026 | LLM 그래프의 형식적 태스크 스케줄링 이론화 (포지션 페이퍼, 실증 결과 없음) |
| Why Do Multi-Agent LLM Systems Fail? (arXiv:2503.13657) | 2025 | 14개 실패 유형 분류 체계(MAST), 7개 MAS 프레임워크 1,600+ 트레이스 분석 |

**현재 한계**

- 태스크 의존성(엣지)을 **사전에 수동 정의**해야 함 — 실행 중 구조 변화 불가
- 그래프 토폴로지 자체가 적절한지 검증하는 방법이 없음
- 노드 단위 평가는 있지만 **파이프라인 전체 품질 평가** 기준이 없음

**가능성**

- 실행 피드백을 반영해 의존성 그래프를 동적으로 수정하는 방향
- **우리 연구 연결점**: 노드 게이트(A-score)가 파이프라인 수준 품질에 미치는 영향 측정

---

### 2-2. LLM-as-Judge / Agent Evaluation

**연구 내용**

| 논문 | 연도 | 핵심 내용 |
|------|------|----------|
| A Survey on LLM-as-a-Judge (arXiv:2411.15594) | 2024 | G-Eval, Multi-LLM Judge, 편향 분류 종합 서베이 |
| Crowd Comparative Reasoning: Unlocking Comprehensive Evaluations for LLM-as-a-Judge (arXiv:2502.12501) | ACL 2025 | Crowd 비교 추론 기반 평가 향상, 5개 벤치마크 평균 6.7% 정확도 향상 |
| G-Eval (EMNLP 2023 / 2024 확장) | 2023–24 | CoT 루브릭 + logprobs 가중 평균으로 인간 평가 정렬 개선 |

**현재 한계**

- **동일 모델 편향**: GPT는 GPT 출력에 더 높은 점수를 줌 (실험 exp06에서 직접 확인)
- 프롬프트 형식만 바꿔도 점수가 크게 달라짐 — 재현성 낮음
- **완전성(Completeness) 미측정**: "출력이 그럴듯한가"는 보지만 "요구한 걸 다 했는가"는 못 봄

**가능성**

- 도메인별 자동 프롬프트 캘리브레이션
- **우리 연구 연결점**: A-score의 S·C 문제 + Completeness score 부재가 이 한계와 직결됨

---

### 2-3. Error Propagation in Agentic Pipelines

**연구 내용**

| 논문 | 연도 | 핵심 내용 |
|------|------|----------|
| Why Do Multi-Agent LLM Systems Fail? (arXiv:2503.13657) | 2025 | 실패 유형 중 태스크 검증 실패가 최다 — 중간 검증 부재가 핵심 원인으로 지목 |
| Sherlock: Reliable and Efficient Agentic Workflow Execution (arXiv:2511.00330) | 2024 | 오류 전파 차단 메커니즘 |
| On the Resilience of LLM-Based Multi-Agent Collaboration with Faulty Agents (arXiv:2408.00989) | ICML 2025 | 계층 구조가 성능 하락 5.5%로 최고 복원력, Challenger/Inspector로 오류 96.4% 복구 |

**현재 한계**

- 현재 시스템은 **최종 출력만 검증** — 중간 노드 오류를 조기에 차단하지 못함
- 오류 전파 범위에 대한 **형식적 보장(formal guarantee)** 없음
- 병렬 실행 시 상태 전파로 인한 중복 작업 문제

**가능성**

- DAG 중간 노드에서 검증 게이트를 두는 것이 오류 증폭을 줄인다는 실증
- **우리 연구 연결점**: 이것이 DAG + A-score 게이트의 존재 이유이자 논문의 핵심 주장이 될 수 있음

---

### 2-4. Human-in-the-Loop (HITL) Agent Systems

**연구 내용**

| 논문 / 사례 | 연도 | 핵심 내용 |
|------------|------|----------|
| Human-In-the-Loop Software Development Agents, HULA (arXiv:2411.12924) | ICSE 2025 | 개발자 가이드 코드 생성에서 HITL 프레임워크, 플랜 승인률 82% |
| GitHub Copilot Workspace | 2025 | 멀티파일 변경에 필수 승인 게이트 도입 |

**현재 한계**

- **언제 개입할지 기준이 없음** — 대부분 임의의 임계값 또는 수동 설정
- 인간에게 보여주는 컨텍스트가 부족해 판단 부하(cognitive load)가 높음
- 개입 후 **하위 노드 재실행 범위** 결정 로직이 ad-hoc

**가능성**

- AMBIGUOUS 판정 기준을 학습 기반으로 자동화
- **우리 연구 연결점**: Orchestrator의 AMBIGUOUS 상태 + `calculate_impact_factor()`가 이 문제를 구조적으로 다루고 있음. 논문에서 HITL 설계 원칙으로 발전 가능

---

### 2-5. Agent Observability & Execution Tracing

**연구 내용**

| 도구 / 논문 | 연도 | 핵심 내용 |
|------------|------|----------|
| OpenTelemetry LLM Tracing Standard | 2024 | 에이전트 계측을 위한 벤더 중립 표준 |
| LangSmith / Langfuse / Datadog | 2024–25 | 멀티에이전트 워크플로우 waterfall 트레이싱 |
| 8 LLM Observability Tools Survey (LangChain) | 2025 | 도구 비교 및 한계 정리 |

**현재 한계**

- 단일 실행 추적에는 강하지만 **수천 번 실행의 집합적 패턴 탐지** 불가
- 시맨틱 이상(semantic anomaly) 표현 표준이 없음 — 로그는 있지만 의미 해석 불가
- 노드 수준 점수와 그래프 수준 시각화가 연결되지 않음

**가능성**

- 집합 관측성 시스템으로 에이전트 집단의 이상 행동 자동 탐지
- **우리 연구 연결점**: A-score per node를 시각화하면 어느 노드가 병목인지 즉시 파악 가능. 낮은 우선순위이지만 실험 결과를 논문 figure로 만드는 데 직접 활용

---

## 3. 연구 공백 지도 (Gap Map)

```
현재 연구가 많은 영역          연구 공백 (우리가 파고들 수 있는 곳)
─────────────────────         ──────────────────────────────────
DAG 실행 스케줄링              중간 노드 검증이 오류 전파에 미치는 효과
LLM 품질 평가 (G-Eval 등)      완전성(Completeness) 측정
단일 실행 트레이싱              파이프라인 전체 신뢰도 지표
HITL 개입 메커니즘             언제 개입할지 판단 기준
```

---

## 4. 우리 프로젝트의 위치

```
기존 연구가 다루는 것:
  "어떻게 DAG를 실행하는가" + "LLM 출력을 어떻게 평가하는가"

우리가 추가할 수 있는 것:
  "DAG 중간 노드에 평가 게이트를 달면
   오류 전파가 얼마나 줄어드는가"
  + "기존 A-score의 어떤 성분이 실제로 유효한가"
```

---

*참고 논문 링크*
- [Why Do Multi-Agent LLM Systems Fail? (arXiv:2503.13657)](https://arxiv.org/abs/2503.13657)
- [A Survey on LLM-as-a-Judge (arXiv:2411.15594)](https://arxiv.org/abs/2411.15594)
- [DynTaskMAS (arXiv:2503.07675)](https://arxiv.org/abs/2503.07675)
- [From Agent Loops to Structured Graphs (arXiv:2604.11378)](https://arxiv.org/abs/2604.11378)
- [Crowd Comparative Reasoning: Unlocking Comprehensive Evaluations for LLM-as-a-Judge (arXiv:2502.12501)](https://aclanthology.org/2025.acl-long.252.pdf)
- [Human-In-the-Loop Software Development Agents (arXiv:2411.12924)](https://arxiv.org/abs/2411.12924)
- [Sherlock: Reliable Agentic Workflow Execution (arXiv:2511.00330)](https://arxiv.org/abs/2511.00330)
- [On the Resilience of LLM-Based Multi-Agent Collaboration with Faulty Agents (arXiv:2408.00989)](https://arxiv.org/abs/2408.00989)
