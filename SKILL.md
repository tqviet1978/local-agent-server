---
name: local-agent-api
description: Use this skill whenever the user wants Claude to work directly on their local system — reading files, uploading code, running commands, managing services, or performing any operation on a remote codebase via the Local Agent API. Trigger this skill when the user mentions a repository code/ID, asks Claude to deploy, test, or run something on their machine, or when any workflow involves reading from or writing to a local codebase through an API. This skill is essential for end-to-end coding workflows where Claude should autonomously code, upload, test, and fix — without the user needing to copy-paste anything manually.
---

# Local Agent API Skill

This skill enables Claude to operate autonomously on the user's local system via a deployed API server. Claude can read files, upload code, execute shell commands, manage services, and run full dev workflows — all without the user touching their machine.

---

## Setup (ask user if not provided)

Before starting, confirm these values:

| Parameter | Example | Description |
|-----------|---------|-------------|
| `REPO` | `crypto-alerts` | Repository code/ID (lowercase) |
| `BASE_URL` | `https://local-agent-server.vietml.com` | API base URL |
| `TOKEN` | `las@54321` | Bearer token |

Store these mentally for the entire session. Use them in every API call.

---

## Core Rules

1. **Always propose plan first** — explain what you'll do, then wait for user confirmation before executing
2. **Never edit files directly on the codebase** — always develop locally in `/home/claude` first, then upload
3. **4-space indentation always** — never use tabs
4. **TLS errors** — retry silently using `--retry 5 --retry-delay 3`, never notify the user unless all retries fail
5. **Match existing code style** — read surrounding files before writing new ones

---

## API Reference

### API 1 — Read File
```bash
curl -s --retry 5 --retry-delay 3 -X POST $BASE_URL/file/read_safe \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "repository": "$REPO",
    "path": "path/to/file",
    "encoding": "utf-8",
    "line_start": 1,
    "line_end": 100
  }'
```
- Use `"encoding": "base64"` for binary files
- `line_start` / `line_end` are optional — omit to read entire file

### API 2 — Upload File
```bash
curl --retry 5 --retry-delay 3 -X POST $BASE_URL/file/upload \
  -H "Authorization: Bearer $TOKEN" \
  -F "repository=$REPO" \
  -F "path=target/path/file.py" \
  -F "file=@/home/claude/file.py" \
  -F "post_cmd=optional shell command after upload"
```
- `post_cmd` is optional — use for post-upload operations (unzip, move, restart service, etc.)
- For **4+ files**: zip them → upload zip → unzip via `post_cmd`

```bash
# Multiple files example
cd /home/claude
zip -r changes.zip file1.py file2.py config.yaml
curl --retry 5 --retry-delay 3 -X POST $BASE_URL/file/upload \
  -H "Authorization: Bearer $TOKEN" \
  -F "repository=$REPO" \
  -F "path=changes.zip" \
  -F "file=@changes.zip" \
  -F "post_cmd=unzip -o changes.zip && mv file1.py src/ && mv file2.py src/ && mv config.yaml config/ && rm changes.zip"
```

### API 3 — Execute Command
```bash
curl -s --retry 5 --retry-delay 3 -X POST $BASE_URL/command/execute \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "repository": "$REPO",
    "command": "shell command here"
  }'
```
Use for: git, npm, pip, docker, pytest, service management, file inspection, logs, etc.

### API 4 — Chunked Upload (large files)

For files too large for a single API 2 call (hundreds of MB to GB+). Splits into small chunks, each sent as an independent HTTP request — safe through cloudflared tunnels, supports resume on failure.

**Step 1: Init session**
```bash
curl -s --retry 5 --retry-delay 3 -X POST $BASE_URL/chunk/init \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "repository": "$REPO",
    "path": "target/path/bigfile.zip",
    "total_size": 524288000,
    "chunk_size": 5242880,
    "filename": "bigfile.zip"
  }'
```
- `total_size`: exact file size in bytes (required)
- `chunk_size`: bytes per chunk (optional, default 5MB = 5242880)
- Returns `session_id` and `total_chunks`

**Step 2: Upload chunks — pipe directly from source file, no temp files**
```bash
# Use dd to read exact byte range → pipe straight into curl
dd if=/home/claude/bigfile.zip bs=5242880 skip=$CHUNK_INDEX count=1 2>/dev/null | \
  curl -s --retry 5 --retry-delay 3 -X POST $BASE_URL/chunk/upload \
    -H "Authorization: Bearer $TOKEN" \
    -F "session_id=$SESSION_ID" \
    -F "chunk_index=$CHUNK_INDEX" \
    -F "file=@-;filename=chunk_$CHUNK_INDEX"
```
- `chunk_index`: 0-based
- Idempotent — re-uploading same index overwrites safely
- Returns `received_chunks`, `total_chunks`, `percent`

**Step 2b (optional): Check progress / resume after failure**
```bash
curl -s --retry 5 --retry-delay 3 -X POST $BASE_URL/chunk/status \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"session_id": "$SESSION_ID"}'
```
- Returns `missing_chunks` array — only resend those
- Use `"action": "cancel"` to abort and cleanup

**Step 3: Complete — merge all chunks into final file**
```bash
curl -s --retry 5 --retry-delay 3 -X POST $BASE_URL/chunk/complete \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "session_id": "$SESSION_ID",
    "post_cmd": "optional command after merge"
  }'
```
- `post_cmd` works the same as API 2 (unzip, restart, etc.)
- Returns final `size`

