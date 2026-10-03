# django__django-11742

## Plan

def _check_choices_length(self):
        """
        Ensure that the longest string value in self.choices does not
        exceed the field's max_length (if one is set).  This is relevant
        only for string‑based fields such as CharField and SlugField.
        """
        if not self.choices or self.max_length is None:
            return []

        errors = []
        # max_length is only meaningful for string fields.
        if isinstance(self.max_length, int):
            for choice_value, _ in self.choices:
                if isinstance(choice_value, str) and len(choice_value) > self.max_length:
                    errors.append(
                        checks.Error(
                            f'The longest choice value for field "{self.name}" '
                            f'exceeds its max_length of {self.max_length}.',
                            obj=self,
                            id='fields.E003',
                            hint=f'Increase max_length to at least {len(choice_value)}.',
                        )
                    )
                    # One error is enough; stop after the first too‑long value.
                    break
        return errors

## Patch

```diff

```
