# AgentDAG Bible

**최초 작성:** 2026-05-09 | **구조 개편:** 2026-05-16

---

## 1부. 결론 요약

### 1. 연구 질문 & 기여점

#### 1-1. 핵심 질문

> DAG 중간 노드에 평가 게이트를 달면 **오류 전파율이 얼마나 줄어드는가?**  
> Partial Backpropagation이 게이트 단독 대비 **추가로 얼마나 줄이는가?**

기존 연구: "어떻게 DAG를 실행하는가" + "오류를 어떻게 탐지하는가"  
우리 추가: 게이트와 Partial Backpropagation의 오류 전파 **억제 효과를 Fault Injection 실험으로 정량화**

#### 1-2. 예상 기여점 (Contribution)

| # | 기여 | 근거 |
|---|------|------|
| C1 | DAG 중간 게이트가 오류전파율을 정량적으로 줄임을 실증 | Exp09: Vanilla vs Option1 비교 |
| C2 | Partial Backpropagation이 게이트 단독 대비 추가 억제 효과를 검증 | Exp09: Option1 vs Option2 비교 |
| C3 | 정형/비정형 태스크 타입에 따라 오류 전파 패턴이 다름을 발견 | 분리 집계 분석 |

---

## 2부. DAG 기술 개요

### 2. DAG 기술 기초

#### 2-1. DAG란

Directed Acyclic Graph. 노드(작업 단위) + 방향 엣지(데이터 의존성) + 비순환 보장.  
실행 순서는 위상 정렬(Topological Sort)로 결정론적으로 결정됨.

```
Linear:   A → B → C
Parallel: A → B, A → C          (B·C 동시 실행)
Fan-in:   B → D, C → D          (D는 B·C 완료 후 실행)
Diamond:  A → B → D, A → C → D  (Fan-out + Fan-in 조합)
```

#### 2-2. 7대 기술 표준

