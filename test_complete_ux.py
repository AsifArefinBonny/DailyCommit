#!/usr/bin/env python3
"""
Comprehensive UX Test - Simulates Complete User Journey
Tests the actual user experience from start to finish
"""
import subprocess
import json
import time
import sys

CHAT_ID = 6676414504
WEBHOOK_URL = "https://ybblpzymovvngtllrsbn.supabase.co/functions/v1/telegram-webhook"

class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    END = '\033[0m'
    BOLD = '\033[1m'

def print_header(text):
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*80}{Colors.END}")
    print(f"{Colors.HEADER}{Colors.BOLD}{text:^80}{Colors.END}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'='*80}{Colors.END}\n")

def print_success(text):
    print(f"{Colors.GREEN}✓ {text}{Colors.END}")

def print_info(text):
    print(f"{Colors.CYAN}ℹ {text}{Colors.END}")

def print_warning(text):
    print(f"{Colors.WARNING}⚠ {text}{Colors.END}")

def print_error(text):
    print(f"{Colors.FAIL}✗ {text}{Colors.END}")

def send_command(text):
    """Send a text command to the bot"""
    data = {
        "message": {
            "message_id": int(time.time() * 1000),
            "from": {"id": CHAT_ID, "first_name": "Test"},
            "chat": {"id": CHAT_ID, "type": "private"},
            "date": int(time.time()),
            "text": text
        }
    }

    cmd = ['curl', '-s', '-X', 'POST', WEBHOOK_URL,
           '-H', 'Content-Type: application/json',
           '-d', json.dumps(data)]

    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.stdout

def send_callback(callback_data):
    """Simulate clicking a button"""
    data = {
        "callback_query": {
            "id": str(int(time.time() * 1000)),
            "from": {"id": CHAT_ID, "first_name": "Test"},
            "message": {
                "message_id": int(time.time() * 1000),
                "chat": {"id": CHAT_ID}
            },
            "data": callback_data
        }
    }

    cmd = ['curl', '-s', '-X', 'POST', WEBHOOK_URL,
           '-H', 'Content-Type: application/json',
           '-d', json.dumps(data)]

    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.stdout

