Study session initialization skill.

## 실행 순서

### 1. 진도 상태 확인
```bash
python -X utf8 01.basic_study/init_progress.py status
```
출력에서 현재 모듈, 정답률, weak_topics 파악.

### 2. 공부 범위 및 방법 확인
사용자에게 두 가지를 확인한다:
- **범위**: 특정 토픽 지정 vs 자동 선택 (약점 우선)
- **방법**: 개념 설명 먼저 vs 바로 문제 풀기

예시 질문:
> 오늘 어떤 토픽 할까요? (약점 토픽: {weak_topics}) — 직접 지정하거나 "자동"이라고 하면 약점 우선으로 선택할게요.
> 개념 설명부터 할까요, 바로 문제로 들어갈까요?

### 3. 세션 시작 기록
```bash
python -X utf8 01.basic_study/init_progress.py start
```

### 4. 학습 진행
CLAUDE.md의 세션 프로토콜(3~7단계)에 따라 진행:
- 개념 설명: `01.basic_study/{module}.md` 해당 섹션 읽어서 대화체로 설명
- 에이전트 모듈이면 `03.SOTA/ai_agent_trends_2026_05.md` 함께 참조
- 문제 출제 → 평가 → 진도 기록 반복

### 행동 규칙
- 힌트는 요청 시에만
- 오답 시 바로 정답 알려주지 않고 한 번 더 시도 유도
- 매 문제 후 `01.basic_study/init_progress.py record` 호출
