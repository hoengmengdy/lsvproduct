import json
import re
from pathlib import Path
from PIL import Image

root = Path(__file__).resolve().parent
sources = (("oka", root / "img" / "oka"), ("rins", root / "img" / "RINs"), ("empress", root / "img" / "products Empress"))
out_dir = root / "static" / "uploads"
out_dir.mkdir(parents=True, exist_ok=True)
manifest = []
prices = {"oka": "6.50", "rins": "4.50", "empress": "3.75"}
for category, folder in sources:
    files = sorted((p for p in folder.iterdir() if p.suffix.lower() in {".png", ".jpg", ".jpeg", ".webp"}), key=lambda p: p.name.casefold())
    for index, source in enumerate(files, 1):
        clean = re.sub(r"[_-]+", " ", source.stem)
        clean = re.sub(r"\s+", " ", clean).strip()
        prefix = {"oka": "OKA", "rins": "RINs", "empress": "Empress"}[category]
        if not clean.casefold().startswith(prefix.casefold()):
            name = f"{prefix} {clean}"
        else:
            name = clean
        filename = f"catalog-{category}-{index:02d}.webp"
        if not (out_dir / filename).exists():
            with Image.open(source) as image:
                image.thumbnail((900, 900), Image.Resampling.LANCZOS)
                if image.mode not in {"RGB", "RGBA"}:
                    image = image.convert("RGBA" if "transparency" in image.info else "RGB")
                image.save(out_dir / filename, "WEBP", quality=78, method=2)
        manifest.append({"name": name, "description": f"ផលិតផល {prefix} គុណភាពខ្ពស់ សម្រាប់ប្រើប្រាស់ប្រចាំថ្ងៃ។", "price": prices[category], "old_price": None, "stock": 30, "category": category, "image": filename})
(root / "catalog_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
print(f"Created {len(manifest)} products")