| 개념 | 정의 |
|------|------|
| 위상 정렬 | 선행 노드 항상 먼저 실행 (Kahn's / DFS) |
| Critical Path | 전체 실행 시간 결정하는 최장 의존 경로 |
| Dataflow 모델 | 데이터 가용성이 실행 트리거 |
| 멱등성 | 동일 입력 → 동일 출력 (재시도 안전성 전제) |
| 체크포인팅 | 노드 완료 시 상태 영속 저장 → 장애 복구 |
| Fan-out / Fan-in | 분배 → 합산 패턴 |
| 비순환 보장 | 정의 시점 DFS로 사이클 원천 차단 |

#### 2-3. 실행 모델 구성 요소

| 구성 요소 | 역할 |
|----------|------|
| Orchestrator | 위상 정렬 → 실행 순서 결정, 노드 상태 추적, 재시도·HITL 라우팅 |
| Worker | 개별 노드 작업 수행 (LLM 호출) |
| State Store | 노드별 입출력·상태 영속 저장 |
| Evaluator | 노드 출력 품질 판정 → PASS / FAIL / AMBIGUOUS |

---

### 3. 시스템 아키텍처

#### 3-1. 코드 구조

```
paper/src/
├── config.py          — 하이퍼파라미터 (게이트 임계값, 재시도 횟수 등)
├── models.py          — 데이터 모델 (NodeState, GraphState, EvaluationResult)
├── graphs.py          — 그래프 정의 (7-node SaaS Pricing)
├── evaluator.py       — 노드 출력 평가기 (PASS / FAIL / AMBIGUOUS 판정)
├── orchestrator.py    — DAG 실행, 위상 정렬, Partial Backprop
└── evaluators/        — 실험별 평가기 변형 (Exp03~08)
```

#### 3-2. 실행 흐름 (Exp09 기준)

```
Fault Injection (A_Pricing에 오류 삽입)
    ↓
Orchestrator — 위상 정렬 → 실행 순서 결정
    ↓
Worker — LLM 호출 (gpt-4o-mini)
    ↓
[Vanilla] 평가 없음 → 다음 노드로 그대로 전달
[Option1] Evaluator 판정 → FAIL 시 재시도, PASS 시 다음 노드
[Option2] Evaluator 판정 → FAIL 시 재시도, 수정 발생 시 Impact Factor 계산
              → Partial Backpropagation — 영향받는 하위 노드만 재실행
    ↓
오류전파율 측정 — 하위 노드 오류 흡수 여부 판정
```

#### 3-3. 사용 모델

| 역할 | 모델 | 이유 |
|------|------|------|
| Worker (응답 생성) | gpt-4o-mini | 비용 효율 |
| Evaluator (게이트 판정) | gpt-4o | 정확도 우선 |
| Embedding (노드 간 유사도) | text-embedding-3-small | 경량 |

#### 3-4. 실험 그래프 (7-node SaaS Pricing)

```
A_Pricing ──→ B_ROI ──→ C_AdCopy
    │              │
    │         G_MarketSize
    │
    └──→ D_ConditionAudit ──→ E_ChurnFormula
                   │
                   └──→ F_BoardReport
```

| 노드 | 타입 | 역할 |
|------|------|------|
| A_Pricing | 정형 | 3-tier 구독 가격 설계 (Pro = 2.5× Basic 제약) |
| B_ROI | 정형 | A 가격 기반 연간 ROI 계산 |
| C_AdCopy | 비정형 | B의 ROI% 인용 광고 문구 작성 |
| D_ConditionAudit | 비정형 | 계약 조건 검토 |
| E_ChurnFormula | 정형 | 이탈률 공식 계산 |
| F_BoardReport | 비정형 | 경영진 보고서 |
| G_MarketSize | 비정형 | 시장 규모 분석 |

---

## 3부. DAG 최신 기술 정보

### 4. 연구 지형도

#### 4-1. 핵심 연구 키워드 5개

| 분야 | 키워드 | 우리 연구 연결점 |
|------|--------|----------------|
| 구조 | DAG-Structured Multi-Agent Orchestration | 핵심 실험 환경 |
| 평가 | Error Propagation Measurement | 핵심 측정 지표 |
| 신뢰성 | Fault Injection & Reliability | 실험 방법론 |
| 개입 | Human-in-the-Loop (HITL) Agent Systems | AMBIGUOUS 판정 + Impact Factor |
| 시각화 | Agent Observability & Execution Tracing | 논문 Figure |

#### 4-2. 에이전트 연구 분야 순위

> 논문 기여 가능성(4) + 차별화 여지(3) + 현재 관심도(3) 기준

| 순위 | 분야 | 점수 | DAG 포함 |
|------|------|------|---------|
| 1 | Multi-Agent Orchestration / DAG 구조 | 9.1 | 핵심 |
| 2 | Error Propagation Measurement | 8.7 | 핵심 |
| 3 | LLM-as-Judge / Agent Evaluation | 8.4 | 연관 |
| 4 | Error Recovery & Resilience | 7.8 | 연관 |
| 5 | Human-in-the-Loop (HITL) | 7.5 | 연관 |

#### 4-3. 분야별 최신 연구 & 한계

**DAG 오케스트레이션**

| 논문 | 연도 | 핵심 |
|------|------|------|
| DynTaskMAS (arXiv:2503.07675) | ICAPS 2025 | DAG 자동 생성 + 비동기 병렬, 실행 21~33% 단축 |
| Scheduler-Theoretic Framework (arXiv:2604.11378) | 2026 | 형식적 스케줄링 이론 (실증 없음) |
| Why Do MAS Fail? / MAST (arXiv:2503.13657) | 2025 | 14개 실패 유형, 1,600+ 트레이스 분석 |

**한계:** 중간 노드 품질 검증 없음 / 파이프라인 전체 품질 기준 없음

**오류 전파 측정 (핵심 선행 연구)**

| 논문 | 연도 | 핵심 |
|------|------|------|
| AgentEval (arXiv:2604.23581) | 2026 | DAG 노드별 LLM Judge + 실패 분류(3단계 21유형), 루트코즈 vs 전파 실패 구분. 전체 실패의 **63%가 upstream 전파** |
| AgentProp-Bench (arXiv:2604.16706) | 2026 | 3단계 지표(S1·S2·S3)로 단계별 전파율 측정. 파라미터 주입 → 최종 오류 확률 **≈0.62** |
| MAS-FIRE (arXiv:2602.19843) | 2026 | 15개 결함 유형, 3가지 비침습 주입 방식. Of/Lf/Sf 이중 계층 지표 |
| Sherlock (arXiv:2511.00330) | 2024 | 반사실적 분석으로 취약 노드 식별, 선택적 검증기 부착. 정확도 **+18.3%** |
| COCO (arXiv:2508.13815) | 2025 | 비동기 자기모니터링 + 이종 모델 교차 검증. 평균 **+6.5%** 성능 향상 |
| Faulty Agents Resilience (arXiv:2408.00989) | ICML 2025 | 계층 구조 오류 증폭 4.4×, 독립 구조 17.2× |

**핵심 발견:**
- Sherlock: 말단 노드 > 초기 노드 > 중간 노드 순으로 오류 취약
- AgentEval: DAG 의존성 모델링만으로 실패 탐지 +22pp, 루트코즈 정확도 +34pp
- MAS-FIRE: 반복적 폐루프 설계가 선형 워크플로우 대비 결함 40%+ 무력화

**한계:** 최종 출력만 검증 / 오류 전파 범위의 형식적 보장 없음

**HITL**

| 논문 | 연도 | 핵심 |
|------|------|------|
| HULA (arXiv:2411.12924) | ICSE 2025 | 개발자 HITL 프레임워크, 플랜 승인률 82% |
| GitHub Copilot Workspace | 2025 | 멀티파일 변경 필수 승인 게이트 |

**한계:** 개입 시점 기준 없음 / 재실행 범위 결정이 ad-hoc

#### 4-4. 연구 공백 지도 (Gap Map)

| 현재 연구 집중 영역 | 공백 (우리가 파고들 곳) |
|--------------------|----------------------|
| DAG 실행 스케줄링 | 게이트 유무·백프롭 유무가 오류전파율에 미치는 단계적 효과 |
| 오류 전파 측정 (단일 파이프라인) | DAG 중간 게이트가 전파율을 구조적으로 줄이는지 실증 |
| 단일 실행 트레이싱 | 정형/비정형 태스크 타입에 따른 전파 패턴 차이 |
| HITL 개입 메커니즘 | 게이트 + 백프롭 조합의 비용 대비 전파 억제 효율 |

---

### 5. DAG & 오류전파율 집중 연구 분석

> 실험 설계의 직접 근거가 되는 선행 연구. 측정 방식·주입 방법·결과 지표를 상세히 정리한다.

#### AgentEval (arXiv:2604.23581) — 2026

**핵심 아이디어:** 에이전트 실행을 평가 DAG로 형식화하고, 각 노드에 타입별 품질 지표 + LLM Judge 부착.

**오류 분류 방식:**
- 루트코즈 실패: 노드 자체에서 발생한 오류 (36.8%)
- 전파 실패: upstream 오류가 흘러 내려온 것 (63.2%)
- 평균 전파 체인 길이: 2.1 노드

**주요 지표:**
```
FDRec (Failure Detection Recall) = 탐지된 실패 / 전체 실패
RCA (Root Cause Accuracy) = 올바르게 귀속된 루트코즈 / 전체 루트코즈
```

**실험 결과:**
- DAG 의존성 모델링 단독: FDRec +22pp, RCA +34pp (동일 Judge 기준)
- E2E 평가 대비 2.17× 높은 실패 탐지 재현율 (0.89 vs 0.41)
- 인간 전문가 합의 κ = 0.84

**우리 실험 시사점:** 루트코즈 vs 전파 실패를 구분하면 게이트의 효과(전파 억제)를 직접 측정 가능.

---

#### AgentProp-Bench (arXiv:2604.16706) — 2026

**핵심 아이디어:** 파라미터 수준 fault injection 후 3단계 지표로 전파율을 단계별 분해.

**측정 방식:**
```
S1 = 1 [주입 적용됨]
S2 = 1 [주입 효과 발생 — 하위 실행에 observable 변화]
S3 = 1 [최종 출력 오류]

전파율     = P[S3=1 | S1=1]   ≈ 0.62 (human-calibrated, 범위 0.46~0.73)
hop rate   = P[S2=1|S1=1],  P[S3=1|S2=1]
거절률     = 1 - P[S1=1]     (주입 자체를 막은 비율)
회복률     = 1 - P[S3=1|S2=1] (효과 발생 후 올바른 답 생성 비율)
```

**핵심 발견:**
- 거절률과 회복률은 독립 능력 (Spearman ρ=0.126, p=0.747) — 모델이 두 차원에서 따로 변함
- 전파율은 모델별 편차 큼 (0.43 ~ 0.97)

**우리 실험 시사점:** S1→S3 단계 추적으로 "어느 단계에서 게이트가 개입했는가"를 정량화 가능.

---

#### MAS-FIRE (arXiv:2602.19843) — 2026

**핵심 아이디어:** 15개 결함 유형 × 3가지 비침습 주입 방식으로 MAS 강건성 체계적 평가.

**주입 방식:**
- 프롬프트 수정 (Prompt Modification)
- 응답 재작성 (Response Rewriting)
- 메시지 라우팅 조작 (Message Routing Manipulation)

**이중 계층 지표:**
```
시스템 수준:
  전체 태스크 성공률 (성능 하락폭)

프로세스 수준:
  Of = 결함 인식 후 방어 행동 유발 비율 (낮으면 침묵 전파)
  Lf = 지역 복구 성공률
  Sf = 지역 복구 → 전역 태스크 성공 비율
  Lf - Sf 갭 = 지역 복구가 전역 실패로 이어지는 잔류 효과
```

**핵심 발견:**
- 반복적 폐루프(iterative closed-loop) 설계: 선형 대비 결함 40%+ 무력화
- 강한 모델이 항상 강건하지 않음 — 아키텍처 토폴로지가 동등하게 중요

**우리 실험 시사점:** Option2(백프롭)의 "지역 복구 → 전역 성공" 효과를 Lf/Sf 차이로 보완 측정 가능.

---

#### Sherlock (arXiv:2511.00330) — 2024

**핵심 아이디어:** 반사실적 분석(counterfactual analysis)으로 취약 노드 식별 → 선택적 검증기 부착.

**Fault Injection 방법:** 100+ 그래프 × 15K+ 실행 트레이스

**노드 위치별 취약성 발견:**
```
말단 노드 > 초기 노드 > 중간 노드  (취약성 순)
이유: 말단 노드는 복구 경로 없음
     초기 노드는 오류가 전체에 파급
     중간 노드는 하위 노드가 보정 가능
```

**Fan-in 도수:** 상관관계 있음 (Fan-in 높을수록 오류 증폭·전파 가능성 높음)  
**Fan-out 도수:** 상관관계 거의 없음

**성능:** 비검증 baseline 대비 정확도 +18.3%, 실행시간 최대 48.7% 단축

**우리 실험 시사점:** A_Pricing(초기 노드)이 주입 위치로 적합함을 이론적으로 뒷받침. Fan-in 노드(D_ConditionAudit, F_BoardReport)가 전파 취약점.

---

#### 선행 연구 종합 — 우리 실험 설계 원칙

| 설계 결정 | 근거 논문 | 구체 수치 |
|----------|----------|---------|
| 루트 노드(A_Pricing)에 주입 | Sherlock (초기 노드 = 전체 파급) | 15K+ 트레이스 실증 |
| 루트코즈 vs 전파 실패 구분 | AgentEval | 실패의 63%가 전파 실패 |
| 단계별 전파율(S1→S3) 측정 | AgentProp-Bench | 기준값 ≈ 0.62 |
| 정형/비정형 분리 집계 | MAS-FIRE (도메인별 결함 반응 차이) | 아키텍처별 편차 40%+ |
| Fan-in 노드 중점 관찰 | Sherlock | Fan-in ↑ → 오류 증폭 |

---

### 6. 2026 AI Agent 생태계

#### 6-1. 프로토콜 계층

| 프로토콜 | 방향 | 2026 상태 |
|---------|------|----------|
| MCP | Agent → Tools/Data | 월 9,700만 SDK 다운로드, 서버 18,000+ |
| A2A | Agent ↔ Agent | v1.0 GA, 150+ 조직 지원 |
| LangGraph | 프레임워크 내부 오케스트레이션 | 프로덕션 표준 (Supervisor 패턴) |

#### 6-2. AgentDAG ↔ 2026 생태계 갭

| 항목 | 현재 상태 | 갭 |
|------|----------|-----|
| LangGraph | 사용 중 | `interrupt()` / `Command(resume=...)` 미적용 |
| 체크포인터 | 자체 구현 | `AsyncPostgresSaver` 교체 고려 |
| MCP | 미적용 | Evaluator를 MCP 서버로 노출 시 외부 재사용 가능 |
| HITL | 자체 구현 | LangGraph `interrupt()` 패턴으로 표준화 가능 |
| A2A | 미적용 | 단일 배포 → 현재 불필요 |

---

## 4부. 실험 옵션

### 7. 회의 결론 항목 (2026-05-16)

> 아래 4가지를 오늘 회의에서 확정한다.

#### 7-1. 실험형식 — Vanilla vs Option1 vs Option2

| | **Option A** | **Option B** | **Option C** |
|---|---|---|---|
| **Vanilla** | 게이트 X, 백프롭 X | 게이트 X, 백프롭 X | 게이트 X, 백프롭 X |
| **Option1** | 게이트 O, 백프롭 X | 단순 게이트 O, 백프롭 X | 게이트 O, 백프롭 X |
| **Option2** | 게이트 O, 백프롭 O | 엄격 게이트 O, 백프롭 X | 게이트 O, 적응형 재실행 O |
| **비교 축** | 게이트 유무 × 백프롭 유무 | 게이트 엄격도 (판정 기준 강약) | 재실행 방식 (고정 vs 적응형) |
| 논문 기여도 | ★★★★★ | ★★★☆☆ | ★★★★☆ |
| 실험 실현성 | ★★★★★ | ★★★☆☆ | ★★★★☆ |
| 결과 설득력 | ★★★★★ | ★★★☆☆ | ★★★★☆ |
| 코드 재활용 | ★★★★☆ | ★★★★★ | ★★★★★ |

| **종합** | **19/20** | **13/20** | **17/20** |

**권장: Option A** — 게이트 유무·백프롭 유무를 단계적으로 분리해 기여점 C1·C2를 직접 증명. AgentProp-Bench의 단계별 전파율(S1→S3)과 직접 대응.

**→ 회의 결정:** \_\_\_\_\_\_\_\_\_\_

---

#### 7-2. 기본 형태

단방향 DAG — 이미 확정. 7-node SaaS Pricing 그래프 유지.

---

#### 7-3. 오류전파율 측정 방식 옵션

최신 논문(5절)을 바탕으로 4가지 방식을 비교한다.

**방식 A — 구조적 전파율 (Structural EPR)**

```
EPR = 오류 흡수 하위 노드 수 / 전체 하위 노드 수
```

- **오류 주입:** 루트 노드(A_Pricing) 고정
- **오류 판정:** 노드 출력의 정형/비정형 기준 위반 여부
- **출처:** 자체 설계 (Vanilla vs Gate 비교에 최적)
- 장점: 단순, DAG 구조 직접 반영, 구현 비용 낮음
- 단점: 전파 경로 추적 없음, 루트코즈 vs 전파 실패 구분 불가

**방식 B — 단계적 조건부 전파율 (Stage-Conditional EPR)**

```
S1 = 주입 적용 여부
S2 = 주입 효과 발생 여부 (하위 노드 출력 변화)
S3 = 최종 출력 오류 여부

전파율 = P[S3=1 | S1=1]   (주입→최종오류 확률)
hop-conditional = P[S2=1|S1=1], P[S3=1|S2=1]
```

- **출처:** AgentProp-Bench (arXiv:2604.16706)
- 실증값: 파라미터 주입 → 최종 오류 확률 ≈ 0.62 (0.46~0.73)
- 장점: 전파 경로 단계별 추적, 거절률·회복률 분리 측정
- 단점: 다분기 DAG에서 S2 정의 복잡, 구현 비용 높음

**방식 C — 루트코즈 분리 전파율 (Root-Cause Attribution EPR)**

```
전파율 = 전파된 실패 수 / 전체 실패 수
루트코즈 실패 = 노드 자체 오류
전파 실패 = upstream 오류로 인한 downstream 오류
```

- **출처:** AgentEval (arXiv:2604.23581)
- 실증값: 전체 실패의 63%가 upstream 전파
- 장점: DAG 의존성 모델 직접 활용, 원인 귀속 가능
- 단점: LLM Judge 추가 필요, greedy 휴리스틱 의존

**방식 D — 이중 계층 강건성 지표 (Dual-Layer Robustness)**

```
Of (발생률) = 결함 인식 후 방어 행동 유발 비율
Lf (지역 성공률) = 지역 복구 성공 비율
Sf (전역 성공률) = 지역 복구 → 최종 태스크 성공 비율
```

- **출처:** MAS-FIRE (arXiv:2602.19843)
- 장점: 회복 능력까지 측정, 가장 포괄적
- 단점: 구현 복잡, 3개 지표 동시 설계 필요

**방식별 비교**

| | 방식 A | 방식 B | 방식 C | 방식 D |
|--|--------|--------|--------|--------|
| 논문 정합성 | ★★★☆☆ | ★★★★★ | ★★★★★ | ★★★★☆ |
| 구현 용이성 | ★★★★★ | ★★★☆☆ | ★★★☆☆ | ★★☆☆☆ |
| DAG 구조 활용 | ★★★★☆ | ★★★☆☆ | ★★★★★ | ★★★☆☆ |
| 전파 경로 추적 | ★★☆☆☆ | ★★★★☆ | ★★★★★ | ★★★☆☆ |
| **종합** | **14/20** | **15/20** | **17/20** | **11/20** |

**권장: 방식 C** (루트코즈 분리) — AgentEval 선행 연구와 직접 비교 가능, DAG 의존성을 가장 잘 활용.  
**차선: 방식 A + B 병행** — 구현이 단순하면서 단계별 추적까지 가능. 논문 Figure 두 가지 확보.

**→ 회의 결정:** \_\_\_\_\_\_\_\_\_\_

---

#### 7-4. 평가항목 — 정형/비정형

| | **정형만** | **혼합 (분리 집계)** |
|---|---|---|
| 대상 노드 | A_Pricing, B_ROI, E_ChurnFormula | 7-node 전체 |
| 오류 판정 | 수치 위반 (명확) | 정형: 수치 위반 / 비정형: LLM Judge |
| 논문 기여도 | ★★★☆☆ | ★★★★★ |
| 실험 실현성 | ★★★★★ | ★★★★☆ |
| 일반화 주장 | 약함 | 강함 |
| 추가 설계 부담 | 없음 | 비정형 판정 기준 1회 설계 필요 |
| **종합** | **13/20** | **18/20** |

**권장: 혼합** — 기여점 C3(정형/비정형 전파 패턴 차이) 추가 확보. SaaS 그래프 그대로 사용.

**→ 회의 결정:** \_\_\_\_\_\_\_\_\_\_

---

## 다음 단계 (Phase 2 체크리스트)

```
[회의] 실험형식 확정 — Option A / B / C
[회의] 오류전파율 측정 방식 확정 — 방식 A / B / C / D
[회의] 평가항목(정형/비정형) 확정
[확정] 기본 형태 — 단방향 DAG (7-node SaaS 그래프)

[미완] Fault injection 레이어 구현 (A_Pricing 오류 주입)
[미완] 오류 판정 기준 코드화 (정형: 수치 위반 / 비정형: LLM Judge)
[미완] Exp09 실행 — Vanilla vs Option1 vs Option2
[미완] 결과 시각화 — 오류전파율 비교 Figure
[예정] Exp10 — 신재용 데이터셋으로 도메인 일반화 검증
```

---

## 참고 논문

- [AgentEval: DAG EPR Tracking (arXiv:2604.23581)](https://arxiv.org/abs/2604.23581)
- [AgentProp-Bench: Stage-level Propagation (arXiv:2604.16706)](https://arxiv.org/abs/2604.16706)
- [MAS-FIRE: Fault Injection & Robustness (arXiv:2602.19843)](https://arxiv.org/abs/2602.19843)
- [COCO: Continuous Oversight (arXiv:2508.13815)](https://arxiv.org/abs/2508.13815)
- [Sherlock: Reliable Agentic Workflow (arXiv:2511.00330)](https://arxiv.org/abs/2511.00330)
- [Faulty Agents Resilience (arXiv:2408.00989)](https://arxiv.org/abs/2408.00989)
- [Why Do MAS Fail? / MAST (arXiv:2503.13657)](https://arxiv.org/abs/2503.13657)
- [DynTaskMAS (arXiv:2503.07675)](https://arxiv.org/abs/2503.07675)
- [HULA (arXiv:2411.12924)](https://arxiv.org/abs/2411.12924)
