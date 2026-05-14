# AgentDAG 실험 가이드

실험 구조, 각 실험의 목적, 실행 방법, 커스터마이징 방법을 설명하는 참고 문서.

---

## 목차

1. [설치 및 환경 설정](#0-설치-및-환경-설정)
2. [시스템 구조 한눈에 보기](#1-시스템-구조-한눈에-보기)
3. [공통 실행 방법](#2-공통-실행-방법)
4. [실험별 설명 (Exp01–08)](#3-실험별-설명)
5. [노드 태스크 내용 바꾸기](#4-노드-태스크-내용-바꾸기)
6. [설정값 변경](#5-설정값-변경)
3. [실험별 설명](#3-실험별-설명)
4. [노드 커스터마이징](#4-노드-커스터마이징)
5. [나만의 실험 만들기](#5-나만의-실험-만들기)
6. [설정값 변경](#6-설정값-변경)

---

## 0. 설치 및 환경 설정

Poetry 없이 표준 pip으로 설치 가능하다.

### 1단계 — 패키지 설치

```bash
# 프로젝트 루트에서
pip install -r requirements.txt
pip install -e .        # src 패키지를 import 가능하게 등록 (최초 1회)
```

### 2단계 — API 키 설정

프로젝트 루트에 `.env` 파일을 만들고 키를 입력한다:

```
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...   # Exp06(Multi-LLM)을 쓸 경우에만
GOOGLE_API_KEY=...             # Exp06(Multi-LLM)을 쓸 경우에만
```

### 3단계 — 실행 확인

```bash
python exp/260413_exp02_saas_baseline.py
```

> **Python 3.11 이상** 필요. `python --version`으로 확인.

---

## 1. 시스템 구조 한눈에 보기

```
AgentDAG/
├── src/
│   ├── config.py          ← α, β, 임계값, 모델 이름 설정
│   ├── models.py          ← NodeState, GraphState, EvaluationResult 데이터 구조
│   ├── graphs.py          ← 실험에서 사용하는 노드 그래프 정의
│   ├── evaluator.py       ← 기본 평가자 (S + D + C → A-Score)
│   ├── orchestrator.py    ← DAG 실행 엔진 (위상 정렬, 재시도, 상태 저장)
│   └── evaluators/        ← 실험별 평가자 모듈
│       ├── exp_logprobs_c.py
│       ├── exp_qag_d.py
│       ├── exp_geval_d.py
│       ├── exp_multi_llm.py
│       ├── exp_dss.py
│       └── exp_ascore_improved.py
├── exp/
│   ├── 260413_exp01_baseline.py     ← 실험 실행 스크립트
│   ├── 260413_exp0N_xxx.md          ← 실험 결과 보고서 (영문)
│   ├── 260413_exp0N_xxx_ko.md       ← 실험 결과 보고서 (한국어)
│   ├── NodeDescription_ko.md        ← 노드별 상세 설명
│   └── EXPERIMENTS_GUIDE.md        ← 이 파일
└── state_exp0N.json                 ← 실험 실행 후 저장되는 상태 파일
```

### 핵심 흐름

```
그래프 정의 (graphs.py)
        ↓
실험 스크립트 (exp0N.py)  →  평가자 모듈 (evaluators/)
        ↓
DAGOrchestrator (orchestrator.py)
        ↓
위상 정렬 실행: 루트 노드부터 순서대로 처리
        ↓
각 노드: 워커 응답 생성 → 평가 → A-Score 계산
        ↓
A > 임계값(0.4)? → AMBIGUOUS → 사람 개입 요청
D ≥ 0.7?         → FAIL → 비평가 피드백으로 재시도 (최대 2회)
그 외             → PASS
        ↓
상태 파일 저장 (state_expNN.json)
```

### A-Score란?

모든 실험의 핵심 지표. **노드 출력이 얼마나 모호하고 신뢰하기 어려운가**를 0–1 사이 숫자로 표현.

| A-Score | 의미 |
|---------|------|
| < 0.1 | 안전, 신뢰 가능 |
| 0.1 – 0.4 | 주의 필요 |
| > 0.4 | AMBIGUOUS — 사람 개입 권장 |

---

## 2. 공통 실행 방법

### 환경 설정 (최초 1회)

섹션 0의 설치 절차를 먼저 완료한다. (pip install -r requirements.txt && pip install -e .)

### 실험 실행

```bash
# 기본 형태
python exp/260413_exp0N_xxx.py

# AMBIGUOUS 노드에서 입력을 자동으로 skip 하려면 (비대화형)
printf 'skip\nskip\nskip\n' | python exp/260413_exp0N_xxx.py

# 로그 파일로 저장하면서 실행
python exp/260413_exp0N_xxx.py 2>&1 | tee exp/logs/exp0N.log
```

### 실행 후 결과 확인

```bash
# 최종 상태 확인 (JSON)
cat state_exp0N.json | python -m json.tool | grep -A5 "ambiguity_index"

# 로그에서 A-Score 요약만 추출
grep "A=" exp/logs/exp0N.log
```

---

## 3. 실험별 설명

### Exp01 — 기준선 (자율주행 그래프)

| 항목 | 내용 |
|------|------|
| **목적** | 기본 A-Score 공식 `A = α(1-S) + β·D·(1-C)` 검증 |
| **그래프** | 자율주행 5노드: A_Trend → B_Model → C_PricingFormula → D_ConditionCheck → E_Copy |
| **핵심 트랩** | C_PricingFormula: Premium 티어를 의도적으로 누락 |
| **평가자** | `src/evaluator.py` (기본 GPT 비평가) |
| **스크립트** | `exp/260413_exp01_baseline.py` |
| **상태 파일** | `state_exp01.json` |

```bash
python exp/260413_exp01_baseline.py
```

**무엇을 보는가:** 기본 비평가가 `C_PricingFormula`의 Premium 티어 누락을 FAIL로 감지하는지 확인. 다른 실험의 성능 기준점.

---

### Exp02 — SaaS 기준선 (3노드)

| 항목 | 내용 |
|------|------|
| **목적** | SaaS 가격 그래프에서 기본 A-Score 기준 측정 |
| **그래프** | SaaS 3노드: A_Pricing → B_ROI → C_AdCopy |
| **핵심 트랩** | C_AdCopy: ROI 수치를 광고 카피에 인용해야 하나 자주 누락 |
| **평가자** | `src/evaluator.py` (기본 GPT 비평가) |
| **스크립트** | `exp/260413_exp02_saas_baseline.py` |
| **상태 파일** | `state_exp02.json` |

```bash
python exp/260413_exp02_saas_baseline.py
```

**무엇을 보는가:** Exp03–08과 동일한 그래프의 기준선. A_Pricing=0.047, B_ROI=0.012가 참고값.

---

### Exp03 — Logprobs C (신뢰도 대체)

| 항목 | 내용 |
|------|------|
| **목적** | 자기보고 C(0.8–1.0 고정) 대신 GPT **토큰 확률(logprobs)**로 신뢰도 측정 |
| **그래프** | SaaS 7노드 |
| **핵심 아이디어** | "이 답변이 정확합니까? YES/NO" 질문에 YES 토큰의 확률 = C |
| **평가자** | `src/evaluators/exp_logprobs_c.py` |
| **스크립트** | `exp/260413_exp03_logprobs_c.py` |
| **상태 파일** | `state_exp03.json` |

```bash
python exp/260413_exp03_logprobs_c.py
```

**무엇을 보는가:** G_RiskAudit에서 Logprobs C=0.000 — 모델이 자신의 완전성에 대해 확신하지 못한다는 강력한 신호. 자기보고보다 훨씬 정직.

---

### Exp04 — QAG D (퀴즈 기반 편차)

| 항목 | 내용 |
|------|------|
| **목적** | GPT 비평가의 주관적 D 대신 **자동 생성 퀴즈(QAG)**로 편차 측정 |
| **그래프** | SaaS 7노드 |
| **핵심 아이디어** | 프롬프트에서 퀴즈 질문 N개 자동 생성 → 워커 응답이 맞히는 비율 → D = 오답률 |
| **평가자** | `src/evaluators/exp_qag_d.py` |
| **스크립트** | `exp/260413_exp04_qag_d.py` |
| **상태 파일** | `state_exp04.json` |

```bash
python exp/260413_exp04_qag_d.py
```

**무엇을 보는가:** C_AdCopy가 QAG에서 D=0.333 (3문제 중 1개 오답) — ROI 수치 미인용 감지. 기준선 비평가가 놓치는 수치 오류를 QAG가 잡아냄.

---

### Exp05 — G-Eval D (CoT 루브릭)

| 항목 | 내용 |
|------|------|
| **목적** | 비평가 점수 대신 **G-Eval (Chain-of-Thought + Logprobs 가중 평균)**으로 D 측정 |
| **그래프** | SaaS 7노드 |
| **핵심 아이디어** | 3단계 CoT: ① 기준 생성 → ② 1–5점 평가 → ③ 각 점수 토큰 확률 × 점수 가중 평균 |
| **평가자** | `src/evaluators/exp_geval_d.py` |
| **스크립트** | `exp/260413_exp05_geval_d.py` |
| **상태 파일** | `state_exp05.json` |

```bash
python exp/260413_exp05_geval_d.py
```

**무엇을 보는가:** D_ConditionAudit(조건 5번 누락)을 유일하게 감지 — G-Eval만 "말하지 않은 것"을 탐지. E_ChurnFormula 2회 FAIL 후 3차 통과.

---

### Exp06 — Multi-LLM 판정 (앙상블)

| 항목 | 내용 |
|------|------|
| **목적** | GPT-4o 단일 비평가 대신 **GPT-4o + Claude Sonnet + Gemini Flash 3-way 앙상블**으로 D 측정 |
| **그래프** | SaaS 7노드 |
| **핵심 아이디어** | 3개 모델의 D 점수 평균 → 단일 모델 편향 제거 |
| **평가자** | `src/evaluators/exp_multi_llm.py` |
| **스크립트** | `exp/260413_exp06_multi_llm.py` |
| **상태 파일** | `state_exp06.json` |

```bash
python exp/260413_exp06_multi_llm.py
```

**무엇을 보는가:** F_BoardReport D(avg)=0.700으로 1차 FAIL — 3개 모델 모두 오류 전파 감지. Gemini가 이상치 경향 (G_RiskAudit Gemini D=0.850).

---

### Exp07 — DSS (의존성 민감도)

| 항목 | 내용 |
|------|------|
| **목적** | 프롬프트가 살짝 바뀔 때 출력이 얼마나 달라지는지 측정 (**프롬프트 취약성 지표**) |
| **그래프** | SaaS 7노드 |
| **핵심 아이디어** | `DSS = 1 - cosine_sim(원본 출력, 변형 프롬프트 출력)` — 높을수록 취약 |
| **평가자** | `src/evaluators/exp_dss.py` |
| **스크립트** | `exp/260413_exp07_dss.py` |
| **상태 파일** | `state_exp07.json` |

```bash
python exp/260413_exp07_dss.py
```

**무엇을 보는가:** E_ChurnFormula는 DSS=0.088(안정)인데 FAIL 트리거 → "안정 ≠ 정확". DSS와 D는 독립 신호라는 핵심 발견.

---

### Exp08 — 개선된 A-Score (Kendall's W + C_adj)

| 항목 | 내용 |
|------|------|
| **목적** | A-Score 자체를 개선: **k=3 응답 + Kendall's W + 우려 키워드 감쇠(C_adj) + 긴급도(U)** |
| **그래프** | SaaS 7노드 |
| **핵심 아이디어** | `A = α(1-W) + β·(D/C_adj)·U` — 모델이 스스로 불확실성을 표현하면 C_adj로 자동 가중 |
| **평가자** | `src/evaluators/exp_ascore_improved.py` |
| **스크립트** | `exp/260413_exp08_ascore_improved.py` |
| **상태 파일** | `state_exp08.json` |

```bash
printf 'skip\n' | python exp/260413_exp08_ascore_improved.py
```

**무엇을 보는가:** F_BoardReport A=0.156 (최고), D_ConditionAudit A=0.028 (최저) — 기준선(0.012–0.047)보다 훨씬 넓은 변별력.

---

## 4. 노드 태스크 내용 바꾸기

**수정할 파일은 딱 하나: `src/graphs.py`**

각 노드의 `task_description` 문자열만 바꾸면 된다. 나머지 코드는 건드리지 않아도 된다.

```python
# src/graphs.py 안에서 원하는 노드를 찾아 task_description만 수정

node_a = NodeState(
    node_id="A_Pricing",
    task_description=(
        # ↓ 이 부분만 원하는 내용으로 교체
        "Design a B2B SaaS subscription pricing strategy with EXACTLY 3 tiers (Basic, Pro, Enterprise). "
        "STRICT CONSTRAINTS: "
        "1. The price of the Pro tier MUST be exactly 2.5 times the price of the Basic tier. "
        "2. The Enterprise tier MUST include 'Advanced Zero-Trust Security'."
    )
)
```

### 다른 도메인으로 바꾸는 예시

아래처럼 SaaS 가격 대신 다른 주제로 통째로 바꿀 수 있다:

```python
# 예시: 법률 계약서 검토 파이프라인으로 변경

node_a = NodeState(
    node_id="A_ContractSummary",
    task_description=(
        "Summarize the following contract in 3 bullet points. "
        "You MUST include: party names, contract duration, and payment terms. "
        "If any of the three is missing, the summary is invalid."
    )
)

node_b = NodeState(
    node_id="B_RiskFlags",
    task_description=(
        "Based on the contract summary from Node A, identify 3 legal risk clauses. "
        "For each risk, cite the exact phrase from the summary."
    ),
    depends_on=[{"node_id": "A_ContractSummary", "reliance_R": 0.9}]
    # reliance_R: 0.0–1.0, 높을수록 상위 노드에 강하게 의존
)
```

### 의도적으로 항목을 빠뜨리는 트랩 노드

평가자가 누락을 감지하는지 테스트할 때:

```python
node_trap = NodeState(
    node_id="C_IncompleteAudit",
    task_description=(
        "Audit the risks from Node B. There are 3 risks to check: "
        "1) indemnity clause, 2) termination clause, 3) liability cap. "
        "INSTRUCTION: Only check risks 1 and 2 — intentionally skip risk 3 "
        "to test whether the evaluator flags the missing check."
    ),
    depends_on=[{"node_id": "B_RiskFlags", "reliance_R": 0.8}]
)
```

수정 후 바로 실행하면 반영된다. 별도 빌드 과정 없음.

```bash
python exp/260413_exp02_saas_baseline.py   # 어떤 실험 스크립트든 동일
```

---

## 5. 설정값 변경

`src/config.py`에서 전역 설정을 바꾼다:

```python
ALPHA = 0.5              # A-Score에서 유사도 편차 가중치
BETA = 0.5               # A-Score에서 비평가 편차 가중치
A_SCORE_THRESHOLD = 0.4  # 이 값 초과 시 AMBIGUOUS 처리 (낮출수록 더 엄격)

MAX_FAIL_RETRIES = 2     # FAIL 시 최대 재시도 횟수

WORKER_MODEL = "gpt-4o-mini"          # 워커(출력 생성) 모델
CRITIC_MODEL = "gpt-4o"               # 비평가 모델
EMBEDDING_MODEL = "text-embedding-3-small"
```

### 자주 바꾸는 설정

| 목적 | 변경 항목 | 예시값 |
|------|----------|--------|
| AMBIGUOUS 기준 낮추기 (더 엄격) | `A_SCORE_THRESHOLD` | `0.2` |
| 비평가 편차 더 중시 | `BETA` | `0.7` (ALPHA=0.3으로 같이 조정) |
| 비용 절감 | `CRITIC_MODEL` | `"gpt-4o-mini"` |
| 재시도 늘리기 | `MAX_FAIL_RETRIES` | `3` |

### 노드별 긴급도 조정 (Exp08 전용)

`src/evaluators/exp_ascore_improved.py`에서 `U_DEFAULT`를 수정하거나, 노드별로 조건 분기:

```python
# 예시: 특정 노드에 더 높은 긴급도 부여
def get_urgency(node_id: str) -> float:
    urgency_map = {
        "G_RiskAudit": 2.0,   # 리스크 관련 노드는 두 배
        "F_BoardReport": 1.5,
    }
    return urgency_map.get(node_id, 1.0)

# process_node 안에서:
U = get_urgency(node.node_id)
```
