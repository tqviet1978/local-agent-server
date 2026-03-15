# Local Agent Server

A lightweight Python server that lets AI agents operate on your local codebase through a simple REST API. Read files, upload code, execute commands, and transfer large files — all through a secure tunnel.

Built for [Claude](https://claude.ai) but works with any AI that can make HTTP requests.

---

## Why?

AI coding assistants like Claude run in the cloud. They can write code, but can't touch your filesystem. You end up copy-pasting files back and forth, running commands manually, and losing context.

**Local Agent Server bridges that gap.** You run it on your machine, expose it through a tunnel (cloudflared/ngrok), and give your AI the URL + token. Now it can:

- Read any file in your repo
- Upload code changes directly
- Run shell commands (tests, git, docker, npm...)
- Transfer large files in chunks with auto-resume

You stay in the conversation. The AI stays in the loop.

---

## Quick Start

### 1. Clone & install

```bash
git clone https://github.com/user/local-agent-server.git
cd local-agent-server
pip install -r requirements.txt
```

### 2. Configure

```bash
cp config.example.json config.json
```

Edit `config.json`:

```json
{
    "host": "0.0.0.0",
    "port": 5100,
    "debug": false,
    "auth_token": "CHANGE_THIS_TO_A_STRONG_TOKEN",
    "repositories": {
        "my-project": {
            "path": "/home/user/projects/my-project"
        },
        "another-repo": {
            "path": "/home/user/projects/another-repo"
        }
    }
}
```

### 3. Expose via tunnel

```bash
# Option A: cloudflared (recommended)
cloudflared tunnel --url http://localhost:5100

# Option B: ngrok
ngrok http 5100
```

### 4. Start the server

```bash
cd src
python app.py
```

### 5. Give your AI the credentials

Tell Claude (or your AI of choice):

> Base URL: `https://your-tunnel-url.trycloudflare.com`
> Token: `your-auth-token`
> Repository: `my-project`

That's it. The AI can now read, write, and execute on your machine.

---

## API Reference

All endpoints require `Authorization: Bearer <token>` header.

### Read File

```
POST /file/read_safe
```

```json
{
    "repository": "my-project",
    "path": "src/main.py",
    "encoding": "utf-8",
    "line_start": 1,
    "line_end": 50
}
```

Read any file with optional line range. Supports `"encoding": "base64"` for binary files.

### Upload File

```
POST /file/upload  (multipart/form-data)
```

| Field | Required | Description |
|-------|----------|-------------|
| `repository` | Yes | Repository code |
| `path` | Yes | Target path in repo |
| `file` | Yes | File to upload |
| `post_cmd` | No | Shell command to run after upload |

Upload a file and optionally run a command afterwards (e.g., unzip, restart service).

### Execute Command

```
POST /command/execute
```

```json
{
    "repository": "my-project",
    "command": "npm test"
}
```

Run any shell command in the repository directory. Returns stdout, stderr, and exit code.

### Chunked Upload (large files)

For files that are too large for a single upload (hundreds of MB to GB+).

```
POST /chunk/init       → Create upload session
POST /chunk/upload     → Send one chunk (multipart)
POST /chunk/status     → Check progress or cancel
POST /chunk/complete   → Merge chunks into final file
```

Each chunk is a small independent HTTP request (~5MB default), safe through tunnels with auto-retry. Supports resume — if the connection drops, query `/chunk/status` to find missing chunks and resend only those.

### Chunked Download (large files)

```
POST /chunk/download   → Download one chunk (base64)
```

No setup call needed. Request `chunk_index: 0` and the response includes `total_chunks`, `total_size`, and `is_last`. Loop until `is_last` is `true`.

---

## Architecture

```
local-agent-server/
├── src/
│   ├── app.py                    # Flask app, auto-registers all routes
│   ├── auth.py                   # Bearer token authentication
│   ├── config.py                 # Repository manager
│   ├── logger.py                 # Request logging
│   ├── routes/
│   │   ├── command/
│   │   │   └── execute.py        # POST /command/execute
│   │   ├── file/
│   │   │   ├── read_safe.py      # POST /file/read_safe
│   │   │   └── upload.py         # POST /file/upload
│   │   └── chunk/
│   │       ├── init.py           # POST /chunk/init
│   │       ├── upload.py         # POST /chunk/upload
│   │       ├── status.py         # POST /chunk/status
│   │       ├── complete.py       # POST /chunk/complete
│   │       └── download.py       # POST /chunk/download
│   └── utils/
│       ├── path_utils.py         # Path sanitization
│       ├── response_utils.py     # Standardized responses
│       ├── post_command_helper.py # Post-upload command execution
│       └── chunk_session.py      # Chunked transfer session manager
├── scripts/
│   ├── bundle.sh                 # Build self-extracting installer
│   ├── install.sh                # Generated installer (after bundle)
│   └── chunk_transfer.sh         # CLI helper for chunked transfer
├── config.json                   # Server configuration
└── requirements.txt
```

Routes are auto-discovered — drop a `.py` file with a `register(app)` function into any `routes/` subdirectory and it's live on the next restart.

---

## Security

> **This server executes arbitrary shell commands on your machine.** Treat the auth token like a root password.

- Always use a strong, random token
- Always use HTTPS tunnels (cloudflared and ngrok do this by default)
- Only expose the server when you need it
- Path traversal is blocked by `get_safe_path()` — all file operations are sandboxed within configured repository directories
- No data is sent to any third party; everything stays between your machine and the tunnel

---

## One-Line Remote Install

If you run `bash scripts/bundle.sh`, it generates a self-extracting `install.sh`. You can then install on another machine with:

```bash
curl -sSL https://your-tunnel-url/install | sudo bash
```

---

## Use with Claude

This server was designed as a companion for Claude's web chat. A [Claude Skill file](https://docs.anthropic.com/en/docs/build-with-claude/prompt-engineering) is included that teaches Claude how to use every endpoint — read files, upload code, run tests, and handle large file transfers automatically.

See `SKILL.md` for the full integration guide.

---

## Contributing

Contributions are welcome. Please open an issue first to discuss what you'd like to change.

---

## License

MIT
