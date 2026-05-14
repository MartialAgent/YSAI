# Agent Paper — Study Q&A

---

## Q1. DAG는 무엇인가?

Directed Acyclic Graph. 노드(작업 단위)와 방향 엣지(데이터 의존성)로 구성된 단방향 비순환 그래프.

LLM 에이전트 맥락에서:
- **노드** = 하나의 AI 작업 (예: 가격 분석, ROI 계산, 광고 문구 생성)
- **엣지** = 상위 노드 출력 → 하위 노드 입력 흐름
- **비순환** = 루프 없음 → 실행 순서가 위상 정렬로 결정론적으로 결정됨

단순 체인(A→B→C)과의 차이: DAG는 병렬 분기(A→B, A→C, B+C→D)와 복합 의존성을 표현 가능.

---

## Q2. 에이전트 연구 분야 10개 — 점수·순위·DAG 포함 여부

> 점수 기준: 논문 기여 가능성(4) + 차별화 여지(3) + 현재 관심도(3), 합계 10점

| 순위 | 분야 | 점수 | DAG 포함 |
|------|------|------|---------|
| 1 | Multi-Agent Orchestration / DAG 구조 | 9.1 | ✅ 핵심 |
| 2 | LLM-as-Judge / Agent Evaluation | 8.4 | ✅ 연관 |
| 3 | Planning & Reasoning (CoT, GoT, ToT) | 8.0 | ▲ 부분 |
| 4 | Error Recovery & Resilience | 7.8 | ✅ 연관 |
| 5 | Human-in-the-Loop (HITL) | 7.5 | ✅ 연관 |
| 6 | Agent Safety & Alignment | 7.2 | ❌ |
| 7 | Memory & Context Management | 6.5 | ❌ |
| 8 | Tool Use & Function Calling | 6.0 | ❌ |
| 9 | Multi-modal Agents | 5.8 | ❌ |
| 10 | RLHF / RLAIF for Agents | 5.5 | ❌ |

DAG는 1위이면서 2·4·5위와 교차 — 단일 주제로 여러 분야를 포괄할 수 있는 구조.

---

## Q3. DAG의 주요 연구 분야 & 논문 가능성 주제

`dag_research_landscape.md` 기준 5개 분야 + 각 가능성 주제:

| 분야 | 현재 공백 | 논문 가능성 주제 |
|------|----------|----------------|
| DAG 오케스트레이션 | 중간 노드 검증 효과 미측정 | **"노드 게이팅이 파이프라인 오류 전파를 줄이는가"** (우리 핵심) |
| LLM-as-Judge | 완전성(Completeness) 미측정 | **"A-score의 S·C·D 중 어떤 성분이 실제로 유효한가"** |
| Error Propagation | 형식적 보장 없음 | "DAG 게이트 위치에 따른 오류 증폭 계수 측정" |
| HITL | 개입 시점 기준 없음 | "AMBIGUOUS 판정 임계값 자동 캘리브레이션" |
| Observability | 집합적 패턴 탐지 불가 | "A-score 히트맵으로 병목 노드 자동 식별" |

**우선순위 높은 주제:** 첫 번째 (직접 실험 가능) + 두 번째 (exp03~08 결과가 증거).

---

## Q4. DAG의 기술 핵심 (기술 표준)