def main():
    test_results = {
        "passed": 0,
        "failed": 0,
        "tests": []
    }

    print_header("COMPREHENSIVE UX TEST - COMPLETE USER JOURNEY")

    # Test 1: /start command
    print_info("Test 1: Testing /start command...")
    response = send_command("/start")
    print_info("Response received (check Telegram for welcome message with dashboard URL)")
    time.sleep(2)
    test_results["tests"].append({
        "name": "/start command",
        "status": "manual_check",
        "message": "Check Telegram for welcome message"
    })

    # Test 2: First /learn - Question 1/3
    print_info("Test 2: Sending /learn to get first question...")
    response = send_command("/learn")
    print_info("Question 1/3 should appear in Telegram")
    time.sleep(2)
    test_results["tests"].append({
        "name": "Question 1/3",
        "status": "manual_check",
        "message": "Check Telegram for Question 1/3"
    })

    # Test 3: Answer Question 1
    print_info("Test 3: Answering Question 1 (selecting option A)...")
    response = send_callback("answer_A")
    print_info("Should show feedback and Question 2/3")
    time.sleep(3)
    test_results["tests"].append({
        "name": "Answer Q1 -> Q2/3",
        "status": "manual_check",
        "message": "Check Telegram for feedback and Question 2/3"
    })

    # Test 4: Answer Question 2
    print_info("Test 4: Answering Question 2 (selecting option B)...")
    response = send_callback("answer_B")
    print_info("Should show feedback and Question 3/3")
    time.sleep(3)
    test_results["tests"].append({
        "name": "Answer Q2 -> Q3/3",
        "status": "manual_check",
        "message": "Check Telegram for feedback and Question 3/3"
    })

    # Test 5: Answer Question 3 - Lesson Complete!
    print_info("Test 5: Answering Question 3 (completing lesson)...")
    response = send_callback("answer_C")
    print_info("Should show:")
    print_info("  1. Feedback for Q3")
    print_info("  2. 'Lesson Complete!' celebration message")
    print_info("  3. XP earned notification")
    print_info("  4. Automatically start NEW AI-generated lesson (Question 1/3)")
    time.sleep(5)
    test_results["tests"].append({
        "name": "Lesson Complete + Auto New Lesson",
        "status": "manual_check",
        "message": "Check Telegram for celebration and new lesson"
    })

    # Test 6: Verify new lesson started
    print_info("Test 6: Verifying new lesson auto-started...")
    print_warning("CHECK TELEGRAM NOW!")
    print_info("You should see Question 1/3 of a NEW AI-generated lesson")
    print_info("Topic should be different from previous lesson")
    time.sleep(3)

    # Test 7: Answer one question from new lesson
    print_info("Test 7: Answering Question 1 of new lesson...")
    response = send_callback("answer_A")
    print_info("Should show Question 2/3 of the new lesson")
    time.sleep(3)

    # Test 8: Check /stats
    print_info("Test 8: Checking progress with /stats...")
    response = send_command("/stats")
    print_info("Should show:")
    print_info("  - Updated XP (from completed lesson)")
    print_info("  - Accurate question count")
    print_info("  - Dashboard URL link")
    time.sleep(3)
    test_results["tests"].append({
        "name": "/stats with updated progress",
        "status": "manual_check",
        "message": "Check Telegram for updated stats and dashboard URL"
    })

    # Test 9: Test /learn again
    print_info("Test 9: Testing /learn returns to current lesson...")
    response = send_command("/learn")
    print_info("Should show Question 2/3 or 3/3 (NOT Question 1/3)")
    print_info("Should continue the SAME lesson, not start a new one")
    time.sleep(3)
    test_results["tests"].append({
        "name": "/learn continues current lesson",
        "status": "manual_check",
        "message": "Check Telegram shows correct question number"
    })

    # Summary
    print_header("TEST SUMMARY")

    print(f"\n{Colors.BOLD}Manual Verification Required:{Colors.END}")
    print(f"\nPlease check your Telegram and verify the following:\n")

    checklist = [
        "✓ /start shows welcome message with personalized dashboard URL",
        "✓ Question 1/3 shows with lesson title and difficulty stars",
        "✓ Answering questions shows immediate feedback (correct/incorrect)",
        "✓ Progress indicator updates (1/3 → 2/3 → 3/3)",
        "✓ After Q3, 'Lesson Complete!' celebration message appears",
        "✓ XP earned is shown (e.g., '+30 XP')",
        "✓ NEW AI-generated lesson starts automatically",
        "✓ New lesson has different topic from previous one",
        "✓ /stats shows updated XP and dashboard URL",
        "✓ /learn continues current lesson (doesn't restart)",
        "✓ Dashboard loads at: https://asifarefinbonny.github.io/DailyCommit/?user=6676414504",
        "✓ Dashboard shows activity heatmap, stats, and progress"
    ]

    for item in checklist:
        print(f"  {item}")

    print(f"\n{Colors.BOLD}UX Quality Checks:{Colors.END}\n")

    ux_checks = [
        "Does the flow feel smooth and intuitive?",
        "Are messages clear and easy to understand?",
        "Is the celebration message motivating?",
        "Does auto-starting new lesson feel natural?",
        "Are difficulty indicators helpful?",
        "Does the dashboard load quickly?",
        "Is the dashboard visually appealing?",
        "Can you easily see your progress?"
    ]

    for item in ux_checks:
        print(f"  ❓ {item}")

    print(f"\n{Colors.HEADER}{'='*80}{Colors.END}")
    print(f"{Colors.CYAN}Test completed! Please review Telegram and dashboard.{Colors.END}")
    print(f"{Colors.CYAN}Dashboard: https://asifarefinbonny.github.io/DailyCommit/?user=6676414504{Colors.END}")
    print(f"{Colors.HEADER}{'='*80}{Colors.END}\n")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n{Colors.WARNING}Test interrupted by user{Colors.END}")
        sys.exit(1)
    except Exception as e:
        print(f"\n{Colors.FAIL}Test failed with error: {e}{Colors.END}")
        sys.exit(1)
