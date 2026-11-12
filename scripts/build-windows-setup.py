"""Build the downloadable Windows application/setup archive without runtime data."""
from pathlib import Path
import zipfile

ROOT = Path(__file__).resolve().parent.parent
OUTPUT = ROOT / 'public' / 'downloads' / 'LIN4CRE-SENTINEL-Windows-Setup.zip'
INCLUDE = ['backend', 'host_companion', 'windows', 'scripts', 'dist', 'docs', 'agents', 'config']
FILES = ['requirements.txt', 'README.md', 'LICENSE', 'SECURITY.md', 'THIRD_PARTY_NOTICES.md', 'CHANGELOG.md', 'SUPPORT.md']
EXCLUDED_PARTS = {'__pycache__', '.git', 'node_modules', 'data', 'host_data', 'logs', 'runtime'}

if not (ROOT / 'dist' / 'index.html').exists():
    print('Windows setup archive skipped: dist/index.html has not been built')
    raise SystemExit(0)
OUTPUT.parent.mkdir(parents=True, exist_ok=True)
with zipfile.ZipFile(OUTPUT, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
    archive.writestr('LIN4CRE-SENTINEL/data/', '')
    for folder in INCLUDE:
        source = ROOT / folder
        if not source.exists():
            continue
        for path in sorted(source.rglob('*')):
            if not path.is_file() or path.is_symlink() or path.suffix.lower() == '.zip' or any(part in EXCLUDED_PARTS for part in path.relative_to(ROOT).parts):
                continue
            archive.write(path, 'LIN4CRE-SENTINEL/' + str(path.relative_to(ROOT)))
    for name in FILES:
        path = ROOT / name
        if path.exists():
            archive.write(path, 'LIN4CRE-SENTINEL/' + name)
    archive.writestr('LIN4CRE-SENTINEL/START-HERE.txt', (ROOT / 'windows' / 'START-HERE.txt').read_text(encoding='utf-8'))
print(f'Created {OUTPUT} ({OUTPUT.stat().st_size} bytes)')