| 개념 | 정의 | 표준 구현 사례 |
|------|------|--------------|
| **위상 정렬 (Topological Sort)** | 선행 노드가 항상 먼저 실행되도록 순서 결정 (Kahn's / DFS) | Apache Airflow, Prefect, Dagster |
| **Critical Path Method (CPM)** | 전체 실행 시간을 결정하는 최장 의존 경로 — 이 경로의 노드가 병목 | PERT/CPM (1950s~), Spark DAG optimizer |
| **데이터 흐름 (Dataflow) 모델** | 시간이 아닌 데이터 가용성이 실행 트리거 — 입력이 준비된 순간 실행 | TensorFlow Graph, Apache Flink |
| **멱등성 (Idempotency)** | 동일 입력 → 동일 출력 보장 — 재시도 안전성의 전제 조건 | 분산 워크플로우 공통 요구사항 |
| **체크포인팅 (Checkpointing)** | 노드 완료 시 상태 영속 저장 → 장애 시 마지막 성공 지점부터 재개 | Spark RDD lineage, Airflow task state |
| **팬아웃 / 팬인 (Fan-out / Fan-in)** | 하나의 노드가 여러 하위 노드에 분배(Fan-out) / 여러 결과를 합산(Fan-in) | Scatter-gather 패턴, MapReduce |
| **비순환 보장 (Acyclicity)** | 그래프 정의 시점에 사이클 탐지(DFS)로 무한 루프 원천 차단 | 모든 DAG 엔진의 필수 불변 조건 |

---

## Q5. DAG의 핵심 구조

### 노드 유형

| 유형 | 역할 | 특징 |
|------|------|------|
| **Source 노드** | 외부 입력을 그래프로 진입시키는 시작점 | 선행 의존성 없음, 병렬 실행 가능 |
| **Processing 노드** | 상위 노드 출력을 받아 변환·생성·판단 수행 | 의존 노드 전부 완료돼야 실행 |
| **Sink 노드** | 파이프라인 최종 출력을 내보내는 종착점 | 후속 의존성 없음 |
| **Gate 노드** | 조건 평가 후 실행 경로를 분기 | 조건부 DAG에서 동적 라우팅 담당 |

### 엣지 유형

| 유형 | 의미 |
|------|------|
| **데이터 의존성 엣지** | 상위 노드 출력이 하위 노드 입력으로 직접 전달 |
| **제어 흐름 엣지** | 데이터 전달 없이 실행 순서만 강제 (완료 신호) |

### 토폴로지 패턴

```
Linear Chain:   A → B → C
Parallel:       A → B
                A → C           (B, C 동시 실행)
Fan-in:         B → D
                C → D           (D는 B·C 모두 완료 후 실행)
Diamond:        A → B → D
                A → C → D       (Fan-out + Fan-in 조합)
```

### 실행 모델 구성 요소

| 구성 요소 | 역할 |
|----------|------|
| **Orchestrator (스케줄러)** | 위상 정렬 → 실행 순서 결정, 노드 상태 추적, 재시도·HITL 라우팅 |
| **Worker** | 개별 노드의 실제 작업 수행 (LLM 호출, 도구 실행 등) |
| **State Store** | 노드별 입출력·상태를 영속 저장 — 체크포인팅 기반 |
| **Evaluator** | 노드 출력 품질 판정 → PASS / FAIL / AMBIGUOUS 결정 |

### 그래프 수준 속성

| 속성 | 정의 | 의미 |
|------|------|------|
| **깊이 (Depth)** | 최장 경로의 노드 수 | 직렬 지연의 하한 |
| **너비 (Width)** | 동시 실행 가능한 최대 노드 수 | 병렬화 이득의 상한 |
| **Critical Path** | 전체 실행 시간을 결정하는 최장 의존 경로 | 최적화 우선 대상 |
| **팬아웃 계수** | 노드 하나가 갖는 평균 하위 엣지 수 | 오류 전파 범위와 비례 |

---

## Q6. DAG 평가의 요소들

| 요소 | 기호 | 의미 | 측정 방법 |
|------|------|------|----------|
| 유사도 | S | 동일 태스크 2회 응답 간 일치도 | 코사인 유사도 (embedding) |
| 확신도 | C | 모델 자기 평가 정확도 | 자기보고 JSON / Logprobs YES·NO |
| 편차 | D | Critic이 감지한 오류 심각도 | GPT Critic / QAG 퀴즈 / G-Eval CoT |
| 모호성 지수 | A-Score | 종합 불확실성 | α(1-S) + β×D×(1-C) |
| 일치도 | W | 3응답 간 그룹 합의 | Kendall's W 프록시 |
| 우려 키워드 | Z | 모델 자체 불확실성 표현 수 | 텍스트 키워드 카운팅 |
| 조정 신뢰도 | C_adj | Z로 감쇠된 C | C × 1/(1+ln(1+Z)) |
| 의존도 민감도 | DSS | 입력 변화 대비 출력 변화 | 섭동 후 코사인 거리 |
| 영향도 지수 | I-Factor | 수정 전파 범위 | Σ(R/(d+1)) |
| 완전성 | Completeness | 요구 조건 충족 비율 | QAG 또는 체크리스트 (미구현) |

---

## Q7. DAG 평가 관련 우리 기존 실험 기획

| Exp | 핵심 변경 | 가설 |
|-----|----------|------|
| 01 | Baseline (자율주행 그래프) | 기준선 수립 |
| 02 | Baseline (SaaS Pricing 3-노드) | 도메인 고정 비교 기준 |
| 03 | C → Logprobs YES/NO | 자기보고 C의 편향 노출 |
| 04 | D → QAG 퀴즈 3문항 | 객관적 조건 충족 검증 |
| 05 | D → G-Eval CoT + logprobs | 루브릭 기반 안정적 D |
| 06 | D → Multi-LLM 평균 (GPT·Claude·Gemini) | 동일 모델 편향 제거 |
| 07 | + DSS 진단 | 고위험 upstream 노드 식별 |
| 08 | 전면 수식 개선 (W + C_adj + Z, 7-노드) | 복잡 파이프라인 변별력 향상 |
| 09 | Vanilla vs DAG 비교 (설계 완료) | DAG 부가가치 절대 수치 증명 |

---

## Q8. 우리 실험 결과

**유효한 발견:**

- **Exp03**: Logprobs C가 자기보고 편향 노출 — A_Pricing C≈0.000 (실제 불확실) vs 자기보고 ~0.9
- **Exp04**: QAG가 C_AdCopy에서 3문항 중 2개 조건 누락 탐지 (D=0.667) — Critic 단독보다 민감
- **Exp05**: G-Eval이 가장 안정적 — 최저 노이즈, A-Score 범위 최소
- **Exp06**: A_Pricing에서 모델 간 편차 탐지 (GPT D=0.5 vs Claude·Gemini D=0.0) → 동일 모델 편향 실증
- **Exp07**: A_Pricing DSS=0.349 → 고위험 upstream 노드 — A-Score만으로는 탐지 불가
- **Exp08**: F_BoardReport(A=0.156), G_RiskAudit(A=0.113) 정확히 최고 위험 노드로 식별 — C_adj가 핵심 변별자

**실패한 탐지:**

- **Exp08 D_ConditionAudit**: 5번째 조건 의도적 누락 → A=0.028, Z=0, 판정 PASS → **침묵 실패(Silent Failure)**

---

## Q9. 잔혹한 평가와 개선점

**① 침묵 실패 — 가장 심각**
출력이 그럴듯하면 통과. 완전성(Completeness) 검증이 없어 누락이 감지 안 됨.
→ QAG 방식의 체크리스트 평가 필수.

**② Vanilla 기준선 없음**
exp01~08 전부 DAG 내부 비교. "DAG가 없는 것보다 얼마나 낫나"를 수치로 못 보임.
→ exp09가 이를 해결해야 논문 성립.

**③ C는 항상 높다 (자기보고 편향)**
모델은 JSON으로 자기 신뢰도를 물으면 거의 항상 0.8~1.0을 반환.
→ Logprobs(Exp03) 또는 C_adj(Exp08)로 보정 필요.

**④ Z 카운팅 조악함**
"note that", "assumption"이 맥락 무관하게 동일하게 처리됨.
→ 맥락별 가중치 또는 문장 수준 sentiment 분류 필요.

**⑤ 단일 도메인 — 일반화 미검증**
모든 실험이 B2B SaaS Pricing. 타 도메인에서 같은 결론이 나오는지 미검증.
→ exp10 신재용 데이터셋으로 확장 예정.

**⑥ 임계값 고정 (A=0.7)**
도메인·노드 역할과 무관하게 동일 임계값. 금융·의료 노드는 더 엄격해야 함.
→ U (긴급도 승수) 활성화 또는 도메인별 임계값 설정.

---

## Q10. Vanilla vs Others 구조로 평가 가능한 것들

| 측정 항목 | Vanilla 예측 | DAG 예측 | 측정 방법 |
|----------|------------|---------|----------|
| **A-score (사후 적용)** | 높음 (방어 없음) | 낮음 | 동일 evaluator 사후 적용 |
| **조건 완전성** | 낮음 (체크 없음) | 중간~높음 | QAG 체크리스트 |
| **오류 전파율** | 높음 | 낮음 | 상위 노드 오류 → 하위 출력 변화율 |
| **침묵 실패 빈도** | 높음 | 중간 | 의도적 결함 삽입 후 통과 여부 |
| **AMBIGUOUS 판정 수** | 0 (체계 없음) | 측정됨 | retry count |
| **출력 일관성** | 낮음 (재시도 없음) | 높음 | 동일 태스크 N회 반복 분산 |
| **비용 대비 품질** | 낮은 비용, 낮은 품질 | 높은 비용, 높은 품질 | API 호출 수 vs A-score 개선폭 |

**추가 제안 — 비교 가능한 구조 변형:**

| 구조 | 설명 |
|------|------|
| Vanilla | 단일 LLM 순차 호출, 평가 없음 |
| DAG-Baseline (exp02) | A-score 게이팅, 자동 재시도 |
| DAG-BestEval (exp05) | G-Eval D + Logprobs C |
| DAG-Improved (exp08) | Kendall's W + C_adj + Z |
| DAG-MultiJudge (exp06) | 3-모델 평균 D |

이 5-way 비교가 논문의 핵심 Figure가 될 수 있음.
