# django__django-11742

## Plan

def _check_choices_length(self):
        if self.choices and self.max_length is not None:
            for value, _ in self.choices:
                # Skip None or empty string checks if they are valid "null" representations
                # but strictly string length check
                if value is not None:
                    if len(str(value)) > self.max_length:
                        return [checks.Error(
                            "The field %s has a choice value '%s' which is longer than the max_length (%s)." % (self.name, value, self.max_length),
                            obj=self,
                            id='fields.E120',
                        )]
        return []

## Patch

```diff

```
