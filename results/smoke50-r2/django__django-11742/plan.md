# django__django-11742

## Plan

def _check_choices_max_length(self):
          if self.choices and self.max_length is not None:
              for value, _ in self.choices:
                  if isinstance(value, (list, tuple)):
                      # Handle grouped choices
                      for subvalue, _ in value:
                          if subvalue is not None and len(str(subvalue)) > self.max_length:
                              return [checks.Error(
                                  'Choices contain a value that is too long (length %d) for the field max_length (%d).' % (len(str(subvalue)), self.max_length),
                                  obj=self,
                                  id='fields.E009',
                              )]
                  elif value is not None and len(str(value)) > self.max_length:
                      return [checks.Error(
                          'Choices contain a value that is too long (length %d) for the field max_length (%d).' % (len(str(value)), self.max_length),
                          obj=self,
                          id='fields.E009',
                      )]
          return []

## Patch

```diff

```
