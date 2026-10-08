"""Fetch and statically audit selected OAI import closures at an immutable commit."""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
import re
import requests

ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / "source"
COMMIT = "fd4aeeb2ee4fc729c18d98444fed42fd0529eeeb"
WORKSPACE = ROOT.parents[3]
TREE = json.loads((WORKSPACE / "tmp/lean-study/complete-git-tree.json").read_text(encoding="utf8"))
INDEX = {x["path"]: x for x in TREE["tree"] if x["type"] == "blob"}

def fetch(path):
    target = SOURCE / path
    if not target.exists():
        response = requests.get(f"https://raw.githubusercontent.com/openai/math/{COMMIT}/{path}", timeout=45)
        response.raise_for_status()
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(response.content)
    data = target.read_bytes()
    actual = hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()
    assert actual == INDEX[path]["sha"], (path, actual, INDEX[path]["sha"])
    return data.decode("utf8")

def closure(seed):
    pending, seen, edges = {seed}, {}, []
    while pending:
        wave = sorted(pending)
        pending.clear()
        with ThreadPoolExecutor(max_workers=10) as pool:
            contents = list(pool.map(fetch, wave))
        for path, text in zip(wave, contents):
            seen[path] = text
            for imported in re.findall(r"^import\s+([^\n]+)", text, re.M):
                for module in imported.split():
                    if module.startswith("OAI."):
                        dependency = "lean/" + module.replace(".", "/") + ".lean"
                        edges.append([path, dependency])
                        if dependency not in seen:
                            pending.add(dependency)
    return {
        "seed": seed,
        "files": sorted(seen),
        "edges": edges,
        "file_count": len(seen),
        "bytes": sum(len(x.encode("utf8")) for x in seen.values()),
        "lexical_markers": [
            {"path": p, "line": n, "text": line}
            for p, text in sorted(seen.items())
            for n, line in enumerate(text.splitlines(), 1)
            if re.search(r"\b(sorry|admit|axiom|unsafe)\b", line)
        ],
    }

if __name__ == "__main__":
    results = [closure("lean/OAI/Analysis/TraceCone/IdealTransport.lean"),
               closure("lean/OAI/AlgebraicGeometry/CharacterVarieties/Seams/ProducedSolution.lean")]
    records = []
    for path in sorted(SOURCE.rglob("*.lean")) + sorted(SOURCE.rglob("*.json")):
        relative = path.relative_to(SOURCE).as_posix()
        if relative not in INDEX:
            continue
        data = path.read_bytes()
        actual = hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()
        assert actual == INDEX[relative]["sha"], relative
        records.append({"path": relative, "git_blob": actual,
                        "sha256": hashlib.sha256(data).hexdigest(), "bytes": len(data)})
    (ROOT / "source-audit.json").write_text(json.dumps({
        "commit": COMMIT, "method": "Static source/import audit; no Lean compilation or comparator execution",
        "closures": results, "source_files": records}, indent=2) + "\n", encoding="utf8")
    print(json.dumps([{k: v for k, v in r.items() if k not in ["files", "edges"]} for r in results], indent=2))
