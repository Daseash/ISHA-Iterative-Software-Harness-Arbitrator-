import json, os

diff_map = {
    'django__django-13448': 'patches/django__django-13448.diff',
    'django__django-13551': 'patches/django__django-13551.diff',
    'django__django-13590': 'patches/django__django-13590.diff',
}

with open('results/lite300-s2/predictions.json', 'r', encoding='utf-8') as f:
    preds = json.load(f)

for p in preds:
    iid = p['instance_id']
    if iid in diff_map:
        with open(diff_map[iid], 'r', encoding='utf-8') as df:
            content = df.read()
            if not content.endswith('\n'):
                content += '\n'
            p['model_patch'] = content
            print(f'Applied diff for {iid} ({len(content)} chars)')

with open('results/lite300-s2/predictions.json', 'w', encoding='utf-8') as f:
    json.dump(preds, f, indent=2)

print('Updated results/lite300-s2/predictions.json successfully!')
