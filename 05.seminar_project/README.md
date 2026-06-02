# AgentDAG

**DAG 기반 멀티 에이전트 워크플로우 신뢰성 제어 프레임워크**

> 3단계 상태 평가(PFA)와 적응형 복구를 통한 LLM 에이전트 파이프라인 안정화 연구 프로젝트

---

## 개요

멀티 에이전트 LLM 워크플로우에서는 초기 노드의 작은 환각(Hallucination)이나 오류가 하위 노드로 조용히 전파되는 **오류 캐스케이딩** 문제가 발생합니다. 기존 솔루션은 이를 무시하거나, 전체 워크플로우를 처음부터 재시작하는 비용 문제를 안고 있습니다.

AgentDAG는 이 문제를 세 가지 핵심 메커니즘으로 해결합니다:

| 메커니즘 | 설명 |
|---|---|
| **PFA 평가 엔진** | 각 노드 실행 후 출력을 PASS / FAIL / AMBIGUOUS로 자동 분류 |
| **부분 역전파(Partial Backpropagation)** | 수정된 노드의 영향도(Impact Factor)가 높은 하위 노드만 선택적으로 재실행 |
| **Human-in-the-Loop (HITL)** | AMBIGUOUS 상태에서 자동으로 실행을 중단하고 인간 검토를 요청 |

---

## 아키텍처

```
┌─────────────────────────────────────────────────────────────┐
│                      DAGOrchestrator                        │
│                                                             │
│  ┌──────────┐  depends_on   ┌──────────┐  depends_on  ┌───────────┐ │
│  │  Node A  │ ────────────► │  Node B  │ ───────────► │  Node C  │ │
│  │ (Worker) │               │ (Worker) │              │ (Worker) │ │
│  └──────────┘               └──────────┘              └───────────┘ │
│       │                          │                         │        │
│       ▼                          ▼                         ▼        │
│  ┌─────────┐               ┌─────────┐               ┌─────────┐   │
│  │  PFA    │               │  PFA    │               │  PFA    │   │
│  │Evaluator│               │Evaluator│               │Evaluator│   │
│  └─────────┘               └─────────┘               └─────────┘   │
│       │                                                             │
│   AMBIGUOUS? ──────────────────────────────► HITL Terminal Input   │
└─────────────────────────────────────────────────────────────────────┘
```

### PFA 평가 공식

```
A-Score = α × (1 - S) + β × D × (1 - C)
```

| 변수 | 설명 |
|---|---|
| `S` | 코사인 유사도 (Worker 응답 2회 → 임베딩 비교) |
| `C` | Worker 자기 신뢰도 (0~1) |
| `D` | Critic 이탈 점수 (0~1, Critic LLM이 평가) |
| `α`, `β` | 가중치 파라미터 (기본값: 각 0.5) |

**분기 규칙:**
- `D >= 0.7` → **FAIL** (명백한 결함, 즉시 재시도)
- `A > 0.7` → **AMBIGUOUS** (불확실, HITL 대기)
- 그 외 → **PASS**

### 영향도(Impact Factor) 계산

```
path_impact = reliance_R / (distance + 1 + 1)
```

수정된 노드로부터 BFS 탐색으로 누적 영향도를 계산하고, `I > 0.4`인 하위 노드만 재실행합니다.

---

## 프로젝트 구조

```
AgentDAG/
├── main.py               # Exp 01 진입점 (자율주행 시장 분석 시나리오)
├── main_exp02.py         # Exp 02 진입점 (B2B SaaS 가격 전략 시나리오)
├── requirements.txt      # 의존성 패키지
├── prd.md                # 제품 요구사항 문서
├── technical_specs.md    # 기술 명세서
└── src/
    ├── config.py         # 전역 파라미터 및 모델명 설정
    ├── models.py         # Pydantic 데이터 모델 정의
    ├── evaluator.py      # PFA 평가 로직 (Worker + Critic + A-Score)
    └── orchestrator.py   # DAG 실행 제어, 재시도, 부분 역전파, 상태 저장
```

---

## 사용 기술 스택

| 구분 | 기술 |
|---|---|
| **언어** | Python 3.10+ |
| **LLM (Worker)** | `gpt-4o-mini` (비용 효율, 생성 및 자기 신뢰도 평가) |
| **LLM (Critic)** | `gpt-4o` (정확도 우선, 논리적 결함 탐지) |
| **임베딩** | `text-embedding-3-small` (유사도 S 계산) |
| **데이터 검증** | `pydantic >= 2.6.4` |
| **수치 연산** | `numpy >= 1.26.4` (코사인 유사도) |

> **외부 오케스트레이션 없음**: LangGraph, LangChain, CrewAI 등 기존 프레임워크 미사용. DAG 엔진 직접 구현.

---

## 빠른 시작

### 1. 환경 설정

```bash
# 의존성 설치
pip install -r requirements.txt

# .env 파일 생성
echo "OPENAI_API_KEY=sk-..." > .env
```

### 2. Exp 01 실행 (자율주행 시나리오)

```bash
python main.py
```

