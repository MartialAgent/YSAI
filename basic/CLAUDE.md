# AI Study Loop — Claude Code 학습 지침

이 디렉토리는 AI/ML 무한 학습 루프 시스템이다.
`/loop` 스킬로 진입하면 아래 지침에 따라 학습 세션을 진행한다.

---

## 학습 모듈

| 파일 | 모듈 | 핵심 주제 |
|------|------|----------|
| `prob_stats.md` | 확률통계 | 확률분포, 베이즈 정리, MLE, 정보이론 |
| `linear_algebra.md` | 선형대수 | 벡터/행렬, 고유값, SVD, PCA |
| `python_syntax.md` | 파이썬 문법 | 자료구조, 함수형, OOP, NumPy/Pandas |
| `nlp.md` | NLP | 토크나이저, 임베딩, Attention |
| `llm.md` | LLM | Transformer, 파인튜닝, RAG, 프롬프트 |
| `agent.md` | 에이전트 | ReAct, Tool Use, 메모리, 멀티에이전트 |

---

## 세션 시작 프로토콜

`/loop` 진입 시 아래 순서로 진행한다:

### 1단계: 상태 확인
```
python -X utf8 init_progress.py status
```
- 현재 모듈, 정답률, 약점 토픽 확인
- 모듈이 미선택이면 사용자에게 선택 요청

### 2단계: 토픽 선정
우선순위:
1. `weak_topics`에 있는 약점 토픽 (오답 우선 반복)
2. `completed_topics`에 없는 미완료 토픽
3. 전체 순환 (모든 토픽 완료 시)

### 3단계: 개념 설명
해당 모듈 MD 파일을 읽고 선정된 토픽 섹션을 대화체로 설명한다.
- 3~5줄 핵심 요약
- 직관적 비유 1개
- 코드 예시 1개 (간단한 것)

### 4단계: 문제 출제
레벨을 순환하며 출제한다:
- **레벨 1**: 개념 확인 (객관식 or 단답)
- **레벨 2**: 계산 / 설명 (주관식)
- **레벨 3**: 코딩 (Python 코드 작성)

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
```
python -X utf8 init_progress.py record correct --topic {topic}   # 정답
python -X utf8 init_progress.py record wrong  --topic {topic}    # 오답
```

### 7단계: 다음 문제로
- 같은 토픽에서 레벨업 → 또는
- 다음 토픽으로 이동
- 10문제마다 중간 통계 출력

---

## 루프 행동 규칙

### 반드시 해야 하는 것
- 매 문제마다 `init_progress.py record`로 결과 기록
- 오답 토픽은 `weak_topics`에 추가됨 (자동 처리)
- 세션 종료 시 `init_progress.py end` 호출
- `session_log.md`에 세션 요약 기록

### 하지 말아야 하는 것
- 사용자가 요청하지 않으면 힌트 먼저 제공하지 않기
- 틀린 답에 바로 정답 알려주지 않기 (한 번 더 시도 유도)
- 같은 문제를 연속 출제하지 않기

### 약점 반복 규칙
- `weak_topics` 목록에 있는 토픽은 다음 세션에서 우선 출제
- 해당 토픽에서 2번 연속 정답 시 `weak_topics`에서 제거
- 오답률 60% 이상 토픽은 레벨 1부터 다시 시작

---

## 문제 출제 예시

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

## 세션 종료 프로토콜

사용자가 "그만", "종료", "끝내자" 라고 하면:

1. 현재 문제 피드백 완료
2. 세션 통계 출력
3. 약점 토픽 요약
4. `python -X utf8 init_progress.py end --summary "..."` 실행
5. 다음 세션 예고 (약점 토픽 기반)

---

## 진도 파일 구조

```
progress.json — 학습 진도 (자동 관리)
session_log.md — 세션별 기록 (자동 추가)
init_progress.py — 진도 관리 CLI
```

---

## 빠른 시작

```bash
# 모듈 선택 후 학습 시작 (Windows는 -X utf8 필수)
python -X utf8 init_progress.py set nlp
python -X utf8 init_progress.py status

# Claude Code에서
> /loop NLP 모듈 학습 세션 시작
```

> **Windows 주의**: `init_progress.py` 실행 시 반드시 `python -X utf8` 옵션을 사용한다.
> 또는 환경변수 `PYTHONUTF8=1` 설정 후 `python -X utf8 init_progress.py ...` 사용 가능.
