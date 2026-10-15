"""Export a complete search index in bounded static JSON files."""
import json


def write_search_index(records, destination, max_bytes=2000000):
    encoded = [json.dumps(row, ensure_ascii=False) for row in records]
    if sum(len(row.encode()) + 2 for row in encoded) <= max_bytes:
        (destination / 'search.json').write_text('[' + ', '.join(encoded) + ']\n')
        return
    folder = destination / 'search-data'
    folder.mkdir(exist_ok=True)
    groups, current, size = [], [], 2
    for row in encoded:
        weight = len(row.encode()) + 2
        if current and size + weight > max_bytes:
            groups.append(current)
            current, size = [], 2
        current.append(row)
        size += weight
    if current:
        groups.append(current)
    chunks = []
    for index, group in enumerate(groups):
        name = f'{index:03}.json'
        (folder / name).write_text('[' + ', '.join(group) + ']\n')
        chunks.append('search-data/' + name)
    (destination / 'search.json').write_text(json.dumps({'version': 2, 'chunks': chunks}) + '\n')
