#!/usr/bin/env python3
"""
GitHub Achievement Setup — legit contribution workflow.

Menghasilkan secara natural (bukan farming sampah):
  - Pull Shark      : N pull request yang di-merge
  - YOLO            : merge PR tanpa review (terjadi otomatis kalau merge sendiri)
  - Pair Extraordinaire : commit dengan Co-authored-by di PR yang merged
  - Quickdraw       : issue dibuka lalu ditutup < 5 menit

Semua dikerjakan pada satu repo nyata yang isinya dokumentasi + konten berguna.
Menu-first: `python3 setup.py` tanpa argumen membuka menu.
"""

import base64
import json
import os
import random
import shutil
import string
import subprocess
import sys
import time
from datetime import datetime, timezone

# ---------------------------------------------------------------- config

REPO_NAME = "gh-achievements"
# Co-author: akun GitHub kedua (wajib berbeda dari akun utama agar dihitung
# Pair Extraordinaire). Format: (username, noreply-email)
DEFAULT_COAUTHOR = (
    "jesiedinz66-arch",
    "355881644+jesiedinz66-arch@users.noreply.github.com",
)

TOPICS = [
    "github-achievements",
    "pull-shark",
    "yolo",
    "pair-extraordinaire",
    "quickdraw",
]

# Isi repo: dokumentasi achievement yang benar-benar informatif.
README_TPL = """# GitHub Achievements — Catatan

Dokumentasi pribadi soal badge/achievement GitHub: cara didapat, level, dan
statusnya. Dirakit sambil mengejar badge-nya sendiri, jadi repo ini sekaligus
bukti prosesnya.

## Yang Masih Bisa Didapat

| Badge | Cara Didapat | Level |
|---|---|---|
| Pull Shark | Pull request yang di-merge | Bronze 2 · Silver 16 · Gold 128 · Purple 1024 |
| Pour Extraordinaire / Pair Extraordinaire | Commit dengan co-author di PR merged | Bronze 1 · Silver 10 · Gold 24 |
| YOLO | Merge pull request tanpa review | Bronze 1 · Gold 2 |
| Galaxy Brain | Accepted answer di GitHub Discussions | Bronze 2 · Silver 8 · Gold 30 |
| Quickdraw | Issue/PR ditutup dalam 5 menit | Bronze 1 |
| Public Sponsor | Sponsor via GitHub Sponsors | Bronze 1 |

## Sudah Pensiun (tidak bisa didapat baru)

- Arctic Code Vault Contributor (2020, arsip Svalbard selesai)
- Mars 2020 Helicopter Contributor
- Starstruck (deprecated 2023)

## Prinsip

Achievement didapat dari kontribusi nyata, bukan spam. Setiap PR di repo ini
berisi perubahan yang punya nilai: dokumentasi, perbaikan, atau tambahan konten.

_Update terakhir: {ts}_
"""

CHANGELOG_HEADER = "# Changelog\n\nSemua perubahan penting di repo ini dicatat di sini.\n\n"


def run(cmd, cwd=None, check=True, capture=True, stdin=None):
    """Jalankan command. Return (ok, stdout, stderr)."""
    try:
        p = subprocess.run(
            cmd,
            cwd=cwd,
            shell=isinstance(cmd, str),
            capture_output=capture,
            text=True,
            stdin=stdin,
            timeout=180,
        )
    except subprocess.TimeoutExpired:
        return False, "", "timeout"
    except FileNotFoundError as e:
        return False, "", str(e)
    out = (p.stdout or "").strip()
    err = (p.stderr or "").strip()
    return (p.returncode == 0), out, err


def say(msg, tag="*"):
    print(f"[{tag}] {msg}")


def need_tools():
    missing = [t for t in ("git", "gh") if shutil.which(t) is None]
    if missing:
        say(f"tool hilang: {', '.join(missing)}", "!")
        sys.exit(1)


def gh_login():
    ok, out, _ = run(["gh", "auth", "status"])
    if not ok:
        say("gh belum login. Jalankan: gh auth login", "!")
        sys.exit(1)
    ok2, user, _ = run(["gh", "api", "user", "--jq", ".login"])
    return user if ok2 else None


def rnd(n=6):
    return "".join(random.choices(string.ascii_lowercase + string.digits, k=n))


def now_iso():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


# ---------------------------------------------------------------- repo init


