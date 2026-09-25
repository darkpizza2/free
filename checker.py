import urllib.request
from python_v2ray.downloader import BinaryDownloader
from python_v2ray.tester import ConnectionTester
from python_v2ray.config_parser import parse_uri
from pathlib import Path

# 1. Читаем список источников
with open("sources.txt") as f:
    sources = [line.strip() for line in f if line.strip() and not line.startswith("#")]

# 2. Собираем все сырые конфиги из всех источников
raw_configs = []
for src in sources:
    try:
        data = urllib.request.urlopen(src, timeout=15).read().decode()
        raw_configs.extend([line.strip() for line in data.splitlines() if line.strip()])
        print(f"[OK] {src} — {len(data.splitlines())} строк")
    except Exception as e:
        print(f"[FAIL] {src} — {e}")

# 3. Дедупликация и парсинг
seen = set()
parsed = []
for u in raw_configs:
    if u in seen:
        continue
    seen.add(u)
    try:
        p = parse_uri(u)
        if p:
            parsed.append(p)
    except Exception:
        pass

print(f"[INFO] Уникальных конфигов: {len(parsed)}")

# 4. Ограничиваем количество тестов
LIMIT = 120
parsed = parsed[:LIMIT]

# 5. Скачиваем Xray и тестируем
downloader = BinaryDownloader(Path("./"))
downloader.ensure_all()

tester = ConnectionTester(vendor_path="./vendor", core_engine_path="./core_engine")
results = tester.test_uris(parsed)

# 6. Фильтруем живые и сортируем по пингу
alive = [r for r in results if r.get("ping_ms") and r["ping_ms"] < 1500]
alive_sorted = sorted(alive, key=lambda x: x["ping_ms"])[:15]

# 7. Записываем результат
with open("alive.txt", "w") as f:
    for r in alive_sorted:
        f.write(r["uri"] + "\n")

print(f"[DONE] Живых: {len(alive)}, записано топ-{len(alive_sorted)}")
