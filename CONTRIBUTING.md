# Contributing to AI SDR Platform

Thanks for working on this project! This guide covers how to get set up and the
workflow for making changes.

## 1. Get set up

1. **Clone** the repo (or add it in GitHub Desktop):
   ```bash
   git clone https://github.com/generativeproducts/AI_SDR.git
   cd AI_SDR
   ```
2. **Create your secrets file** — copy the template and add your own keys.
   This file is gitignored; never commit it.
   ```powershell
   copy secrets.local.ps1.example secrets.local.ps1
   ```
   Fill in `$ApolloKey`, `$HunterApiKey`, `$NeonDbUrl` (blank values fall back to
   public/local mode).
3. **Follow the runbook** for first-time setup: `WINDOWS_RUNBOOK.md` (or
   `MAC_RUNBOOK.md`). Use `RESTART_SERVICES.md` to restart after a reboot.

## 2. Branching

Never commit directly to `main`. Create a branch for every change:

```bash
git checkout main
git pull origin main            # start from the latest code
git checkout -b <type>/<short-description>
```

Branch name examples:
- `feature/zoominfo-provider`
- `fix/contact-dedup`
- `docs/update-readme`

## 3. Make your change

- Keep changes focused — one feature or fix per branch.
- Match the existing code style and patterns in the module you're editing.
- **Do not commit secrets** (API keys, DB passwords) or generated data
  (`.venv/`, `node_modules/`, `*.db`). These are already gitignored — keep it that way.

## 4. Test before you push

```bash
pytest ai_sdr_platform/tests/unit ai_sdr_platform/tests/integration -q
```

For a quick syntax check on files you changed:
```bash
python -m py_compile <path/to/file.py>
```

## 5. Commit and push your branch

```bash
git add .
git commit -m "Short, clear description of the change"
git push -u origin <your-branch-name>
```

(In GitHub Desktop: write a summary, **Commit to <branch>**, then **Push origin**.)

## 6. Open a Pull Request

1. Go to the repo on GitHub → it will prompt **"Compare & pull request"** for your branch.
2. Base branch = `main`, compare = your branch.
3. Write a short description of what changed and why.
4. Request a review, then merge once approved.
5. Delete the branch after merge to keep things tidy.

## 7. Keeping your branch up to date

If `main` moves while you're working:
```bash
git checkout main
git pull origin main
git checkout <your-branch>
git merge main            # resolve any conflicts, commit, continue
```

## Questions

Check the runbooks and `ARCHITECTURE_MULTI_SOURCE_ENRICHMENT.md` first — most
setup and design questions are answered there.