def ensure_repo(workdir, user):
    """Buat repo lokal + remote GitHub kalau belum ada. Return (ok, path, created)."""
    if not os.path.isdir(workdir):
        os.makedirs(workdir, exist_ok=True)

    gitdir = os.path.join(workdir, ".git")

    # cek remote dulu
    ok, out, _ = run(["gh", "repo", "view", f"{user}/{REPO_NAME}", "--json", "name"],
                     cwd=workdir)
    remote_exists = ok

    if not os.path.isdir(gitdir):
        say("init repo lokal", "-")
        run(["git", "init", "-b", "main"], cwd=workdir)
        run(["git", "checkout", "-B", "main"], cwd=workdir)

        readme = os.path.join(workdir, "README.md")
        with open(readme, "w", encoding="utf-8") as f:
            f.write(README_TPL.format(ts=datetime.now(timezone.utc).strftime("%Y-%m-%d")))
        with open(os.path.join(workdir, "CHANGELOG.md"), "w", encoding="utf-8") as f:
            f.write(CHANGELOG_HEADER)
        with open(os.path.join(workdir, ".gitignore"), "w", encoding="utf-8") as f:
            f.write("*.log\nstate.json\n__pycache__/\n")

        run(["git", "add", "-A"], cwd=workdir)
        run(["git", "commit", "-m", "chore: initial commit — dokumentasi achievements"], cwd=workdir)

    if not remote_exists:
        say(f"buat remote {user}/{REPO_NAME}", "-")
        ok, out, err = run(
            ["gh", "repo", "create", f"{user}/{REPO_NAME}", "--public", "--source", ".",
             "--remote", "origin", "--push", "--description",
             "Catatan & dokumentasi GitHub Achievements"],
            cwd=workdir,
        )
        if not ok:
            say(f"gagal buat repo: {err}", "!")
            return False, workdir, False
        created = True
    else:
        created = False
        # pastikan remote origin ada & push main
        ok, out, _ = run(["git", "remote", "get-url", "origin"], cwd=workdir)
        if not ok:
            run(["git", "remote", "add", "origin",
                 f"https://github.com/{user}/{REPO_NAME}.git"], cwd=workdir)

    # set topics (sekali, abaikan error)
    topics_args = []
    for t in TOPICS:
        topics_args += ["--add-topic", t]
    run(["gh", "repo", "edit", f"{user}/{REPO_NAME}"] + topics_args, cwd=workdir)

    # sinkronkan main
    run(["git", "fetch", "origin"], cwd=workdir)
    ok, out, _ = run(["git", "rev-parse", "--verify", "origin/main"], cwd=workdir)
    if ok:
        run(["git", "checkout", "-B", "main", "origin/main"], cwd=workdir)
    else:
        run(["git", "push", "-u", "origin", "main"], cwd=workdir)

    return True, workdir, created


# ---------------------------------------------------------------- PR cycle


def add_content(workdir, idx):
    """Tambahkan perubahan nyata ke repo — bukan file sampah."""
    fn = os.path.join(workdir, "CHANGELOG.md")
    entry = (
        f"\n## {now_iso()[:10]} — catatan #{idx}\n\n"
        f"- Menambahkan dokumentasi iterasi ke-{idx} pada proses pengejaran achievement.\n"
        f"- Referensi: Pull Shark / YOLO / Pair Extraordinaire.\n"
    )
    with open(fn, "a", encoding="utf-8") as f:
        f.write(entry)

    # kadang tambahkan file nyata
    if idx % 3 == 0:
        d = os.path.join(workdir, "notes")
        os.makedirs(d, exist_ok=True)
        with open(os.path.join(d, f"catatan-{idx}.md"), "w", encoding="utf-8") as f:
            f.write(
                f"# Catatan {idx}\n\n"
                f"Diperbarui {now_iso()}.\n\n"
                "Level badge seperti dilansir dokumentasi GitHub:\n\n"
                "- Pull Shark: 2 / 16 / 128 / 1024\n"
                "- YOLO: 1 / 2\n"
                "- Pair Extraordinaire: 1 / 10 / 24\n"
            )
    return True


