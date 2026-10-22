"""Verify UTF-8 integrity of project text files (catches mojibake).

Usage:  python tools/check_encoding.py [paths...]
Exit code 1 if any file is not clean UTF-8 or contains replacement/mojibake markers.
"""
import pathlib
import sys

MOJIBAKE = ("\ufffd", "\u951f", "\u9425", "\u5d4e", "\u6d93", "\u7e3a")  # FFFD, 锟, 鈥, ...
HAN = ("\u4e00", "\u9fff")


def han_count(text):
    return sum(1 for ch in text if HAN[0] <= ch <= HAN[1])


def check(path: pathlib.Path):
    raw = path.read_bytes()
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        print(f"DECODE-FAIL {path} :: {exc}")
        return False
    bad = sum(text.count(m) for m in MOJIBAKE)
    head = text.splitlines()[0][:40] if text else ""
    flag = "OK  " if bad == 0 else "BAD "
    print(f"{flag} {str(path):52} bytes={len(raw):7} han={han_count(text):5} bad={bad:4} | {head}")
    return bad == 0


def main(argv):
    targets = [pathlib.Path(p) for p in argv[1:]]
    if not targets:
        targets = sorted(p for p in pathlib.Path(".").rglob("*") if p.suffix in (".md", ".json", ".csv", ".gd", ".tscn"))
        targets = [p for p in targets if ".git" not in p.parts]
    ok = all([check(p) for p in targets if p.is_file()])
    return 0 if ok else 1


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    raise SystemExit(main(sys.argv))
