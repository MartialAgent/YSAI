# AI Study Loop — Claude Code 학습 시스템

이 디렉토리는 **AI/ML 무한 학습 루프 시스템**이다.
사용자가 AI/ML 핵심 지식을 체계적으로 학습할 수 있도록, Claude Code가 로컬 학습 자료를 기반으로 대화·출제·피드백을 무한 반복하는 자율 학습 루프를 구현한다.

`/study`, `/loop`, `/memo`, `/finish` 스킬로 진입하면 아래 지침에 따라 동작한다.

---

## 1. 의도와 배경

### 왜 만들었는가
- 이론서는 있지만 **"대화하며 확인받는"** 학습 파트너가 없다.
- 온라인 강의는 단방향이며, **진도 맞춤 피드백**이 없다.
- Claude Code는 로컬 파일을 읽고 스크립트를 실행하며 대화할 수 있어, **개인화 학습 루프** 구현에 최적이다.

### 핵심 가치
- **로컬 기반**: 인터넷 없이도 MD 파일만으로 학습 가능 (LLM API는 선택적)
- **약점 우선 반복**: 오답률 높은 토픽을 다음 세션에 자동 재출제
- **무한 루프**: `/loop` 진입 후 사용자가 "그만"이라고 할 때까지 끊김 없이 지속
- **개인 진도 관리**: `progress.json`에 학습 이력 누적

### Out of Scope
- 웹 UI / 대시보드 / 다중 사용자 / 클라우드 동기화
- 자동 MD 파일 생성 (학습 자료는 사람이 직접 작성)

---

## 2. 리포지토리 구조

```
AgentStudy/
├── 00.memo/                  — 일자별 학습 메모 (/memo 로 누적)
├── 01.basic_study/           — 핵심 학습 모듈 6개 + 진도 관리 시스템
├── 02.codebase/              — 실습 코드베이스 (강의/오픈소스 레퍼런스)
│   ├── 01.python/            — 패스트캠퍼스 파이썬/데이터분석 (11개 Part)
│   ├── 02.agent-park/        — 패스트캠퍼스 AI Agent (공원나연, LangGraph Part 1~3)
│   ├── 03.RAG-park/          — 패스트캠퍼스 GraphRAG (공원나연, Neo4j 기반)
│   └── 04.modern-agent/      — (예약, 비어 있음)
├── 03.agent-SOTA/            — 2026 최신 트렌드 (Exa+Context7 검증판)
├── 04.agent-10papers/        — (예약, 향후 top10 논문 코드/요약)
├── 05.seminar_project/       — AgentDAG 연구 자료 (논문/실험/PRD)
├── .claude/commands/         — study, loop, memo, finish 스킬 정의
└── CLAUDE.md                 — (이 파일) 학습 시스템 단일 지침
```

---

## 3. 학습 모듈 (`01.basic_study/`)

각 모듈은 독립된 MD 파일로 관리된다. 번호 순서는 권장 학습 순서이지만, 사용자가 임의 선택 가능.

| 파일 | 모듈 키 | 도메인 | 핵심 주제 |
|------|--------|--------|----------|
| `01_prob_stats.md` | `prob_stats` | 확률통계 | 확률분포, 기댓값, 베이즈 정리, MLE, 정보이론 |
| `02_linear_algebra.md` | `linear_algebra` | 선형대수 | 벡터/행렬 연산, 고유값, SVD, PCA, 차원축소 |
| `03_python_syntax.md` | `python_syntax` | 파이썬 문법 | 자료구조, 함수형, OOP, NumPy/Pandas 패턴 |
| `04_nlp.md` | `nlp` | NLP | 토크나이저, 임베딩, Attention, 전처리 파이프라인 |
| `05_llm.md` | `llm` | LLM | Transformer, 파인튜닝, RAG, 프롬프트 엔지니어링 |
| `06_agent.md` | `agent` | 에이전트 | ReAct, Tool Use, 메모리, 멀티에이전트 오케스트레이션 |

### 권장 학습 순서
1. **확률통계 → 선형대수**: 수학 기초 (수식 + NumPy 검증)
2. **파이썬 문법**: 코딩 도구 다지기 (스니펫 동작 예측 + 실행)
3. **NLP**: HuggingFace/NLTK 실습으로 토크나이저·임베딩 체화
4. **LLM**: Transformer 아키텍처 + Anthropic API 실습
5. **에이전트**: ReAct → Tool Use → 멀티에이전트 (`03.agent-SOTA/` 함께 참조)

---

## 4. 참조 자료 (`02.~05.`)

