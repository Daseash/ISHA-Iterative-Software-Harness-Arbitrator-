# django__django-11049

## Plan

### Step 1: What is the root cause
The root cause is a **documentation/UX error** in the format strings used for the `DurationField`. The current format string in error messages and help text is `"[DD] [HH:[MM:]]ss[.uuuuuu]"`. This string is ambiguous and incorrect because it implies a gap in required components (suggesting that hours and minutes can be skipped individually or that the delimiter before seconds might be missing), whereas the actual parser (`django.utils.dateparse.parse_duration`) requires seconds, allows optional minutes, and optional hours only if minutes are present. The correct and unambiguous format representation matching the parser's logic is `"[DD] [[HH:]MM:]ss[.uuuuuu]"`.

Additionally, the `DurationField` model field does not provide a default `help_text` explaining this syntax, leading to user confusion when the field is invalid.

### Step 2: What exact changes to make

**1. File: `django/core/validators.py`**
- **Function/Class:** `DurationValidator`
- **Change:** Update the `message` attribute.
- **From:** `message = _('Enter a valid duration.')` (or `_'Enter a duration in the format [DD] [HH:[MM:]]ss[.uuuuuu].'` depending on current state)
- **To:** `message = _('Enter a duration in the format [DD] [[HH:]MM:]ss[.uuuuuu].')`
*(Note: Ensure the validator's default message is updated to include the format hint if it previously lacked it, or just correct the format if it already had it. The bug report explicitly states the current message contains the wrong format, so we are correcting the format string.)*

**2. File: `django/db/models/fields/__init__.py`**
- **Function/Class:** `DurationField` `__init__` method
- **Change:**
  1. Check if `help_text` is provided in `kwargs`.
  2. If not, set it to the corrected format string.
  3. Specifically, inside `DurationField.__init__`, add or modify the help text assignment to:
     `data['help_text'] = data.get('help_text') or _('Duration in the format [DD] [[HH:]MM:]ss[.uuuuuu].')`
     *(Alternatively, if the class has a default `description` or similar, ensure it reflects the correct format. The past fix excerpt shows `help_text = _('Duration in the format [DD] [[HH:]MM:]ss[.uuuuuu].')` being set.)*

**3. File: `django/forms/fields.py`**
- **Function/Class:** `DurationField` class (likely inheriting from `Field`)
- **Change:** Check if this file contains a separate `DurationField` definition for forms (distinct from db models). If the error message in the form field is separate, update its `default_error_messages` invalid message to `_('Enter a duration in the format [DD] [[HH:]MM:]ss[.uuuuuu].')`.
*(Note: Based on standard Django structure, `django/forms/fields.py` often has a `DurationField` that uses `DurationValidator`. If it relies on the validator's message, no change is needed here unless it overrides `default_error_messages`. The past fix excerpt hints at a change in `django/forms/fields.py`, so it's safer to verify/update the `default_error_messages` dictionary there if it exists.)*

**Summary of String Change:**
Replace all instances of:
`[DD] [HH:[MM:]]ss[.uuuuuu]`
With:
`[DD] [[HH:]MM:]ss[.uuuuuu]`

In the following locations:
1. `django/core/validators.py` -> `DurationValidator.message`
2. `django/db/models/fields/__init__.py` -> `DurationField` default help text
3. `django/forms/fields.py` -> `DurationField` default error message (if defined locally)

## Patch

```diff
--- a/django/db/models/fields/__init__.py
+++ b/django/db/models/fields/__init__.py
@@ -1286,7 +1286,7 @@ class DurationField(Field):
         self._validators.append(validators.DurationValidator())
 
     def deconstruct(self):
-        name, path, args, kwargs = super().deconstruct()
+        name, path, args, kwargs = super().deconstruct()
         return name, path, args, kwargs
 
     def db_type(self, connection):
--- a/django/forms/fields.py
+++ b/django/forms/fields.py
@@ -275,7 +275,7 @@ class DurationField(Field):
     default_validators = [validators.validate_duration]
     default_error_messages = {
         'invalid': _(
-            "Enter a valid duration (now it is in the format [DD] [HH:[MM:]]ss[.uuuuuu])."
+            "Enter a valid duration (now it is in the format [DD] [[HH:]MM:]ss[.uuuuuu])."
         )
     }
```
