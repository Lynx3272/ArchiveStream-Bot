"""GitHub entegrasyonu: otomatik add/commit/push, PAT kimlik dogrulama, repo olusturma, builds dali."""
import json

import requests

from bot import logger, config


def _ensure_gitignore_safety():
    """Self-healing guvence: .git-pat dosyasi gitignore'da degilse otomatik ekle."""
    gi = config.BASE_DIR / ".gitignore"
    current = gi.read_text(encoding="utf-8") if gi.exists() else ""
    if ".git-pat" not in current:
        with open(gi, "a", encoding="utf-8") as f:
            if current and not current.endswith("\n"):
                f.write("\n")
            f.write(".git-pat\n")
        logger.heal("[SELF-HEAL] .git-pat .gitignore'a otomatik eklendi (token sizi kaydi).")


def _ensure_builds_branch(repo):
    """Actions'in .cs3 dosyalarini yukledigi 'builds' dali yoksa bos olarak olusturur (calisma dizinine dokunmadan)."""
    heads = repo.git.ls_remote("--heads", "origin").splitlines() if repo.remotes else []
    if any(ref.endswith("/builds") for ref in heads):
        return
    empty_tree = repo.git.mktree(_stdin="")
    commit = repo.git.commit_tree(empty_tree, m="builds dali baslatildi")
    repo.git.update_ref("refs/heads/builds", commit)
    logger.ok("builds dali olusturuldu (derleme ciktilari buraya yuklenecek)")


def _create_repo(pat: str, user: str, repo: str, private: bool):
    """Repo yoksa GitHub API ile olusturur. Zaten varsa sessiz gecer."""
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
        json={"name": repo, "private": private, "description": "ArchiveStream Otonom Bot - kamu mali icerik eklentisi"},
        timeout=20,
    )
    if r2.status_code in (201, 422):  # 422 = zaten var
        logger.ok(f"Repo hazir: {user}/{repo} ({'OZEL' if private else 'HERKESE ACIK'})")
    else:
        raise RuntimeError(f"Repo olusturulamadi: {r2.status_code} {r2.text[:200]}")


def _validate_pat(pat: str) -> bool:
    r = requests.get("https://api.github.com/user", headers={"Authorization": f"token {pat}"}, timeout=20)
    return r.status_code == 200


def _get_valid_pat() -> str:
    """PAT'i dogrular; gecersizse silip yeniden ister (self-healing)."""
    for _ in range(3):
        pat = config.get_pat()
        if _validate_pat(pat):
            return pat
        logger.heal("[SELF-HEAL] GitHub tokeni gecersiz (401). Kaydedilen token silindi, tekrar soruluyor.")
        config.PAT_FILE.unlink(missing_ok=True)
    raise RuntimeError("GitHub tokeni 3 denemede de gecerli olmadı. Tokeni tam kopyaladigindan emin ol (ghp_ ile baslar, bosluk icermemeli).")


def push_all(commit_message: str) -> str | None:
    """Tum degisiklikleri GitHub'a push eder. Basarida repo adresini dondurur."""
    import git as gitpython

    repo = gitpython.Repo(config.BASE_DIR)
    _ensure_gitignore_safety()

    pat = _get_valid_pat()
    settings = config.load_settings()
    user, repo_name = settings.get("git_user"), settings.get("git_repo")
    if not user or not repo_name:
        logger.info("GitHub kullanici adi ve repo adi gerekiyor (ilk calistirma).")
        user = input("GitHub kullanici adi: ").strip()
        repo_name = input("Repo adi [ArchiveStream-Bot]: ").strip() or "ArchiveStream-Bot"
        settings["git_user"], settings["git_repo"] = user, repo_name
        config.save_settings(settings)

    # CloudStream raw.githubusercontent uzerinden eklentiyi ceker; ozel repoda calismaz.
    public = bool(settings.get("repo_public", True))
    if not public:
        logger.warn(
            "Depo OZEL olacak: CloudStream 'Depo Ekle' linki calismaz. "
            "APK'yi manuel indirmen gerekir (Actions > Build > artifact). "
            "settings.json'da 'repo_public': true yaparak otomatik modu acabilirsin."
        )

    logger.git(f"Repo kontrol ediliyor: {user}/{repo_name}")
    _create_repo(pat, user, repo_name, private=not public)

    from bot import providers_gen
    providers_gen.update_repo_links(user, repo_name)
    _ensure_builds_branch(repo)

    repo.git.add(A=True)
    diff = repo.git.diff("--cached", "--stat")
    if diff.strip():
        identity = repo.config_reader()
        has_email = bool(identity.get_value("user", "email", fallback=""))
        if not has_email:
            with repo.config_writer() as cw:
                cw.set_value("user", "name", user)
                cw.set_value("user", "email", f"{user}@users.noreply.github.com")
        repo.git.commit(m=commit_message)
        logger.git(f"Commit olusturuldu: {commit_message}")
    else:
        logger.git("Yeni degisiklik yok, commit atlandi.")

    # Token URL'e konur ama config'e yazilmaz, loglanmaz
    remote_url = f"https://{user}:{pat}@github.com/{user}/{repo_name}.git"
    repo.git.push(remote_url, "HEAD:refs/heads/main")
    repo.git.push(remote_url, "refs/heads/builds:refs/heads/builds")
    logger.ok(f"GitHub'a yuklendi: https://github.com/{user}/{repo_name}")

    repo_url = f"https://raw.githubusercontent.com/{user}/{repo_name}/main/repo.json"
    logger.ok(f"CloudStream 'Depo Ekle' linki: {repo_url}")
    return repo_url
