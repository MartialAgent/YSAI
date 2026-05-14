# Technical Product Requirements Document (PRD)

## 🎯 1. 프로젝트 배경 및 목적 (Context & Background)

### 1.1 배경 (The "Why")
- **에이전틱 워크플로우의 확산**: 단순 답변을 넘어 복잡한 단계별 추론과 도구 호출(Tool use)을 수행하는 에이전트 시스템이 증가하고 있습니다.
- **신뢰성 결여 (Reliability Gap)**: LLM의 환각(Hallucination) 및 자기 확신 편향(Overconfidence bias)으로 인해 중간 단계에서 발생한 미세한 오류가 전체 워크플로우(CASI: Cascade Error)로 전파되어 치명적인 결과 초래.
- **비효율적 복구 정책**: 기존 시스템은 중간 노드 오류 시 전체 그래프를 처음부터 다시 실행(Full Re-run)하여 API 비용과 지연 시간(Latency)이 기하급수적으로 증가함.

### 1.2 목적 (The "Goals")
1. **Pass/Fail/Ambiguous(PFA) 3단계 상태 판정 레이어**를 도입하여 에이전트 출력의 신뢰성 검증 자동화.
2. **부분 소급 수정 (Partial Back-propagation)** 알고리즘을 통해 오류 발생 지점의 영향력(Impact)이 미치는 하위 노드만 선택적 재실행하여 운영 효율 극대화.
3. **Human-in-the-loop(HITL)** 구조를 통해 "모호함(Ambiguous)" 상태를 전략적으로 관리하고 사용자 개입 시점을 최적화.

### 1.3 비목표 (Non-Goals)
- 실시간 스트리밍(Streaming) 응답 처리.
- 100개 이상의 노드를 가진 대규모 그래프의 분산 처리(MVP 범위 제외).

### 1.4 주요 용어 (Glossary)
- **$A$-Score (Ambiguity Score)**: 다수 에이전트의 교차 검증을 통해 산출된 모호함 지수.
- **$I$-Factor (Impact Factor)**: 데이터 수정 시 하위 노드에 미치는 누적 영향도 지수.
- **PFA**: 상태 판정 분류 (Pass / Fail / Ambiguous).

---

## 👥 2. 페르소나 및 사용자 시나리오 (Persona & Use Cases)

| 페르소나 | 주요 니즈 (Pain Points) | 기대 효과 |
| :--- | :--- | :--- |
| **AI 엔지니어** | 워크플로우 중간의 에러 전파 제어 및 디버깅 어려움 | 노드별 신뢰도 가시화 및 정밀한 부분 재실행 제어 |
| **서비스 운영자** | 과도한 API 호출 비용 및 예측 불가능한 응답 품질 | 실패 구간 선별 재실행을 통한 비용 효율화 및 품질 안정 |
| **최종 사용자** | AI 결과에 대한 막연한 불신 | '검토 필요(Ambiguous)' 알림을 통한 신뢰할 수 있는 협업 경험 |

---

## 🛠️ 3. 핵심 기능 요구사항 (Functional Requirements)

### 3.1 P0 (Must-Have): 필수 구현 기능
- **[PFA 판정 엔진]**: Multi-Agent 합의 알고리즘 기반의 `A-Score` 계산 및 상태 라우팅 로직.
- **[Partial Back-prop 스케줄러]**: 수정 노드 기준 하위 의존성 그래프 탐색 및 `I-Factor` 기반 재실행 큐 생성.
- **[상태 관리 저장소]**: 각 노드의 Input/Output/Confidence/Metadata를 JSON 형태로 보존하는 State Manager.

### 3.2 P1 (Should-Have): 중요 기능
- **[Human-Interrupt 엔드포인트]**: Ambiguous 상태 노드에서 실행을 일시 중단하고 외부 피드백을 수락하는 API.
- **[에이전틱 가중치 설정]**: 에이전트별 전문성 점수를 부여하여 `A-Score` 계산 시 가중합 적용.

### 3.3 P2 (Could-Have): 선별적 기능
- **[Mnemosyne 시각화 연동]**: 실시간 에이전트 상태를 캐릭터 애니메이션 및 그래프 UI로 표현.
- **[비용 최적화 대시보드]**: Full Re-run 대비 절감된 토큰 수 및 시간의 시각화 보고서.

---

## 📐 4. 핵심 산식 및 데이터 모델 (Technical Logic)

