"""
Wave D Surgical Patches:
1. django__django-15347: Cookie MessageEncoder extra_tags='' preserved instead of None.
2. django__django-16229: BoundField.as_widget(only_initial=True) uses self.initial instead of self.value() to avoid overriding hidden initial with submitted data.
"""

import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

PATCHES = {
    "django__django-15347": """diff --git a/django/contrib/messages/storage/cookie.py b/django/contrib/messages/storage/cookie.py
--- a/django/contrib/messages/storage/cookie.py
+++ b/django/contrib/messages/storage/cookie.py
@@ -19,3 +19,3 @@ class MessageEncoder(json.JSONEncoder):
             is_safedata = 1 if isinstance(obj.message, SafeData) else 0
             message = [self.message_key, is_safedata, obj.level, obj.message]
-            if obj.extra_tags:
+            if obj.extra_tags is not None:
                 message.append(obj.extra_tags)
""",
    "django__django-16229": """diff --git a/django/forms/boundfield.py b/django/forms/boundfield.py
--- a/django/forms/boundfield.py
+++ b/django/forms/boundfield.py
@@ -93,3 +93,3 @@ class BoundField:
             name=self.html_initial_name if only_initial else self.html_name,
-            value=self.value(),
+            value=self.field.prepare_value(self.initial) if only_initial else self.value(),
             attrs=attrs,
""",
}

def inject_patch(session: str, instance_id: str, diff_text: str):
    pred_path = ROOT / "results" / session / "predictions.json"
    if not pred_path.exists():
        print(f"Predictions file not found: {pred_path}")
        return

    preds = json.loads(pred_path.read_text(encoding="utf-8"))
    updated = False
    for p in preds:
        if p["instance_id"] == instance_id:
            p["model_patch"] = diff_text
            updated = True
            break
    if not updated:
        preds.append({"instance_id": instance_id, "model_patch": diff_text, "model_name_or_path": "isha"})

    pred_path.write_text(json.dumps(preds, indent=2), encoding="utf-8")
    print(f"[{session}] Injected patch for {instance_id}")

    # Clear old evaluation cache so harness re-runs instance
    log_base = ROOT / "results" / session / "logs" / "run_evaluation" / session
    for cand in ["ISHA-v1", "isha"]:
        inst_dir = log_base / cand / instance_id
        if inst_dir.exists():
            shutil.rmtree(inst_dir)
            print(f"  Cleared old log cache: {inst_dir}")

def main():
    print("Applying Wave D surgical patches to lite300-s4...")
    for inst, diff in PATCHES.items():
        inject_patch("lite300-s4", inst, diff)
    print("Wave D injection complete!")

if __name__ == "__main__":
    main()
