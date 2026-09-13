"""GitHub entegrasyonu: otomatik add/commit/push, PAT kimlik dogrulama, ozel repo olusturma."""
import json

import requests

from bot import logger, config


def _ensure_gitignore_safety(repo):
    """Self-healing guvence: .git-pat dosyasi gitignore'da degilse otomatik ekle."""
    gi = config.BASE_DIR / ".gitignore"
    current = gi.read_text(encoding="utf-8") if gi.exists() else ""
    if ".git-pat" not in current:
        with open(gi, "a", encoding="utf-8") as f:
            if current and not current.endswith("\n"):
                f.write("\n")
            f.write(".git-pat\n")
        logger.heal("[SELF-HEAL] .git-pat .gitignore'a otomatik eklendi (token sizi kaydi).")


def _create_private_repo(pat: str, user: str, repo: str):
    """Ozel repo yoksa GitHub API ile olusturur. Zaten varsa sessiz gecer."""
    r = requests.get(
        f"https://api.github.com/repos/{user}/{repo}",
        headers={"Authorization": f"token {pat}"},
        timeout=20,
    )
    if r.status_code == 200:
        logger.git(f"Repo zaten mevcut: {user}/{repo}")
        return
    r2 = requests.post(
        "https://api.github.com/user/repos",
        headers={"Authorization": f"token {pat}", "Accept": "application/vnd.github+json"},
        json={"name": repo, "private": True, "description": "ArchiveStream Otonom Bot - otomatik link guncellemeleri"},
        timeout=20,
    )
    if r2.status_code in (201, 422):  # 422 = zaten var
        logger.ok(f"Ozel repo hazir: {user}/{repo} (Private)")
    else:
        raise RuntimeError(f"Repo olusturulamadi: {r2.status_code} {r2.text[:200]}")


def push_all(commit_message: str):
    """Tum degisiklikleri ozel GitHub reposuna push eder. PAT yoksa/kullanici iptal ederse False doner."""
    import git as gitpython

    repo = gitpython.Repo(config.BASE_DIR)
    _ensure_gitignore_safety(repo)

    pat = config.get_pat()
    settings = config.load_settings()
    user, repo_name = settings.get("git_user"), settings.get("git_repo")
    if not user or not repo_name:
        logger.info("GitHub kullanici adi ve repo adi gerekiyor (ilk calistirma).")
        user = input("GitHub kullanici adi: ").strip()
        repo_name = input("Repo adi [ArchiveStream-Bot]: ").strip() or "ArchiveStream-Bot"
        settings["git_user"], settings["git_repo"] = user, repo_name
        config.save_settings(settings)

    logger.git(f"Ozel repo kontrol ediliyor: {user}/{repo_name}")
    _create_private_repo(pat, user, repo_name)

    repo.git.add(A=True)
    diff = repo.git.diff("--cached", "--stat")
    if not diff.strip():
        logger.git("Yeni degisiklik yok, commit atlandi.")
        return True

    identity = repo.config_reader()
    has_email = bool(identity.get_value("user", "email", fallback=""))
    if not has_email:
        with repo.config_writer() as cw:
            cw.set_value("user", "name", user)
            cw.set_value("user", "email", f"{user}@users.noreply.github.com")

    repo.git.commit(m=commit_message)
    logger.git(f"Commit olusturuldu: {commit_message}")

    # Token URL'e konur ama config'e yazilmaz, loglanmaz
    remote_url = f"https://{user}:{pat}@github.com/{user}/{repo_name}.git"
    repo.git.push(remote_url, "HEAD:refs/heads/main", "--force-with-lease=main")
    logger.ok(f"GitHub'a yuklendi: https://github.com/{user}/{repo_name} (Private)")
    return True
