# pylint-dev__pylint-5859

## Plan

escaped_notes = [re.escape(note) for note in self.notes]
self._notes_regexp = re.compile(r'^(?:%s):' % '|'.join(escaped_notes))

## Patch

```diff

```
