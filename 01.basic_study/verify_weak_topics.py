"""
M5: 약점 반복 알고리즘 검증 스크립트
progress.json에 누적된 데이터를 분석하고 약점 토픽 로직을 검증한다.
"""

import json
import sys
from pathlib import Path
from collections import defaultdict

PROGRESS_FILE = Path(__file__).parent / "progress.json"


def load() -> dict:
    if not PROGRESS_FILE.exists():
        print("[오류] progress.json이 없습니다. init_progress.py init 먼저 실행하세요.")
        sys.exit(1)
    with open(PROGRESS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def simulate_sessions(num_sessions: int = 5, questions_per_session: int = 10) -> None:
    """약점 반복 알고리즘 시뮬레이션 — 실제 데이터 없을 때 테스트용"""
    import random

    topics = {
        "prob_stats": ["bayes", "distributions", "mle", "entropy", "clt"],
        "nlp": ["tokenization", "embedding", "attention", "bpe", "bert"],
        "llm": ["transformer", "fine_tuning", "rag", "prompting", "evaluation"],
    }

    # 토픽별 가상 오답률 (높을수록 약점)
    weak_rates = {
        "bayes": 0.6, "attention": 0.7, "transformer": 0.5,
        "mle": 0.3, "embedding": 0.2, "fine_tuning": 0.4,
    }

    data = {
        "module": "prob_stats",
        "completed_topics": [],
        "weak_topics": [],
        "total_questions": 0,
        "correct": 0,
        "last_session": None,
        "sessions": [],
        "topic_stats": defaultdict(lambda: {"correct": 0, "total": 0}),
    }

    print("=" * 50)
    print("약점 반복 알고리즘 시뮬레이션")
    print("=" * 50)

    for session_idx in range(num_sessions):
        print(f"\n--- 세션 {session_idx + 1} ---")

        # 다음 세션 토픽 선정: 약점 우선
        all_topics = [t for ts in topics.values() for t in ts]
        weak = [t for t in data["weak_topics"] if t in all_topics]
        remaining = [t for t in all_topics if t not in data["completed_topics"]]

        session_topics = weak[:3] + [t for t in remaining if t not in weak][:questions_per_session - len(weak[:3])]
        session_topics = session_topics[:questions_per_session]

        session_correct = 0
        for topic in session_topics:
            wrong_rate = weak_rates.get(topic, 0.25)
            is_correct = random.random() > wrong_rate
            data["total_questions"] += 1
            if is_correct:
                data["correct"] += 1
                session_correct += 1
                data["topic_stats"][topic]["correct"] += 1
                # 2번 연속 정답 → 약점 해제
                if data["topic_stats"][topic]["correct"] >= 2 and topic in data["weak_topics"]:
                    data["weak_topics"].remove(topic)
                    print(f"  [약점 해제] {topic} — 2회 연속 정답")
            else:
                if topic not in data["weak_topics"]:
                    data["weak_topics"].append(topic)
                    print(f"  [약점 추가] {topic}")

            data["topic_stats"][topic]["total"] += 1

        session_accuracy = session_correct / len(session_topics) * 100 if session_topics else 0
        print(f"  세션 정답률: {session_accuracy:.1f}% ({session_correct}/{len(session_topics)})")
        print(f"  현재 약점: {data['weak_topics']}")

    # 최종 분석
    print("\n" + "=" * 50)
    print("최종 분석 결과")
    print("=" * 50)
    total_accuracy = data["correct"] / data["total_questions"] * 100 if data["total_questions"] else 0
    print(f"전체 정답률: {total_accuracy:.1f}% ({data['correct']}/{data['total_questions']})")
    print(f"최종 약점 토픽: {data['weak_topics']}")

    print("\n토픽별 성과:")
    for topic, stats in sorted(data["topic_stats"].items()):
        if stats["total"] > 0:
            rate = stats["correct"] / stats["total"] * 100
            flag = " [약점]" if topic in data["weak_topics"] else ""
            print(f"  {topic:20s}: {rate:5.1f}% ({stats['correct']}/{stats['total']}){flag}")


def analyze_real_data() -> None:
    """실제 progress.json 데이터 분석"""
    data = load()

    print("=" * 50)
    print("실제 학습 데이터 분석")
    print("=" * 50)

    total = data["total_questions"]
    correct = data["correct"]
    accuracy = (correct / total * 100) if total else 0

    print(f"총 문제: {total}")
    print(f"정답률: {accuracy:.1f}%")
    print(f"완료 토픽: {data['completed_topics']}")
    print(f"약점 토픽: {data['weak_topics']}")

    # 약점 우선순위 분석
    if data["weak_topics"]:
        print("\n약점 토픽 우선순위 (다음 세션 출제 순서):")
        for i, topic in enumerate(data["weak_topics"], 1):
            print(f"  {i}. {topic}")
    else:
        print("\n현재 약점 토픽 없음.")

    # 세션 히스토리
    if data["sessions"]:
        print(f"\n세션 수: {len(data['sessions'])}")
        for s in data["sessions"][-3:]:  # 최근 3개만
            print(f"  {s['date']} ({s.get('module', '?')}): {s.get('summary', '')[:50]}")

    # 약점 알고리즘 검증
    print("\n[알고리즘 검증]")
    print(f"  약점 토픽 존재: {'Pass' if isinstance(data['weak_topics'], list) else 'Fail'}")
    print(f"  완료 토픽 존재: {'Pass' if isinstance(data['completed_topics'], list) else 'Fail'}")
    print(f"  중복 없음: {'Pass' if len(data['weak_topics']) == len(set(data['weak_topics'])) else 'Fail'}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="약점 반복 알고리즘 검증")
    sub = parser.add_subparsers(dest="cmd")

    p_sim = sub.add_parser("simulate", help="시뮬레이션 (가상 데이터)")
    p_sim.add_argument("--sessions", type=int, default=5, help="세션 수")
    p_sim.add_argument("--questions", type=int, default=10, help="세션당 문제 수")

    sub.add_parser("analyze", help="실제 progress.json 분석")

    args = parser.parse_args()

    if args.cmd == "simulate":
        simulate_sessions(args.sessions, args.questions)
    elif args.cmd == "analyze":
        analyze_real_data()
    else:
        print("사용법:")
        print("  python -X utf8 verify_weak_topics.py simulate --sessions 5 --questions 10")
        print("  python -X utf8 verify_weak_topics.py analyze")