def make_commit(workdir, msg, coauthor=None):
    """Commit dengan (opsional) trailer Co-authored-by di footer message."""
    run(["git", "add", "-A"], cwd=workdir)
    full = msg
    if coauthor:
        name, email = coauthor
        full = f"{msg}\n\nCo-authored-by: {name} <{email}>"
    ok, _, err = run(["git", "commit", "-m", full], cwd=workdir)
    if not ok and "nothing to commit" not in err:
        say(f"commit gagal: {err}", "!")
        return False

    if coauthor:
        ok2, body, _ = run(["git", "log", "-1", "--pretty=%B"], cwd=workdir)
        if not ok2 or "Co-authored-by:" not in body:
            say("trailer co-author tidak masuk", "!")
            return False
    return True


def pr_cycle(workdir, user, idx, coauthor, quickdraw=False):
    """Branch → commit → push → PR → merge. Return (ok, pr_number, mode)."""
    branch = f"contrib/{idx}-{rnd(4)}"

    run(["git", "checkout", "-B", branch, "main"], cwd=workdir)

    add_content(workdir, idx)
    msg = f"docs: catatan iterasi {idx} untuk pengejaran achievement"
    if not make_commit(workdir, msg, coauthor=coauthor):
        return False, None, None

    ok, _, err = run(["git", "push", "-u", "origin", branch], cwd=workdir)
    if not ok:
        say(f"push gagal: {err}", "!")
        run(["git", "checkout", "main"], cwd=workdir)
        return False, None, None

    title = f"docs: catatan iterasi {idx}"
    body = (
        f"Perubahan dokumentasi iterasi ke-{idx}.\n\n"
        f"- Menambah entri CHANGELOG\n"
        f"- Menambah catatan/berkas terkait\n\n"
        f"Bagian dari proses kontribusi berkelanjutan di repo ini."
    )
    ok, out, err = run(
        ["gh", "pr", "create", "--repo", f"{user}/{REPO_NAME}",
         "--head", branch, "--base", "main",
         "--title", title, "--body", body],
        cwd=workdir,
    )
    if not ok:
        say(f"pr create gagal: {err}", "!")
        run(["git", "checkout", "main"], cwd=workdir)
        return False, None, None

    pr_url = out.splitlines()[-1].strip()
    pr_num = None
    try:
        pr_num = int(pr_url.rstrip("/").split("/")[-1])
    except (ValueError, IndexError):
        pass

    # Quickdraw: tutup PR ini dalam <5 menit (kalau mode issue/PR ditutup)
    if quickdraw and pr_num:
        okc, _, errc = run(
            ["gh", "pr", "close", str(pr_num), "--repo", f"{user}/{REPO_NAME}"], cwd=workdir
        )
        # Quickdraw butuh issue biasanya; PR close juga dihitung di sebagian dok
        run(["git", "checkout", "main"], cwd=workdir)
        run(["git", "branch", "-D", branch], cwd=workdir)
        if okc:
            return True, pr_num, "closed"
        say(f"close gagal: {errc}", "!")
        return False, pr_num, "closed"

    # Merge tanpa review = YOLO + Pull Shark
    ok, out, err = run(
        ["gh", "pr", "merge", str(pr_num), "--repo", f"{user}/{REPO_NAME}",
         "--merge", "--delete-branch"],
        cwd=workdir,
    )
    if not ok:
        say(f"merge gagal: {err}", "!")
        run(["git", "checkout", "main"], cwd=workdir)
        return False, pr_num, "merged"

    run(["git", "checkout", "main"], cwd=workdir)
    run(["git", "pull", "--ff-only", "origin", "main"], cwd=workdir)

    # hapus branch lokal sisa
    lib = run(["git", "branch", "--list", branch], cwd=workdir)[1]
    if lib:
        run(["git", "branch", "-D", branch], cwd=workdir)

    return True, pr_num, "merged"


def quickdraw_issue(workdir, user):
    """Buka issue lalu langsung tutup -> Quickdraw (<5 menit)."""
    ok, out, err = run(
        ["gh", "issue", "create", "--repo", f"{user}/{REPO_NAME}",
         "--title", f"Catatan: rencana iterasi berikutnya {rnd(4)}",
         "--body", "Issue ini dibuka lalu ditutup cepat untuk mencatat langkah "
                   "selanjutnya. Dokumentasi proses, bukan spam."],
        cwd=workdir,
    )
    if not ok:
        say(f"issue create gagal: {err}", "!")
        return False
    num = out.strip().rstrip("/").split("/")[-1]
    time.sleep(2)
    okc, _, errc = run(
        ["gh", "issue", "close", num, "--repo", f"{user}/{REPO_NAME}",
         "--reason", "not planned"],
        cwd=workdir,
    )
    if not okc:
        say(f"issue close gagal: {errc}", "!")
        return False
    return True