### 4.1 모호함 판정 지수 (Ambiguity Score: A)
다수 에이전트의 교차 검증을 통해 산출됩니다. (모델 확신도 $C$가 0에 수렴할 때 발산하는 수학적 오류를 방지하기 위해 감쇄 모델 적용)
$$ A = \alpha(1 - S) + \beta \cdot D \cdot (1 - C) $$
- **S (Similarity)**: 동일 프롬프트로 2회 생성한 Worker 응답 간의 벡터 코사인 유사도 (Self-consistency 검증 방식).
- **C (Confidence)**: 생성 모델의 Logprobs 또는 자체 반성 시의 확신도 평가 스코어 (0~1).
- **D (Deviation)**: 비판(Critic) 에이전트가 탐지한 논리적 결함 및 의견 분산 정도.
- **$\alpha, \beta$**: 환경 설정에 따른 조정 가중치 계수.

### 4.2 소급 수정 영향도 (Impact Factor: I)
DAG 특성상 하나의 하위 노드가 여러 경로로 수정 영향을 받을 수 있으므로(Fan-in), 누적 영향도를 계산합니다.
$$ I_{total}(n) = \sum_{path} \left( \frac{R_{path}}{d_{path} + 1} \right) $$
- **R (Reliance)**: 하위 노드가 해당 경로의 상위 데이터를 참조하는 의존 강도 (0~1).
- **d (Distance)**: 수정 원본 노드로부터 타겟 노드까지의 엣지 거리.
- **Rule**: $I_{total} > \tau$ (임계값)인 노드 세트 $N_{re-run}$을 선별하여 재실행 스케줄링.

---

## 📈 5. 성공 지표 (Success Metrics)

1. **신뢰성 강화**: 인간 검토 점수 대비 PFA 분류 일치율(Accuracy) 85% 이상.
2. **비용 효율성 달성 (Break-even Point 분석)**: 
   - PFA 판정(Worker 다중생성, Critic, Consensus)으로 인한 오버헤드 비용 대비, Full Re-run 방지를 통해 얻는 절감 효과가 더 큰 손익분기점 돌파.
   - 목표: 오버헤드를 포함한 **총 소모 토큰량이 기존 전체 그래프 재실행 시뮬레이션 대비 40% 이상 절감**.
3. **검토 효율성**: 전체 노드 중 인간 개입이 필요한 비율(Ambiguous 표출)을 10% 미만으로 유지.

---

## ⚠️ 6. 리스크 및 제약 사항 (Risks & Constraints)

- **평가 에이전트 비용**: 교차 검증을 위해 추가 에이전트를 호출하는 비용이 발생하므로, 중요도가 낮은 노드는 평가 단계를 생략하는 정책 필요.
- **확신도 편향**: 모든 에이전트가 동일하게 틀린 답을 내놓는 경우(Majority False) `A-Score`가 낮게 나올 수 있음 -> 에이전트 다양성(Diversity) 확보 전략 필요.
- **그래프 복잡도**: 순환 구조가 없는 DAG임에도 불구하고, 노드 수 50개 이상의 복잡한 그래프에서의 영향도 계산 오버헤드 주의.

---

## 📅 7. 로드맵 (Execution Plan)

1. **Phase 1 (Core)**: PFA 판정 엔진 및 기초 DAG 오케스트레이터 개발 (`spec_evaluation_engine.md`)
2. **Phase 2 (Optimization)**: Partial Back-propagation 알고리즘 구현 및 성능 벤치마크 (`spec_partial_backprop.md`)
3. **Phase 3 (Integration)**: HITL 인터페이스 및 UI 시각화 통합 (`spec_integration_ui.md`)

---

## 🛠️ 8. 기술 개발 명세 (Technical Specifications)

### 8.1 데이터 모델 및 스키마 (Data Model)
```typescript
interface NodeState {
  node_id: string;               // 노드 고유 ID
  input_data: any;               // 상위 노드로부터 수신한 데이터
  output_data: any;              // 에이전트 실행 결과
  status: 'IDLE' | 'RUNNING' | 'PASS' | 'FAIL' | 'AMBIGUOUS';
  evaluation: {
    similarity_score: number;    // 유사도 (S)
    confidence_score: number;    // 확신도 (C)
    deviation_score: number;     // 편차 (D)
    ambiguity_index: number;     // A-Score 산출값
  };
}
```