**DAG 구조:**
```
A_Trend (자율주행 트렌드 분석)
    └── B_Model [R=0.9] (구독형 수익 모델 설계)
            └── C_Copy [R=0.5] (마케팅 이메일 제목 작성)
```

### 3. Exp 02 실행 (B2B SaaS 가격 전략)

```bash
python main_exp02.py
```

**DAG 구조:**
```
A_Pricing (3-Tier 가격 설계 - 수학적 제약 포함)
    └── B_ROI [R=0.9] (1년 ROI 계산, 정확한 수식 요구)
            └── C_AdCopy [R=0.5] (LinkedIn 광고문구, ROI% 인용 필수)
```

### 4. 재시작 및 체크포인트 복구

실행 중 중단된 경우, 다시 실행하면 `state.json` / `state_exp02.json`에서 자동으로 이전 상태를 복구합니다. 이미 PASS된 노드는 건너뜁니다.

### 5. Human-in-the-Loop

AMBIGUOUS 노드 발생 시 터미널에 프롬프트가 나타납니다:

```
[HITL] Node 'A_Trend' is AMBIGUOUS.
Current output: ...
Enter corrected output (or press Enter to skip): 
```

수정된 출력을 입력하면 영향도 계산 후 필요한 하위 노드만 재실행됩니다.

---

## 실험 결과

### Exp 01 — 자율주행 시장 분석 (2026.03.30)

| 노드 | A-Score | 상태 |
|---|---|---|
| A_Trend | 0.051 | PASS |
| B_Model | 0.031 | PASS |
| C_Copy | 0.016 | PASS |

**주요 발견:** `gpt-4o-mini`의 출력 일관성이 너무 높아 S ≈ 1.0이 항상 유지됨. FAIL/AMBIGUOUS 경로 미발동.

### Exp 02 — B2B SaaS 가격 전략 (2026.03.30)

| 노드 | A-Score | 신뢰도(C) | 상태 |
|---|---|---|---|
| A_Pricing | 0.050 | - | PASS |
| B_ROI | 0.005 | 1.0 | PASS |
| C_AdCopy | 0.033 | - | PASS |

**주요 발견:** 수학적 제약이 있는 프롬프트에서 Node B가 C=1.0 달성. Critic이 가격 수치에 대해 환각을 일으켰으나 A-Score 공식이 이를 흡수하여 오검출(False FAIL) 방지.

---

## 파라미터 설정 (`src/config.py`)

```python
ALPHA = 0.5                  # 유사도 발산 가중치
BETA = 0.5                   # Critic 이탈 가중치
A_SCORE_THRESHOLD = 0.7      # 이 이상이면 AMBIGUOUS
I_FACTOR_THRESHOLD = 0.4     # 이 이상이면 역전파 시 재실행
MAX_FAIL_RETRIES = 2         # FAIL 자동 재시도 한계
WORKER_MODEL = "gpt-4o-mini"
CRITIC_MODEL = "gpt-4o"
EMBEDDING_MODEL = "text-embedding-3-small"
```

---

## 개선 방향

### 단기 개선사항

1. **FAIL/AMBIGUOUS 경로 테스트**
   - 현재 `A_SCORE_THRESHOLD = 0.7`이 너무 높음
   - `β` 값을 0.8~1.0으로 올리거나 임계값을 0.4~0.5로 낮춰 AMBIGUOUS 경로 검증 필요

2. **더 어려운 프롬프트 설계 (Exp 03)**
   - 모순되는 제약 조건을 가진 태스크
   - 정보 부족 또는 불가능한 요구사항이 포함된 시나리오

3. **API 호출 최적화**
   - 현재 노드당 최소 5회 API 호출 (Worker×2 + 신뢰도 + 임베딩 + Critic)
   - Worker 응답 2회를 병렬 호출(`asyncio`)로 개선 가능 → 레이턴시 ~30% 절감

### 중기 개선사항

4. **병렬 노드 실행**
   - 현재 DAG를 위상 정렬 순서로 순차 실행
   - 의존성이 없는 동일 레벨 노드들은 병렬 실행 가능 (`asyncio.gather`)

5. **동적 파라미터 조정**
   - 노드별로 `α`, `β`, `A_SCORE_THRESHOLD`를 다르게 설정
   - 비즈니스 로직이 중요한 노드에는 더 엄격한 임계값 적용

6. **비용 추적**
   - 각 실험의 OpenAI API 호출 비용을 계산하여 state.json에 저장
   - 부분 역전파 vs 전체 재시작 비용 비교 데이터 수집

### 장기 개선사항

7. **웹 UI / 시각화**
   - DAG 구조와 각 노드의 실시간 상태를 시각화하는 대시보드
   - HITL 인터페이스를 터미널 대신 웹 브라우저로 제공

8. **워커 모델 다양화**
   - 현재 OpenAI 모델에 종속
   - Anthropic Claude, Google Gemini, Ollama(로컬 모델) 등 플러그인 방식으로 지원

9. **학술 논문 제출**
   - 실험 확장: 다양한 도메인, 노드 수, DAG 복잡도
   - FAIL/AMBIGUOUS 발생 조건과 복구 비용 절감률 정량화

---

## 라이선스

연구 목적 프로젝트입니다.
