# gh-achievements — Setup Tool

Script untuk mengejar **GitHub Achievements** secara alami: setiap iterasi adalah
pull request yang benar-benar di-merge dan menambah konten berguna ke repo (changelog
+ catatan), bukan file sampah.

## Achievement yang dihasilkan

| Badge | Pemicu | Level |
|---|---|---|
| **Pull Shark** | PR di-merge | Bronze `2` · Silver `16` · Gold `128` · Purple `1024` |
| **YOLO** | Merge PR tanpa review | Bronze `1` · Gold `2` |
| **Pair Extraordinaire** | Commit `Co-authored-by:` di PR merged | Bronze `1` · Silver `10` · Gold `24` |
| **Quickdraw** | Issue dibuka lalu ditutup **< 5 menit** | Bronze `1` |

Merge PR sendiri (tanpa review) = **Pull Shark + YOLO** sekaligus.
Commit dengan `Co-authored-by:` = **Pair Extraordinaire** otomatis ikut.

## Pakai

```bash
python3 setup.py          # menu interaktif (pintu utama)
```

Menu:

```
1  Setup repo + 5 PR merged   → Pull Shark Bronze + YOLO + Pair Extra
2  Setup repo + 20 PR merged  → Pull Shark Silver + Pair Extra
3  Quickdraw supplement       → issue buka + tutup cepat
4  Jumlah iterasi custom
0  keluar
```

Flag (jalur scripting, opsional):

```bash
python3 setup.py --iters 20
python3 setup.py --iters 5 --quickdraw
python3 setup.py --iters 5 --no-coauthor
python3 setup.py --workdir ~/somewhere
```

## Prasyarat

- `git` dan `gh` terpasang
- `gh auth login` sudah (scope minimal `repo`)

## Cara kerja

1. Buat repo `gh-achievements` (public) di akun gh yang login — atau pakai kalau sudah ada.
2. Per iterasi: branch baru → tambah entri `CHANGELOG.md` → commit (`Co-authored-by` trailer)
   → push → `gh pr create` → `gh pr merge --merge --delete-branch`.
3. Mode quickdraw: `gh issue create` lalu `gh issue close` dalam hitungan detik.

## Batas & etika

- Repo isinya dokumentasi nyata, bukan spam empty commit.
- Jangan jalankan ratusan iterasi sekaligus — GitHub bisa membatasi/menandai akun.
  Naik level bertahap (2 → 16) sudah cukup untuk Bronze/Silver.
- Badge muncul di profil beberapa menit setelah diproses GitHub:
  `https://github.com/<user>?tab=achievements`

## Catatan teknis

- `git commit -m` dengan trailer `Co-authored-by:` digabung dalam satu message (bukan `--amend`,
  karena amend akan menimpa message).
- Trailer diverifikasi ulang lewat `git log -1 --pretty=%B` sebelum push — kalau hilang,
  commit tidak dilanjutkan.
- Semua panggilan eksternal (`git`, `gh`) punya timeout 180 s dan error ditangani, bukan crash.
