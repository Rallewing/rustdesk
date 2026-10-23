"""Reject phone-host privileges in the final, merged PC-client APK."""
import sys
from pathlib import Path

text = Path(sys.argv[1]).read_text()
for forbidden in (
    "BIND_ACCESSIBILITY_SERVICE", "accessibilityservice.AccessibilityService",
    "InputService", "MainService", "FloatingWindowService", "BootReceiver",
    "READ_SMS", "RECEIVE_SMS", "BIND_NOTIFICATION_LISTENER_SERVICE",
    "SYSTEM_ALERT_WINDOW", "RECEIVE_BOOT_COMPLETED", "MEDIA_PROJECTION",
):
    if forbidden in text:
        raise SystemExit("Unexpected phone privilege/component: " + forbidden)
for required in ("de.rallewing.pcremote", "Ralf PC Remote", "android.permission.INTERNET"):
    if required not in text:
        raise SystemExit("Missing PC-client identity/permission: " + required)
print("PC-client manifest verified: no phone-control service or sensitive listener")