**Full upload loop example (bash):**
```bash
FILE="/home/claude/bigfile.zip"
FILE_SIZE=$(stat -c%s "$FILE")
CHUNK_SIZE=5242880

# Init
INIT=$(curl -s --retry 5 --retry-delay 3 -X POST $BASE_URL/chunk/init \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d "{\"repository\":\"$REPO\",\"path\":\"data/bigfile.zip\",\"total_size\":$FILE_SIZE,\"chunk_size\":$CHUNK_SIZE}")

SESSION_ID=$(echo "$INIT" | jq -r '.data.session_id')
TOTAL=$(echo "$INIT" | jq -r '.data.total_chunks')

# Upload chunks
for ((i=0; i<TOTAL; i++)); do
  dd if="$FILE" bs=$CHUNK_SIZE skip=$i count=1 2>/dev/null | \
    curl -s --retry 5 --retry-delay 3 -X POST $BASE_URL/chunk/upload \
      -H "Authorization: Bearer $TOKEN" \
      -F "session_id=$SESSION_ID" \
      -F "chunk_index=$i" \
      -F "file=@-;filename=chunk_$i"
done

# Complete
curl -s --retry 5 --retry-delay 3 -X POST $BASE_URL/chunk/complete \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d "{\"session_id\":\"$SESSION_ID\"}"
```

### API 5 — Chunked Download (large files)

Download a large file chunk by chunk. No separate info call needed — the first chunk response includes all metadata.

```bash
curl -s --retry 5 --retry-delay 3 -X POST $BASE_URL/chunk/download \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "repository": "$REPO",
    "path": "path/to/bigfile.zip",
    "chunk_index": 0,
    "chunk_size": 5242880
  }'
```
- `chunk_index`: 0-based (required)
- `chunk_size`: optional, default 5MB
- Returns base64-encoded chunk + `total_chunks`, `total_size`, `is_last`
- Loop from index 0 until `is_last` is `true`

**Full download loop example (bash):**
```bash
OUTPUT="/home/claude/downloaded.zip"
> "$OUTPUT"

i=0
while true; do
  RESP=$(curl -s --retry 5 --retry-delay 3 -X POST $BASE_URL/chunk/download \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer $TOKEN" \
    -d "{\"repository\":\"$REPO\",\"path\":\"data/bigfile.zip\",\"chunk_index\":$i,\"chunk_size\":5242880}")

  echo "$RESP" | jq -r '.data.content' | base64 -d >> "$OUTPUT"

  IS_LAST=$(echo "$RESP" | jq -r '.data.is_last')
  [[ "$IS_LAST" == "true" ]] && break
  ((i++))
done
```

---

## Decision: Which API to Use?

| Task | API |
|------|-----|
| Read a file | API 1 (or API 3 with `cat`) |
| Upload 1–3 small files (< 50MB each) | API 2 (one call per file) |
| Upload 4+ small files | API 2 with zip |
| Upload large file (50MB+) | API 4 (chunked upload) |
| Download large file (50MB+) | API 5 (chunked download) |
| Run git / npm / docker / tests | API 3 |
| Check logs / service status | API 3 |
| Restart a service | API 3 or API 2 with `post_cmd` |

---

## Standard Workflow

```
1. ANALYZE    → Understand request, propose solution, ask clarifying questions
               → WAIT for user confirmation before proceeding

2. READ       → Use API 1 or API 3 to explore codebase structure
               → Read relevant files to understand patterns and style

3. DEVELOP    → Write code locally in /home/claude
               → Use 4-space indentation
               → Match existing code style
               → Verify syntax before uploading

4. UPLOAD     → Single file: API 2
               → Multiple files (4+): zip → API 2 → unzip via post_cmd
               → Large file (50MB+): API 4 (chunked upload)

5. TEST       → Use API 3 to run tests, start services, check output
               → Read logs if needed

6. FIX        → If errors: loop back to step 3
               → Repeat until tests pass

7. REPORT     → Summarize what was done, what changed, test results
```

---

## Error Handling

| Error type | Action |
|------------|--------|
| TLS / connection error | Auto-retry silently (`--retry 5 --retry-delay 3`) |
| API error after all retries | Notify user with error details |
| Syntax error in code | Fix locally, re-upload |
| Test failure | Analyze output, fix, loop |
| Unclear repo structure | Read more files before proceeding |
| Chunked upload interrupted | Call `/chunk/status` to get `missing_chunks`, resend only those |

---

## Exploration Commands

Use API 3 to explore the codebase when needed:

```bash
# List directory structure
"command": "find . -type f -name '*.py' | head -50"

# Read package.json or requirements
"command": "cat package.json"
"command": "cat requirements.txt"

# Check git status
"command": "git status && git log --oneline -10"

# Check running services
"command": "pm2 list"  # or systemctl, docker ps, etc.

# Check recent logs
"command": "tail -100 logs/app.log"
```

---

## Best Practices

- **Explore before coding** — always read relevant files first to avoid style mismatches
- **Small targeted changes** — prefer minimal diffs over full rewrites
- **Verify before upload** — mentally check syntax and logic
- **Test after every upload** — don't assume it works
- **Use `post_cmd` wisely** — can chain multiple commands with `&&`
- **Keep user informed** — brief status updates at each phase (reading... uploading... testing...)
- **Use chunked transfer for large files** — API 2 works for files under ~50MB; for anything larger, use API 4/5 to avoid timeout and memory issues through cloudflared