| 폴더 | 출처 | 용도 | 연동 모듈 |
|------|------|------|----------|
| `02.codebase/01.python/` | 패스트캠퍼스 | 데이터분석 실습 (pandas, 시각화, ML) | `03_python_syntax` |
| `02.codebase/02.agent-park/` | 공원나연 fastcampus-aiagent | LangGraph 실습 코드 | `06_agent` |
| `02.codebase/03.RAG-park/` | 공원나연 fastcampus-graphrag | GraphRAG/Neo4j 실습 | `05_llm`, `06_agent` |
| `03.agent-SOTA/` | Exa + Context7 검증 | 2026 최신 트렌드 — 에이전트 학습 시 **필독** | `06_agent` |
| `04.agent-10papers/` | (예약) | 향후 top10 논문 자리 | `05_llm`, `06_agent` |
| `05.seminar_project/` | MartialAgent/AgentDAG | 자체 연구 자료 (실험·논문) | 심화/응용 |

### 모듈별 코드 참조 매핑
- 에이전트 코딩 문제 출제 시 → `02.codebase/02.agent-park/` LangGraph 예제 참고
- RAG/GraphRAG 학습 시 → `02.codebase/03.RAG-park/` 우선
- 최신 트렌드 질문 시 → `03.agent-SOTA/ai_agent_trends_2026_05.md`

---

## 5. 활용방법 — 스킬 4종

학습 시스템은 4개의 슬래시 스킬로 동작한다. 정의는 `.claude/commands/`에 있다.

| 스킬 | 호출 시점 | 동작 요약 |
|------|----------|----------|
| `/study` | 세션 시작 | 진도 확인 → 범위·방법 협의 → 학습 진입 |
| `/loop` | 학습 루프 진입 | CLAUDE.md 세션 프로토콜(7단계) 무한 반복 |
| `/memo` | 학습 도중 | 일자별 `00.memo/YYYY-MM-DD.md`에 메모 누적 |
| `/finish` | 세션 종료 | 통계 출력 → 진도 저장 → 자동 커밋·푸시 |

### 일반 사용 흐름
```
1. claude 진입
2. /study             ← 오늘 뭐 할지 정하기
3. /loop              ← 무한 학습 루프 진입
   (문제 풀이 반복)
4. /memo {내용}        ← 도중 인사이트 메모 (선택)
5. "그만" 또는 /finish ← 세션 종료, 커밋·푸시
```

---

## 6. 세션 프로토콜 (`/loop` 7단계)

### 1단계: 상태 확인
```bash
python -X utf8 01.basic_study/init_progress.py status
```
- 현재 모듈, 정답률, 약점 토픽 확인
- 모듈이 미선택이면 사용자에게 선택 요청

### 2단계: 토픽 선정
우선순위:
1. `weak_topics`에 있는 약점 토픽 (오답 우선 반복)
2. `completed_topics`에 없는 미완료 토픽
3. 전체 순환 (모든 토픽 완료 시)

### 3단계: 개념 설명
`01.basic_study/0X_*.md`의 해당 토픽 섹션을 읽고 대화체로 설명한다.
에이전트 모듈(`06_agent.md`) 학습 시 `03.agent-SOTA/ai_agent_trends_2026_05.md`를 함께 참조한다.
- 3~5줄 핵심 요약
- 직관적 비유 1개
- 코드 예시 1개 (간단한 것)

### 4단계: 문제 출제
레벨을 순환하며 출제한다:
- 🟢 **레벨 1**: 개념 확인 (객관식 or 단답)
- 🟡 **레벨 2**: 계산 / 설명 (주관식)
- 🔴 **레벨 3**: 코딩 (Python 코드 작성)

문제 형식:
```
[문제 {번호}] {레벨 이모지} {레벨명}
{문제 내용}

힌트: (사용자가 요청 시에만 제공)
```

### 5단계: 답변 평가
**코드 답변인 경우:**
- 코드를 실제로 실행해 결과 확인
- 실행 명령: `python -c "..."` 또는 임시 파일 작성 후 실행

**개념 답변인 경우:**
- MD 파일 내용과 대조해 정오 판단
- 부분 점수 가능 (핵심 키워드 포함 여부)

**피드백 형식:**
```
✓ 정답 / ✗ 오답 / △ 부분 정답

[피드백]
{오답이면 올바른 개념 재설명}
{정답이면 심화 내용 1가지 추가}
```

### 6단계: 진도 업데이트
```bash
python -X utf8 01.basic_study/init_progress.py record correct --topic {topic}   # 정답
python -X utf8 01.basic_study/init_progress.py record wrong  --topic {topic}    # 오답
```

### 7단계: 다음 문제로
- 같은 토픽에서 레벨업 → 또는
- 다음 토픽으로 이동
- 10문제마다 중간 통계 출력

---

## 7. 루프 행동 규칙

