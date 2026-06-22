"""
AI Study Loop - Progress Tracker
학습 진도 초기화 및 관리 스크립트
"""

import json
import os
import sys
from datetime import date
from pathlib import Path

PROGRESS_FILE = Path(__file__).parent / "progress.json"

MODULES = {
    "prob_stats":     {"name": "확률통계",   "file": "01_prob_stats.md"},
    "linear_algebra": {"name": "선형대수",   "file": "02_linear_algebra.md"},
    "python_syntax":  {"name": "파이썬 문법", "file": "03_python_syntax.md"},
    "nlp":            {"name": "NLP",         "file": "04_nlp.md"},
    "llm":            {"name": "LLM",         "file": "05_llm.md"},
    "agent":          {"name": "에이전트",    "file": "06_agent.md"},
}

DEFAULT_PROGRESS = {
    "module": None,
    "completed_topics": [],
    "weak_topics": [],
    "total_questions": 0,
    "correct": 0,
    "last_session": None,
    "sessions": []
}


def load() -> dict:
    if PROGRESS_FILE.exists():
        with open(PROGRESS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return DEFAULT_PROGRESS.copy()


def save(data: dict) -> None:
    with open(PROGRESS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def init(module: str = None) -> dict:
    """진도 초기화 (모듈 지정 시 해당 모듈만, 없으면 전체 리셋)"""
    if module and module not in MODULES:
        print(f"[오류] 알 수 없는 모듈: {module}")
        print(f"사용 가능한 모듈: {', '.join(MODULES)}")
        sys.exit(1)

    data = DEFAULT_PROGRESS.copy()
    if module:
        data["module"] = module
    save(data)
    label = MODULES[module]["name"] if module else "전체"
    print(f"[초기화 완료] {label} 진도가 초기화되었습니다.")
    return data


def set_module(module: str) -> dict:
    """현재 학습 모듈 변경"""
    if module not in MODULES:
        print(f"[오류] 알 수 없는 모듈: {module}")
        sys.exit(1)
    data = load()
    data["module"] = module
    save(data)
    print(f"[모듈 변경] 현재 모듈: {MODULES[module]['name']}")
    return data


def record_question(correct: bool, topic: str = None) -> dict:
    """문제 풀이 결과 기록"""
    data = load()
    data["total_questions"] += 1
    if correct:
        data["correct"] += 1
        if topic and topic in data["weak_topics"]:
            data["weak_topics"].remove(topic)
    else:
        if topic and topic not in data["weak_topics"]:
            data["weak_topics"].append(topic)
    data["last_session"] = date.today().isoformat()
    save(data)
    return data


def complete_topic(topic: str) -> dict:
    """토픽 완료 처리"""
    data = load()
    if topic not in data["completed_topics"]:
        data["completed_topics"].append(topic)
    save(data)
    return data


def end_session(summary: str = "") -> dict:
    """세션 종료 및 로그 기록"""
    data = load()
    session = {
        "date": date.today().isoformat(),
        "module": data["module"],
        "summary": summary,
        "questions_this_session": 0,
    }
    data["sessions"].append(session)
    data["last_session"] = date.today().isoformat()
    save(data)

    # session_log.md 업데이트
    log_file = Path(__file__).parent / "session_log.md"
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(f"\n## {session['date']} — {MODULES.get(session['module'], {}).get('name', session['module'])}\n")
        if summary:
            f.write(f"{summary}\n")
        accuracy = (data["correct"] / data["total_questions"] * 100) if data["total_questions"] else 0
        f.write(f"- 누적 정답률: {accuracy:.1f}% ({data['correct']}/{data['total_questions']})\n")
        if data["weak_topics"]:
            f.write(f"- 약점 토픽: {', '.join(data['weak_topics'])}\n")
    return data


def get_next_topic() -> str:
    """다음으로 학습할 토픽 추천 (약점 우선)"""
    data = load()
    if data["weak_topics"]:
        return data["weak_topics"][0]
    return None


def status() -> None:
    """현재 진도 출력"""
    data = load()
    module_name = MODULES.get(data["module"], {}).get("name", "미선택") if data["module"] else "미선택"
    accuracy = (data["correct"] / data["total_questions"] * 100) if data["total_questions"] else 0

    print("=" * 40)
    print("       AI Study Loop - 학습 현황")
    print("=" * 40)
    print(f"현재 모듈    : {module_name}")
    print(f"마지막 세션  : {data['last_session'] or '없음'}")
    print(f"총 문제수    : {data['total_questions']}")
    print(f"정답률       : {accuracy:.1f}% ({data['correct']}/{data['total_questions']})")
    print(f"완료 토픽    : {', '.join(data['completed_topics']) or '없음'}")
    print(f"약점 토픽    : {', '.join(data['weak_topics']) or '없음'}")
    print("=" * 40)


def list_modules() -> None:
    """사용 가능한 모듈 목록 출력"""
    data = load()
    print("\n사용 가능한 학습 모듈:")
    print("-" * 40)
    for key, info in MODULES.items():
        current = " ← 현재" if data["module"] == key else ""
        md_exists = "O" if Path(__file__).parent.joinpath(info["file"]).exists() else "X"
        print(f"  {md_exists} {key:20s} {info['name']}{current}")
    print()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="AI Study Loop 진도 관리")
    sub = parser.add_subparsers(dest="cmd")

    sub.add_parser("status", help="현재 학습 현황 출력")
    sub.add_parser("modules", help="모듈 목록 출력")

    p_init = sub.add_parser("init", help="진도 초기화")
    p_init.add_argument("module", nargs="?", help="초기화할 모듈 (없으면 전체)")

    p_set = sub.add_parser("set", help="학습 모듈 변경")
    p_set.add_argument("module", help="모듈 키 (예: nlp)")

    p_q = sub.add_parser("record", help="문제 결과 기록")
    p_q.add_argument("result", choices=["correct", "wrong"])
    p_q.add_argument("--topic", default=None, help="토픽 이름")

    p_done = sub.add_parser("complete", help="토픽 완료 처리")
    p_done.add_argument("topic", help="완료된 토픽 이름")

    p_end = sub.add_parser("end", help="세션 종료")
    p_end.add_argument("--summary", default="", help="세션 요약")

    args = parser.parse_args()

    if args.cmd == "status":
        status()
    elif args.cmd == "modules":
        list_modules()
    elif args.cmd == "init":
        init(args.module)
    elif args.cmd == "set":
        set_module(args.module)
    elif args.cmd == "record":
        record_question(args.result == "correct", args.topic)
        status()
    elif args.cmd == "complete":
        complete_topic(args.topic)
        print(f"[완료] 토픽 '{args.topic}' 완료 처리됨")
    elif args.cmd == "end":
        end_session(args.summary)
        print("[세션 종료] session_log.md 업데이트됨")
    else:
        parser.print_help()
