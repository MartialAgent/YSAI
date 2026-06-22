# M4 테스트 가이드 — 모듈별 학습 루프 검증

각 모듈에 대해 최소 10문제 사이클이 정상 작동하는지 확인한다.

---

## 테스트 체크리스트

### 공통 사전 확인
- [ ] `python -X utf8 init_progress.py modules` — 6개 모듈 모두 `O` 표시
- [ ] `python -X utf8 init_progress.py status` — 기본 상태 출력 정상

---

### 모듈 1: 확률통계 (prob_stats)
```bash
python -X utf8 init_progress.py set prob_stats
```
확인 항목:
- [ ] 베이즈 정리 계산 문제 출제 및 코드 실행 검증
- [ ] scipy.stats 코드 문제 출제
- [ ] 오답 시 weak_topics에 추가되는지 확인

### 모듈 2: 선형대수 (linear_algebra)
```bash
python -X utf8 init_progress.py set linear_algebra
```
확인 항목:
- [ ] 고유값 계산 문제 출제
- [ ] SVD/PCA 코딩 문제 실행 검증
- [ ] numpy 코드 실행 정상 작동

### 모듈 3: 파이썬 문법 (python_syntax)
```bash
python -X utf8 init_progress.py set python_syntax
```
확인 항목:
- [ ] 코드 동작 예측 문제 출제
- [ ] 람다/제너레이터 코딩 문제
- [ ] 실행 결과 비교 검증

### 모듈 4: NLP (nlp)
```bash
python -X utf8 init_progress.py set nlp
```
확인 항목:
- [ ] BPE 구현 문제 출제
- [ ] Attention 수식 설명 문제
- [ ] transformers 라이브러리 코드 실행

### 모듈 5: LLM (llm)
```bash
python -X utf8 init_progress.py set llm
```
확인 항목:
- [ ] Transformer 구조 설명 문제
- [ ] Anthropic API 활용 코딩 문제
- [ ] temperature 비교 실습

### 모듈 6: 에이전트 (agent)
```bash
python -X utf8 init_progress.py set agent
```
확인 항목:
- [ ] ReAct 패턴 구현 문제
- [ ] Tool Use API 활용 문제
- [ ] 멀티에이전트 설계 문제

---

## 루프 시작 명령

```bash
# Claude Code 터미널에서
/loop 01_prob_stats.md부터 확률통계 학습 시작

# 또는 특정 모듈 지정
/loop linear_algebra 모듈 학습 — progress.json에서 이어서 시작
```

---

## 10문제 사이클 성공 기준

| 항목 | 기준 |
|------|------|
| 문제 출제 | 레벨 1~3 균형있게 출제 |
| 코드 실행 | Python 코드 답변 실제 실행 후 비교 |
| 피드백 | 정오답 모두 구체적 피드백 제공 |
| 진도 기록 | `progress.json` 업데이트 확인 |
| 약점 추적 | 오답 토픽 `weak_topics` 반영 확인 |
| 세션 로그 | `session_log.md` 자동 기록 확인 |

---

## 기대 결과 (성공 시)

```
python -X utf8 init_progress.py status

========================================
       AI Study Loop - 학습 현황
========================================
현재 모듈    : NLP
마지막 세션  : 2026-05-11
총 문제수    : 12
정답률       : 75.0% (9/12)
완료 토픽    : tokenization, embedding
약점 토픽    : attention_mechanism
========================================
```