### 반드시 해야 하는 것
- 매 문제마다 `init_progress.py record`로 결과 기록
- 오답 토픽은 `weak_topics`에 자동 추가됨 — 다음 세션에서 우선 출제
- 세션 종료 시 `init_progress.py end` 호출 → `session_log.md` 자동 업데이트

### 하지 말아야 하는 것
- 사용자가 요청하지 않으면 힌트 먼저 제공하지 않기
- 틀린 답에 바로 정답 알려주지 않기 (한 번 더 시도 유도)
- 같은 문제를 연속 출제하지 않기

### 약점 반복 규칙
- `weak_topics` 목록에 있는 토픽은 다음 세션에서 우선 출제
- 해당 토픽에서 2번 연속 정답 시 `weak_topics`에서 제거
- 오답률 60% 이상 토픽은 레벨 1부터 다시 시작

---

## 8. 문제 출제 예시

### 확률통계 예시
```
[문제 3] 🟡 레벨 2 — 계산

P(A) = 0.3, P(B) = 0.4, P(A∩B) = 0.1 일 때
P(A|B)를 계산하라. (소수점 둘째 자리까지)
```

### 파이썬 문법 예시
```
[문제 7] 🟢 레벨 1 — 동작 예측

아래 코드의 출력값은?
list(map(lambda x: x**2, filter(lambda x: x%2==0, range(1, 6))))
```

### 코딩 예시
```
[문제 12] 🔴 레벨 3 — 코딩

numpy만 사용해서 100×50 랜덤 행렬의
상위 3개 특이값과 전체 분산 대비 설명 분산 비율을 출력하라.
```

---

## 9. 메모 스킬 (`/memo`)

세션 도중 정리하고 싶은 개념·깨달음·헷갈렸던 부분이 있을 때 호출한다.
실제 동작은 `.claude/commands/memo.md` 에 정의되어 있다.

- `/memo` — 직전 대화의 핵심을 2~4줄로 자동 요약해 저장
- `/memo {내용}` — 사용자가 직접 작성한 내용을 그대로 저장

저장 위치: `00.memo/YYYY-MM-DD.md` (일자별 파일에 누적)
항목 형식:
```
## [YYYY-MM-DD HH:mm] {module} — {topic}

{메모 본문}
```

규칙:
- 진도(`progress.json`)는 건드리지 않는다
- 커밋/푸시는 하지 않는다 (`/finish`에서 일괄 처리)
- 메모 저장 후 진행 중이던 문제/대화로 그대로 복귀

---

## 10. 세션 종료 프로토콜 (`/finish`)

사용자가 "그만", "종료", "끝내자", 또는 `/finish` 호출 시:

1. 현재 문제 피드백 완료
2. 세션 통계 출력 (오늘 문제수 / 정답률 / 새 약점)
3. `init_progress.py end --summary "..."` 실행 → `session_log.md` 기록
4. 다음 세션 예고 (약점 토픽 기반)
5. 자동 커밋·푸시 (`01.basic_study/progress.json`, `session_log.md`, `00.memo/*` 포함)

커밋 메시지 예시: `Study session: 2026-06-22 — agent ReAct, Tool Use (7/9)`

---

## 11. 진도 파일 구조

```
01.basic_study/progress.json    — 학습 진도 (자동 관리)
01.basic_study/session_log.md   — 세션별 기록 (자동 추가)
01.basic_study/init_progress.py — 진도 관리 CLI
01.basic_study/test_guide.md    — 모듈별 검증 체크리스트
01.basic_study/verify_weak_topics.py — 약점 알고리즘 시뮬레이션
00.memo/YYYY-MM-DD.md           — 세션 중 메모 (/memo 로 일자별 누적)
```

`progress.json` 스키마:
```json
{
  "module": "nlp",
  "completed_topics": ["tokenization", "embedding"],
  "weak_topics": ["attention_mechanism"],
  "total_questions": 42,
  "correct": 35,
  "last_session": "2026-06-22",
  "sessions": [...]
}
```

---

## 12. 빠른 시작

```bash
# 모듈 선택 후 학습 시작 (Windows는 -X utf8 필수)
python -X utf8 01.basic_study/init_progress.py set agent
python -X utf8 01.basic_study/init_progress.py status

# Claude Code에서
> /study              # 오늘 뭐 할지 정하기
> /loop               # 무한 학습 루프 진입
```

> **Windows 주의**: `init_progress.py` 실행 시 반드시 `python -X utf8` 옵션을 사용한다.
> 또는 환경변수 `PYTHONUTF8=1` 설정 후 사용 가능.

---

## 13. 성공 지표

- 1회 세션에서 최소 10문제 사이클 완료
- 6개 모듈 전체를 끊김 없이 순환
- 오답 토픽이 다음 세션에 자동 재출제됨을 확인
- 사용자가 "이제 이 개념은 이해했다"고 판단할 때까지 반복
