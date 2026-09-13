"""Canli renkli terminal loglari."""
import datetime
import os

os.system("")  # Windows cmd'de ANSI renkleri etkinlestir

_RESET = "\033[0m"
_COLORS = {
    "info": "\033[96m",
    "ok": "\033[92m",
    "warn": "\033[93m",
    "err": "\033[91m",
    "heal": "\033[95m",
    "git": "\033[94m",
}
_TAGS = {"info": "....", "ok": " OK ", "warn": "UYARI", "err": "HATA", "heal": "ONAR", "git": "GIT "}


def _ts() -> str:
    return datetime.datetime.now().strftime("%H:%M:%S")


def log(level: str, msg: str):
    color = _COLORS.get(level, "")
    tag = _TAGS.get(level, "....")
    print(f"{color}[{_ts()}] [{tag}]{_RESET} {msg}", flush=True)


def info(m): log("info", m)


def ok(m): log("ok", m)


def warn(m): log("warn", m)


def err(m): log("err", m)


def heal(m): log("heal", m)


def git(m): log("git", m)