### 8.2 핵심 컴포넌트
1. **Evaluator Service**: $A$-Score 산출 및 상태 라우팅.
2. **Impact Analyzer**: 수정 발생 시 $I$-Factor 계산 및 재실행 큐 생성.

---

## 🧠 9. LLM 모델링 및 오케스트레이션 전략 (LLM Strategy)

| 역할 (Role) | 추천 모델 | 비고 |
| :--- | :--- | :--- |
| **Worker (생성)** | **Claude 3.5 Sonnet** | 정교한 지시 이행 및 복잡한 구조 생성 |
| **Critic (비판)** | **GPT-4o** | 논리적 오류 탐지 및 교차 검증 |
| **Consensus (합의)**| **GPT-4o-mini** | 경제적인 데이터 요약 및 수치화 |

---

## 🚀 10. 초기 MVP 기술 스펙 (Initial Implementation Spec)

### 10.1 OpenAI API 기반 구성
- **모델**: `gpt-4o` (판정용), `gpt-4o-mini` (생성용)
- **임베딩**: `text-embedding-3-small` (유사도 S 계산)

### 10.2 PFA 판정 및 FAIL 에스컬레이션 루프
1. **[Generate]**: Worker가 동일 지시로 2방향 답변 생성(S 산출용) 및 모델 확신도(C) 자체 평가.
2. **[Critique]**: Critic이 답변의 허점 지적 및 편차(D) 도출.
3. **[Consensus]**: $A = \alpha(1-S) + \beta \cdot D \cdot (1-C)$ 수식 기반 AMBIGUOUS 판별.
4. **[Retry & Escalate]**: 명확한 에러로 판정 시 상태를 `FAIL` 처리 및 최대 N회 자동 재시도 돌입. 재시도 실패 시 `AMBIGUOUS`로 격상(Escalation) 처리.

---

## 🧪 11. 테스트 작업 및 평가 방식 (Test Scenarios & Evaluation)

### 11.1 테스트 태스크: [2026 자율주행 시장 전략 수립]
- **노드 A (Trend)**: 2026년 주요 트렌드 (미래 시점 환각 유도)
- **노드 B (Model)**: 수익 모델 설계 (의존성 R=0.9)
- **노드 C (Copy)**: 마케팅 카피 생성 (의존성 R=0.4)

### 11.2 평가 방식
1. **Reliability**: Human 검토 점수 대비 PFA 분류 일치율 (Target: 85%+)
2. **Efficiency**: Full Re-run 대비 절감된 토큰 사용량 (Target: 40%+)

---

## 📦 12. 컴포넌트별 상세 스펙 (Detailed Component Spec)

### 12.1 Evaluation Engine (판정 엔진)
- **역할**: 에이전트 응답 분석 및 상태(PASS/FAIL/AMBIGUOUS) 라우팅.
- **주요 입력**: Worker 응답 2개(Self-consistency용), Critic 피드백, 모델 확신도(C).
- **로직**:
  - `text-embedding-3-small`을 이용해 Worker 답변 간 코사인 유사도(S) 계산.
  - Critic 피드백을 수치화하여 편차(D) 반영.
  - $A = \alpha(1-S) + \beta \cdot D \cdot (1-C)$ 계산 (Threshold: 0.7 초과 시 AMBIGUOUS).
  - 명백한 `FAIL`의 경우, 피드백을 반영하여 최대 2회 Retry. 연속 실패 시 강제로 `AMBIGUOUS` 승격.

### 12.2 DAG Orchestrator (오케스트레이터)
- **역할**: 그래프 실행 제어 및 비동기 노드 관리.
- **기능**:
  - `Topological Sort`를 통한 노드 실행 우선순위 결정.
  - `AMBIGUOUS` 발생 시 해당 노드 및 하위 브랜치 실행 `PAUSE`, UI 인터럽트 대기.
  - 사용자 승인 완료 시 노드 상태를 PASS로 변경 후 이웃 노드 스케줄링 재개.

### 12.3 Partial Back-prop Analyzer (영향도 분석기)
- **역할**: 다중 경로 의존성을 반영한 비용 최적화 재실행 범위 산점.
- **로직**:
  - 수정 노드로부터 타겟 노드까지 생성된 모든 경로를 탐색하여 누적 영향도 $I_{total} = \Sigma(R/(d+1))$ 계산.
  - $I_{total}$ 누적값이 임계값(0.4)을 초과하는 노드들만 재실행 큐에 삽입.
  - 임계값 미만인 노드들은 기존에 캐싱된 `output_data`를 최종 상태로 확정.