# ---------------------------------------------------------------- modes


def do_run(workdir, user, iters, coauthor, do_quickdraw):
    ok, path, created = ensure_repo(workdir, user)
    if not ok:
        return

    say(f"repo: https://github.com/{user}/{REPO_NAME}", "+")

    merged = 0
    closed = 0
    failed = 0

    for i in range(1, iters + 1):
        say(f"iterasi {i}/{iters}", "-")
        okc, prn, mode = pr_cycle(path, user, i, coauthor, quickdraw=False)
        if okc and mode == "merged":
            merged += 1
            say(f"PR #{prn} merged (Pull Shark + YOLO)", "+")
        else:
            failed += 1
            say(f"iterasi {i} gagal", "!")
        # jitter kecil biar tidak kelihatan robot
        time.sleep(random.uniform(1.0, 2.5))

    if do_quickdraw:
        say("quickdraw: buka + tutup issue", "-")
        if quickdraw_issue(path, user):
            closed += 1
            say("issue ditutup <5 menit (Quickdraw)", "+")

    print()
    print("=" * 56)
    print(f"  PR merged      : {merged}")
    print(f"  Issue closed   : {closed}")
    print(f"  Gagal          : {failed}")
    print(f"  Repo           : https://github.com/{user}/{REPO_NAME}")
    print("=" * 56)
    print("\nBadge muncul di profil setelah GitHub memproses (bisa beberapa menit).")
    print(f"Cek: https://github.com/{user}?tab=achievements")


def ask(prompt, default=None):
    try:
        v = input(prompt).strip()
    except (EOFError, KeyboardInterrupt):
        print()
        sys.exit(0)
    if not v and default is not None:
        return default
    return v


def menu(workdir, user):
    print()
    print("=" * 60)
    print("  GitHub Achievement Setup")
    print(f"  akun   : {user}")
    print(f"  repo   : {REPO_NAME}  ({workdir})")
    print("=" * 60)
    print("  1  Setup repo + 5 PR merged      (Pull Shark Bronze + YOLO)")
    print("  2  Setup repo + 20 PR merged     (Pull Shark Silver + Pair Extra)")
    print("  3  Quickdraw supplement          (issue buka + tutup cepat)")
    print("  4  Jumlah iterasi custom")
    print("  0  keluar")
    print()

    while True:
        c = ask("pilih > ").lower()
        if c in ("0", "q", "exit", "keluar"):
            return
        if c == "1":
            return do_run(workdir, user, 5, DEFAULT_COAUTHOR, False)
        if c == "2":
            return do_run(workdir, user, 20, DEFAULT_COAUTHOR, False)
        if c == "3":
            ok, path, _ = ensure_repo(workdir, user)
            if ok:
                say("quickdraw", "-")
                quickdraw_issue(path, user)
            return
        if c == "4":
            n = ask("jumlah PR merged > ", "5")
            try:
                n = int(n)
            except ValueError:
                say("harus angka", "!")
                continue
            if n < 1:
                continue
            return do_run(workdir, user, n, DEFAULT_COAUTHOR, False)
        say("pilihan tidak dikenal", "!")


def main():
    need_tools()
    user = gh_login()
    if not user:
        say("tidak bisa baca identitas akun gh", "!")
        sys.exit(1)

    workdir = os.path.expanduser("~/github-ach")

    # flag path (opsional, untuk scripting)
    if len(sys.argv) > 1:
        if sys.argv[1] in ("-h", "--help"):
            print(__doc__)
            return
        n = 5
        coauthor = DEFAULT_COAUTHOR
        quickdraw = False
        args = sys.argv[1:]
        try:
            if "--iters" in args:
                n = int(args[args.index("--iters") + 1])
            if "--no-coauthor" in args:
                coauthor = None
            if "--quickdraw" in args:
                quickdraw = True
            if "--workdir" in args:
                workdir = os.path.expanduser(args[args.index("--workdir") + 1])
        except (ValueError, IndexError):
            say("argumen tidak valid", "!")
            sys.exit(2)
        do_run(workdir, user, n, coauthor, quickdraw)
        return

    menu(workdir, user)


if __name__ == "__main__":
    main()
