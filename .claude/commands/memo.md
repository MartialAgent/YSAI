Study session memo skill. Saves a timestamped memo with the current study topic.

세션 도중 호출되어 **현재 공부 주제와 함께 메모를 `memo/` 폴더에 일자별 파일로 누적 저장**한다.

## 실행 순서

### 1. 현재 시각 확인
PowerShell:
```powershell
Get-Date -Format "yyyy-MM-dd HH:mm"
```
날짜 부분(`YYYY-MM-DD`)은 파일명에, 전체(`YYYY-MM-DD HH:mm`)는 항목 헤더에 사용.

### 2. 현재 공부 주제 확인
```bash
python -X utf8 basic/init_progress.py status
```
- `current_module` 식별
- 직전 대화 맥락에서 다루던 **구체적 토픽**을 함께 식별 (예: `python_syntax — 언패킹 문법`)

### 3. 메모 내용 결정
- `/memo <내용>` 형태로 인자가 있으면 → 그 내용을 메모 본문으로 사용
- 인자가 없으면 → 직전 대화에서 다룬 핵심 개념을 **2~4줄로 요약** (불릿 가능)

### 4. `memo/YYYY-MM-DD.md` 에 추가(append)
- `memo/` 폴더가 없으면 만든다.
- 해당 날짜 파일이 없으면 새로 만들고, 있으면 **맨 아래에 추가**한다.
- 같은 날짜 파일 안에 항목 여러 개가 누적되는 구조.

항목 형식:
```markdown
---
## [YYYY-MM-DD HH:mm] {module} — {topic}

{메모 본문}
```

코드 스니펫이 메모에 포함되면 그대로 펜스로 보존한다.

### 5. 저장 결과 안내
저장된 메모 블록을 그대로 출력하고 한 줄로 안내:
> 📝 `memo/YYYY-MM-DD.md` 에 저장 완료.

### 6. 원래 흐름 복귀
진행 중이던 문제/대화가 있으면 **메모 저장 후 그대로 이어간다**. 세션을 종료하지 않는다.

## 행동 규칙
- 메모는 짧고 핵심만. 장황한 설명 금지.
- 사용자 본인 표현(질문/오해/깨달음)이 있으면 그대로 인용해 보존.
- 진도(`progress.json`)는 건드리지 않는다. 메모는 학습 기록 보조 수단이다.
- 커밋/푸시는 하지 않는다. (`/finish` 에서 일괄 처리)