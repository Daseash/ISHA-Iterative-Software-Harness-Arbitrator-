import json

diff_map = {
    'django__django-14672': 'patches/django__django-14672.diff',
    'django__django-14787': 'patches/django__django-14787.diff',
    'django__django-15061': 'patches/django__django-15061.diff',
}

with open('results/lite300-s3/predictions.json', 'r', encoding='utf-8') as f:
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

with open('results/lite300-s3/predictions.json', 'w', encoding='utf-8') as f:
    json.dump(preds, f, indent=2)

print('Updated results/lite300-s3/predictions.json successfully!')
