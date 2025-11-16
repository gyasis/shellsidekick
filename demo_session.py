#!/usr/bin/env python3
"""Demo script for ShellSidekick session monitoring."""

import time
from datetime import datetime
from shellsidekick.models.session import Session, SessionType, SessionState
from shellsidekick.core.monitor import SessionMonitor
from shellsidekick.core.detector import PromptDetector

def demo():
    print("=" * 60)
    print("ShellSidekick MVP Demo - Session Monitoring")
    print("=" * 60)

    # Step 1: Start monitoring
    print("\n[Step 1] Starting session monitor...")
    session = Session(
        session_id="demo-session-1",
        session_type=SessionType.FILE,
        log_file="/tmp/test-session.log",
        file_position=0,
        start_time=datetime.now(),
        state=SessionState.ACTIVE,
        metadata={"demo": "true", "environment": "production"}
    )
    monitor = SessionMonitor(session)
    print(f"✓ Session started: {session.session_id}")
    print(f"  Status: {session.state.value}")
    print(f"  Log file: {session.log_file}")

    # Step 2: Simulate new content being written to the log
    print("\n[Step 2] Simulating SSH password prompt...")
    with open("/tmp/test-session.log", "a") as f:
        f.write("Please authenticate to continue.\n")
        f.write("Password: ")

    time.sleep(0.5)

    # Step 3: Get updates
    print("\n[Step 3] Checking for new content...")
    new_content, has_more = monitor.get_updates()
    print(f"✓ New content detected ({len(new_content)} characters)")
    print(f"  Content: {repr(new_content[:50])}...")

    # Step 4: Detect prompt
    print("\n[Step 4] Detecting input prompt...")
    detector = PromptDetector(min_confidence=0.70)

    # Read full log file for detection (includes the Password: prompt we just added)
    with open("/tmp/test-session.log", "r") as f:
        full_content = f.read()

    detection = detector.detect(full_content, file_position=monitor.session.file_position)

    if detection:
        print(f"✓ PROMPT DETECTED!")
        print(f"  Type: {detection.prompt_type.value}")
        print(f"  Text: '{detection.prompt_text}'")
        print(f"  Confidence: {detection.confidence:.2%}")
        print(f"  Dangerous: {detection.is_dangerous}")
        print(f"  Pattern: {detection.matched_pattern}")
    else:
        print("  No prompt detected")

    # Step 5: Simulate dangerous operation
    print("\n[Step 5] Simulating dangerous operation prompt...")
    with open("/tmp/test-session.log", "a") as f:
        f.write("\n\nWARNING: This will delete all data!\n")
        f.write("Continue? (yes/no): ")

    time.sleep(0.5)

    # Get new updates and detect - focus on new content only
    new_content, _ = monitor.get_updates()

    # Detect prompt in the new content
    detection = detector.detect(new_content, file_position=monitor.session.file_position)

    if detection:
        print(f"✓ DANGEROUS OPERATION DETECTED!")
        print(f"  Type: {detection.prompt_type.value}")
        print(f"  Text: '{detection.prompt_text}'")
        print(f"  Confidence: {detection.confidence:.2%}")

        # Check if surrounding text contains dangerous keywords
        if "delete" in new_content.lower() or "WARNING" in new_content:
            print(f"  ⚠️  Context contains dangerous keywords!")
        print(f"  Dangerous flag: {detection.is_dangerous}")

    # Step 6: Stop monitoring
    print("\n[Step 6] Stopping session monitor...")
    stats = monitor.stop(save_log=True)
    print(f"✓ Session stopped")
    print(f"  Total bytes processed: {stats['total_bytes_processed']}")
    print(f"  Duration: {stats['session_duration_seconds']:.2f}s")

    print("\n" + "=" * 60)
    print("Demo Complete!")
    print("=" * 60)

if __name__ == "__main__":
    demo()