### 12.4 State Persistence Layer (상태 저장소)
- **역할**: 워크플로우 전 과정의 데이터 영속성 보장.
- **구조**:
  - `history.json`: 각 노드의 실행 이력, $A$-Score, 토큰 사용량 저장.
  - `graph_state.json`: 현재 활성화된 노드 정보 및 전체 그래프 진행률 저장.
  - **Recoverability**: 프로세스 종료 후 재시작 시 `graph_state.json`을 읽어 마지막 중단 시점부터 자동 복구.

---

## 📈 13. 실험 이력 및 결과 누적 기록 (Experiment Logs)

본 섹션은 시스템 로직이나 프롬프트를 변경하면서 진행한 실험의 설정 값과 측정된 성과 수치를 누적 기록하는 공간입니다. 새로운 실험이 진행될 때마다 기존 데이터 아래에 추가됩니다.

### [Exp 01] 초기 MVP 검증 - 자율주행 시장 분석 (2026.03.30)
- **목적**: 기초적인 DAG 워크플로우 통과 및 A-Score 수식 작동 확인.
- **설정 값 (Config)**: 
  - `Model`: gpt-4o-mini (Worker), gpt-4o (Critic)
  - $\alpha=0.5, \beta=0.5$, 임계값 $A_{Threshold}=0.7, I_{Threshold}=0.4$
- **수행 태스크**: 2026 자율주행 시장 트렌드 분석 $\rightarrow$ 수익 모델 $\rightarrow$ 카피 작성
- **실험 결과 (KPI)**: 
  - **Node A (Trend)**: $S=0.959, C=0.80, D=0.30 \rightarrow A=0.051$ (PASS)
  - **Node B (Model)**: $S=0.958, C=0.90, D=0.20 \rightarrow A=0.031$ (PASS)
  - **Node C (Copy)**: $S=0.987, C=0.90, D=0.20 \rightarrow A=0.016$ (PASS)
- **인사이트 및 넥스트 스텝**: 
  - 수식($A$)은 정상 작동하나, `gpt-4o-mini` 모델의 태생적 일관성이 너무 높아 변별력 한계 존재.
  - 후속 실험에서는 $\beta$ (비판 가중치)를 올리거나, 고의로 모호한 논쟁적 프롬프트를 주입하여 `AMBIGUOUS` 에스컬레이션 동작을 검증할 것.

### [Exp 02] 복합 제약 조건 검증 - B2B SaaS 프라이싱 전략 (2026.03.30)
- **목적**: математическая(수학적) 제약 조건 부여 시 시스템의 에러 차단 및 자가 수정(Self-Correction) 여부 확인.
- **설정 값 (Config)**: Exp 01과 동일 (`main_exp02.py` 사용)
- **수행 태스크**: 2.5배수 가격 제약이 있는 3 Tier 프라이싱 $\rightarrow$ 연간 ROI 수식 계산 $\rightarrow$ 수치 연동 광고 카피
- **실험 결과 (KPI)**: 
  - **Node A (Pricing)**: $S=0.939, C=0.80, D=0.20 \rightarrow A=0.050$ (PASS)
  - **Node B (ROI)**: $S=0.988, C=1.00, D=0.00 \rightarrow A=0.005$ (PASS) 
  - **Node C (AdCopy)**: $S=0.952, C=0.80, D=0.10 \rightarrow A=0.033$ (PASS)
- **인사이트 및 넥스트 스텝**:
  - `gpt-4o-mini`는 다항 제약 조건과 수식 연산(ROI 수익률)을 최초 시도에 완벽히 해결(`FAIL` 미발생). 명확한 수학 모델일수록 확신도(C=1.0)가 상승하여 A-Score가 0에 수렴함 입증.
  - 노드 A에서 비판 에이전트(Critic)가 숫자 계산 관련 환각을 일으켰으나, A-Score 공식이 이를 편차(D)로 흡수하여 무고한 `FAIL` 처리를 막아냄(안전망 효과).
  - Worker 모델이 너무 똑똑하여 오류가 발생하지 않으므로, 다음 실험에서는 강제로 `FAIL`과 `AMBIGUOUS`를 발생시키기 위해 시스템 임계값 조정($A_{Threshold}$ 하향 및 $\beta$ 상향)과 다중 정보 충돌 프롬프트 구상이 반드시 필요.
