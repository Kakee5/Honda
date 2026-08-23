#!/usr/bin/env python3
"""One-off pass that shrinks/re-encodes every image already under assets/.

Safe to re-run: optimize_image() only keeps a result that is smaller, so a
second run reports 0 saved. Videos and the root-level favicons are left alone.

After running this, regenerate the data file so the paths match:
    python build_data.py
    python -c "import pathlib; d=open('site_data.json',encoding='utf-8').read(); pathlib.Path('data.js').write_text('window.SITE_DATA = '+d+';\\n', encoding='utf-8')"
"""
import pathlib
from imgopt import optimize_image, human, IMAGE_EXTS

BASE = pathlib.Path(__file__).parent
ASSETS = BASE / "assets"

total_before = total_after = 0
changed = renamed = 0

for path in sorted(ASSETS.rglob("*")):
    if not path.is_file() or path.suffix.lower() not in IMAGE_EXTS:
        continue
    result = optimize_image(path)
    if not result:
        continue
    final, before, after = result
    total_before += before
    total_after += after
    if after < before:
        changed += 1
        if final.name != path.name:
            renamed += 1
        rel = final.relative_to(BASE).as_posix()
        print(f"  {rel}: {human(before)} -> {human(after)}"
              f" ({100 - after * 100 // before}% smaller)")

saved = total_before - total_after
print(f"\nOptimised {changed} image(s), {renamed} renamed (png -> jpg)")
print(f"assets/ images: {human(total_before)} -> {human(total_after)}"
      f"  (saved {human(saved)})")
