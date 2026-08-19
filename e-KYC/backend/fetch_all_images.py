import os
import shutil
from pathlib import Path

src = Path('data/processed')
dst = Path(r'C:\Users\user\.gemini\antigravity-ide\brain\9ed9ff69-a2f8-4ce3-a18c-2e2dc20aad06')
md_lines = ['# All Session Images\n\nHere are all the images in the processed folder:']

for i, f in enumerate(src.glob('*.png')):
    dest_file = dst / f'all_image_{i}.png'
    shutil.copy(f, dest_file)
    md_lines.append(f'\n![Image {i}](file:///{dest_file.as_posix()})')

dst.joinpath('all_session_images.md').write_text('\n'.join(md_lines), encoding='utf-8')
print("Artifact created!")
