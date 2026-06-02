Study session finish skill. Saves session stats, commits, and pushes.

## 실행 순서

### 1. 현재 문제 피드백 완료
진행 중인 문제가 있으면 마무리한다.

### 2. 세션 통계 출력
```bash
python -X utf8 "basic study/init_progress.py" status
```
아래 항목을 사용자에게 보여준다:
- 오늘 푼 문제 수 / 정답 수
- 이번 세션 정답률
- 새로 추가된 weak_topics

### 3. 전체 진도 퍼센테이지 계산 및 세션 종료 기록
```bash
python -X utf8 "basic study/init_progress.py" end --summary "{오늘 학습한 토픽 요약}"
```
`progress.json`의 completed_topics / 전체 토픽 수로 완료율 계산해서 출력:
> 전체 커리큘럼 진도: X / Y 토픽 완료 (Z%)

### 4. 다음 세션 예고
weak_topics 기반으로 다음에 집중할 토픽 1~2개 안내.

### 5. 커밋 & 푸시
```bash
cd "c:\Work\Agent Study"
git add "basic study/progress.json" "basic study/session_log.md"
git commit -m "Study session: {오늘 날짜} — {학습 토픽} ({정답수}/{총문제수})"
git push origin master
```

커밋 메시지 예시:
`Study session: 2026-05-15 — agent ReAct, Tool Use (7/9)`
