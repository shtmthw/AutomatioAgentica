# local/: your own defaults (gitignored)

This folder is yours. Everything in it except this README and the `*.example.*` files is
gitignored, so `git pull` never conflicts with it. With an empty folder the pipeline
behaves exactly like the one behind the @anon14none videos: same voices, same rules.

| file | what it does |
|---|---|
| `voices.toml` | Adds your own voice profiles and makes them the defaults of `new`. Start from [`voices.example.toml`](voices.example.toml). |
| `GUIDELINES.md` | Your standing directions for every video. The agent reads them on top of "Production guidelines" in `AGENTS.md`. Start from [`GUIDELINES.example.md`](GUIDELINES.example.md). |

```bash
cp local/voices.example.toml local/voices.toml          # then edit
cp local/GUIDELINES.example.md local/GUIDELINES.md      # then edit
.venv/bin/python -m automatio doctor                    # shows which overrides are active
```

Rules that still apply:

- The house profiles in `voices.toml` (`hindi-adam`, `english-andrew`, ...) are never
  redefined. Give your voices new names; the loader refuses a clash.
- Once a production is made, its voices are fixed like the house voices. The agent never
  swaps them on its own, and changing them needs a new approval.
- Hard rules stay: approval before paid credits, no burned-in subtitles, nothing cut from
  the script.

Set `AA_LOCAL_DIR` to keep this folder somewhere else.
