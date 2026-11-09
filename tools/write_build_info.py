import json
import os
from pathlib import Path

number = int(os.environ['GITHUB_RUN_NUMBER'])
Path('dist/Precision-CAD/build-info.json').write_text(json.dumps({
    'tag': f'test-{number}', 'number': number,
    'commit': os.environ['GITHUB_SHA'], 'version': '0.4',
}, indent=2), encoding='utf-8')
