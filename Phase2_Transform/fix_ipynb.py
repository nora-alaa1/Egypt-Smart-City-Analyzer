import json

path = '/data/phase2_transform/SmartCity_Phase1_Fixed.ipynb'
with open(path, 'r', encoding='utf-8') as f:
    d = json.load(f)

changed = False
for cell in d['cells']:
    if cell['cell_type'] == 'code':
        new_source = []
        for line in cell['source']:
            if 'filter(F.col("subcategory") != "School")' in line:
                changed = True
                continue
            new_source.append(line)
        cell['source'] = new_source

if changed:
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(d, f, indent=1)
    print("Notebook fixed!")
else:
    print("No changes made.")
