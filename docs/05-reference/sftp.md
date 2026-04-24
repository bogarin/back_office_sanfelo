# SFTP File Serving via Nginx X-Accel-Redirect

**Author:** Backoffice Trámites Team
**Status:** Implemented
**Date:** 2026-04-22

---

## Overview

This document describes the architecture for serving PDF files from a remote SFTP server to Django admin users. The system uses **Nginx X-Accel-Redirect** to offload file transfer from Django while maintaining authentication and authorization in the application layer.

### Why X-Accel-Redirect?

For files ranging from 10-50 MB, serving them directly through Django would tie up a gunicorn worker for the entire download duration. With X-Accel-Redirect:

1. Django authenticates and authorizes the request
2. Django downloads the file from SFTP to a local cache (if needed)
3. Django returns an empty response with an `X-Accel-Redirect` header pointing to the cached file
4. Nginx intercepts this header and serves the file directly from disk
5. Django worker is freed immediately — no blocking

This architecture provides:
- **Performance:** Nginx handles file I/O efficiently
- **Scalability:** Multiple simultaneous downloads don't exhaust Django workers
- **Security:** Django controls all access decisions; Nginx only serves files
- **Reliability:** Django workers stay available for API requests

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│  Browser                                                      │
│     │                                                        │
│     ▼                                                        │
│     GET /admin/tramites/tramite/123/download/            │
│          DAU-260420-AAAE-B-19.pdf                         │
└─────────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  Docker Container (port 8080)                                 │
│  ┌────────────────────────────────────────────────────────────┐   │
│  │  nginx (0.0.0.0:8080)                       │   │
│  │     ├── /static/* → /app/staticfiles/              │   │
│  │     ├── /sftp-files/* → /app/.sftp_cache/         │   │
│  │     │         (internal, X-Accel-Redirect target)   │   │
│  │     └── /* → proxy_pass → gunicorn             │   │
│  │                                                 │   │
│  └────────────────────────────────────────────────────────────┘   │
│       │                                            │   │
│       ▼                                            │   │
│  ┌────────────────────────────────────────────────────┐   │
│  │  gunicorn (127.0.0.1:8081)              │   │
│  │     └── Django application (port 8081)       │   │
│  └────────────────────────────────────────────────────┘   │
│       │                                            │
│       ▼                                            │
│  ┌────────────────────────────────────────────────────┐   │
│  │  SFTP Service                                    │   │
│  │    ├── Connection caching (thread-local)           │   │
│  │    ├── Validation (folio, filename)            │   │
│  │    └── Download + local cache               │   │
│  └────────────────────────────────────────────────────┘   │
│       ▼                                            │
│  ┌────────────────────────────────────────────────────┐   │
│  │  Remote SFTP Server                          │   │
│  │    /base_dir/{folio}/{filename}.pdf             │   │
│  └────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## File Download Flow

### Cache Hit (File Already Downloaded)

```
User clicks download link
    ↓
Django view: download_requisito_pdf()
    ↓
1. Authenticate user (must be logged in)
    ↓
2. Check permissions (object-level: assigned or unassigned)
    ↓
3. Validate filename (regex + forbidden chars)
    ↓
4. Validate filename belongs to this tramite's folio
    ↓
5. Check cache: /app/.sftp_cache/{folio}/{filename} exists + fresh (< TTL)
    ↓
CACHE HIT → return X-Accel-Redirect header
    ↓
Nginx serves /app/.sftp_cache/{folio}/{filename}
    ↓
Browser receives file
```

### Cache Miss (First Download)

```
User clicks download link
    ↓
Django view: download_requisito_pdf()
    ↓
1-4. Same as cache hit
    ↓
5. Check cache: file doesn't exist OR expired (> TTL)
    ↓
CACHE MISS → SFTP download
    ↓
6. Open SFTP connection (reused if alive)
    ↓
7. Check file size on SFTP server (< 50 MB)
    ↓
8. Stream download to unique temp file: .{filename}.{pid}.{uuid}.tmp
    ↓
9. Atomic rename: temp → /app/.sftp_cache/{folio}/{filename}
    ↓
10. Close SFTP connection
    ↓
return X-Accel-Redirect header
    ↓
Nginx serves file from cache
    ↓
Browser receives file
```

---

## Security Measures

### Authentication & Authorization

| Layer | Mechanism | Details |
|--------|------------|---------|
| **Django** | Session-based authentication | User must be logged in to access any URL |
| **Django** | Object-level authorization | Download view implements role-based access control mirroring admin queryset rules |
| **Django** | URL pattern validation | `<str:filename>` prevents `/` in URL path |

### Authorization Rules

| Role | Can Download | Details |
|-------|--------------|---------|
| Superuser | All trámites | Full access |
| Administrador | All trámites | Full access (has `is_staff=True`) |
| Coordinador | All trámites | Full access to all trámites for reassignment |
| Analista | Assigned + Unassigned | Only trámites assigned to them OR unassigned trámites |
| Other | None | Access denied |

**Note:** Authorization is checked at the tramite object level. An analista cannot download files from a tramite they were never assigned to, even if they know the primary key.

### Input Validation

| Input | Validation | Purpose |
|--------|-------------|---------|
| **Folio** | Regex + forbidden chars | Prevents path traversal and injection in directory path |
| **Filename** | Regex + forbidden chars | Prevents path traversal and injection in filename |
| **Tramite PK** | `get_object_or_404()` | Prevents enumeration of non-existent trámites |

**Folio validation:**
- Regex: `^[A-Z]+-\d{6}-[A-Z]{4}-[A-Z]$`
- Forbidden characters: `/\x00` (slash, null byte)
- No relative paths, no `..`, no control characters

**Filename validation:**
- Regex: `^[A-Z]+-\d{6}-[A-Z]{4}-[A-Z]-(?P<requisito_id>\d+)\.pdf$`
- Forbidden characters: `/\x00` (slash, null byte)
- Must start with tramite's folio: validates filename belongs to this tramite

### Nginx Security

| Feature | Configuration | Purpose |
|---------|---------------|---------|
| **Internal location** | `internal` directive | Prevents direct browser access to `/sftp-files/` |
| **Regex location** | Pattern match | Only serves files matching exact filename format |
| **Process isolation** | `appuser` | All processes run as non-root user (UID 1000) |
| **Temp paths** | `/tmp/*` | nginx temp files isolated from application data |

**Nginx location for SFTP files:**
```nginx
location ~* ^/sftp-files/[^/]+/[A-Z]+-\d{6}-[A-Z]{4}-[A-Z]-\d+\.pdf$ {
    internal;
    alias /app/.sftp_cache/;
}
```

This location:
1. Matches only the exact filename format (prevents path traversal at nginx level)
2. Uses `internal` directive (only accessible via X-Accel-Redirect from Django)
3. Cannot be accessed directly from browsers even if filename is guessed

### Cache Management

| Setting | Default | Description |
|----------|---------|-------------|
| `SFTP_FILE_CACHE_DIR` | `/app/.sftp_cache` | Local directory for cached PDFs |
| `SFTP_FILE_CACHE_TTL_SECONDS` | 3600 | Cache validity period (1 hour) |
| `SFTP_FILE_CACHE_MAX_SIZE_MB` | 500 | Maximum total cache size (enforced by cleanup command) |

**Cache lifecycle:**
1. Files are downloaded on first access
2. Files are served from cache until TTL expires (1 hour)
3. Expired files are re-downloaded from SFTP on next access
4. Cleanup command removes files older than TTL and enforces size limit

**Unique temp file names:**
```
/app/.sftp_cache/{folio}/.{filename}.{pid}.{uuid8}.tmp
```
This prevents race conditions when multiple users download the same file simultaneously.

### Rate Limiting

| Endpoint | Limit | Purpose |
|----------|-------|---------|
| `/admin/tramites/tramite/` | 10 req/min (burst 20) | Prevents DoS via rapid downloads |

Nginx enforces this limit before requests reach Django.

### Audit Logging

All download attempts are logged with:

```python
logger.info(
    'Descarga PDF: user=%s (id=%s), tramite=%s (folio=%s), filename=%s, ip=%s',
    request.user.username,
    request.user.id,
    tramite.pk,
    tramite.folio,
    filename,
    request.META.get('HTTP_X_REAL_IP', request.META.get('REMOTE_ADDR')),
)
```

This provides:
- **Accountability:** Who downloaded what and when
- **Forensics:** IP address of downloader
- **Compliance:** Audit trail for government records

### File Size Limits

| Limit | Value | Enforced at |
|--------|-------|--------------|
| Max download size | 50 MB | Django: SFTP `stat()` check |
| Max request body | 50 MB | Nginx: `client_max_body_size` |
| Max cache size | 500 MB | Cleanup command |

---

## Configuration

### Environment Variables

| Variable | Required | Default | Description |
|----------|-----------|---------|-------------|
| `SFTP_FILE_CACHE_DIR` | No | `/app/.sftp_cache` | Local cache directory path |
| `SFTP_FILE_CACHE_TTL_SECONDS` | No | 3600 | Cache TTL in seconds (1 hour) |
| `SFTP_FILE_CACHE_MAX_SIZE_MB` | No | 500 | Maximum cache directory size |

### Settings File

Configuration is added to `sanfelipe/settings/sftp.py`:

```python
'SFTP_FILE_CACHE_DIR': env.path(
    'SFTP_FILE_CACHE_DIR',
    default='/app/.sftp_cache',
    is_path=True,
),
'SFTP_FILE_CACHE_TTL_SECONDS': env.int(
    'SFTP_FILE_CACHE_TTL_SECONDS',
    default=3600,
),
'SFTP_FILE_CACHE_MAX_SIZE_MB': env.int(
    'SFTP_FILE_CACHE_MAX_SIZE_MB',
    default=500,
),
```

---

## Docker Setup

### Single Container Architecture

The application runs in a single Docker container with nginx and gunicorn managed by an entrypoint script:

**Process hierarchy:**
- **nginx:** Main process, binds to `0.0.0.0:8080` (public port)
- **gunicorn:** Backend, binds to `127.0.0.1:8081` (localhost only)
- **appuser:** All processes run as UID 1000 (non-root)

**Why single container?**
- Simpler deployment: one image to build and deploy
- Easier monitoring: single container, single health check
- Reduced attack surface: no exposed gunicorn port

### Entrypoint Script

The `docker/entrypoint.sh` script:

1. **Root guard:** Checks that container is NOT running as root
2. **Starts nginx** in background
3. **Starts gunicorn** in foreground (PID 1 for signal handling)
4. **Monitors processes:** Detects if either process dies
5. **Signal handling:** Graceful shutdown on SIGTERM/SIGINT
6. **Cleanup:** Kills both processes and exits if one dies

**Signal flow:**
```
SIGTERM received
    ↓
1. Send SIGTERM to nginx (graceful: `nginx -s quit`)
    ↓
2. Send SIGTERM to gunicorn
    ↓
3. Wait for both processes to exit (with timeout)
    ↓
4. Force kill if timeout (SIGKILL)
    ↓
Container exits
```

### Nginx Configuration

**Main features:**
- Serves static files directly (offloads Django)
- Serves cached SFTP files via X-Accel-Redirect
- Proxies all other requests to gunicorn
- Rate limiting on admin tramite URLs
- Security headers on SFTP file responses

**Key directives:**
```nginx
worker_processes 1;
client_max_body_size 50m;
sendfile on;

# Rate limiting
limit_req_zone $binary_remote_addr zone=download:10m rate=10r/m;

location /admin/tramites/tramite/ {
    limit_req zone=download burst=20 nodelay;
    proxy_pass http://gunicorn;
    # ... proxy headers ...
}

location /sftp-files/ {
    internal;  # ← Prevents direct access
    alias /app/.sftp_cache/;
    add_header X-Content-Type-Options nosniff always;
    add_header X-Frame-Options DENY always;
}
```

### Health Check

The `docker/healthcheck.py` script verifies:

1. **Nginx is running:** Process check or HTTP request to nginx
2. **Django is responding:** Request to `/health/` endpoint through nginx

The `/health/` endpoint (defined in `core/views.py`) checks:
- Database connectivity
- Django application health
- Returns HTTP 200 if healthy

**Note:** SFTP connectivity is NOT checked in health check. If the SFTP server is down, the application remains healthy but file downloads will fail gracefully with user-friendly error messages.

---

## Performance Considerations

### Connection Reuse

SFTP connections are cached per-thread:
- First request: Opens new SFTP connection
- Subsequent requests: Reuses existing connection (if alive)
- Connection lifecycle: Automatically closed on thread exit

This reduces connection overhead for multiple downloads within the same user session.

### Streaming Downloads

Files are downloaded in chunks (64 KB) from SFTP to minimize memory usage:
```python
while chunk := remote.read(65536):
    local.write(chunk)
```

This allows downloading large files (50 MB) without loading entire file into RAM.

### Cache Performance

| Scenario | Behavior |
|----------|-----------|
| **First download** | SFTP fetch + cache write + serve (slowest) |
| **Subsequent downloads** | Cache hit + nginx serve (fastest) |
| **Expired cache** | SFTP re-fetch + cache overwrite + serve (medium) |

For a tramite with 10 PDF files, after the first user downloads all files:
- **Initial access:** ~10 SFTP fetches
- **Subsequent users:** ~10 cache hits (near-instant)

### Worker Availability

Since Django workers are freed immediately after returning X-Accel-Redirect:
- Workers are available for API requests (admin actions, data updates)
- Concurrent downloads don't block workers
- Nginx handles file I/O efficiently

---

## Troubleshooting

### Files Not Downloading

**Symptom:** User clicks download link, browser shows error or hangs.

**Diagnosis steps:**
1. Check Django logs: Look for `SFTPConnectionError` messages
2. Check SFTP settings: Verify `SFTP_HOST`, `SFTP_USERNAME`, `SFTP_HOST_KEY`
3. Check Nginx logs: Look for errors in `/var/log/nginx/error.log`
4. Check cache directory: Verify `/app/.sftp_cache` is writable by appuser
5. Test SFTP manually: Run `python manage.py sftp ping`

**Common causes:**
- SFTP server unreachable (firewall, network issue)
- Wrong SSH key format in `SFTP_HOST_KEY`
- Filename doesn't match expected format
- Folio directory doesn't exist on SFTP server

### Cache Not Working

**Symptom:** Files are re-downloaded from SFTP on every request.

**Diagnosis:**
1. Check `SFTP_FILE_CACHE_DIR` setting: Ensure path is correct
2. Check cache directory permissions: `ls -la /app/.sftp_cache`
3. Check file permissions: Cached files must be readable by appuser
4. Verify TTL: Check `SFTP_FILE_CACHE_TTL_SECONDS` value

**Fix:**
```bash
# In container
rm -rf /app/.sftp_cache/*
```

### High Memory Usage

**Symptom:** Container OOM killed.

**Diagnosis steps:**
1. Check gunicorn worker count: 4 workers × 2 threads = 8 Python threads
2. Check file size: Large PDFs being downloaded simultaneously
3. Check nginx buffers: Default buffer sizes may be too high

**Fixes:**
- Reduce gunicorn workers: `--workers 2 --threads 4`
- Increase Docker memory limit in docker-compose.yml
- Tune nginx buffers: `client_body_buffer_size`, `proxy_buffer_size`

---

## File Structure

```
/home/nnieto/Code/SF/backoffice_tramites/
├── docker/
│   ├── entrypoint.sh          # Process manager for nginx + gunicorn
│   └── healthcheck.py         # Health check script
├── nginx/
│   └── nginx.conf            # Nginx configuration
├── sanfelipe/
│   └── settings/
│       └── sftp.py            # SFTP settings (includes cache config)
├── templates/
│   └── admin/
│       └── tramite_detail.html  # Updated with download links
├── tramites/
│   ├── admin.py                # Updated TramiteBaseAdmin change_view
│   ├── constants.py             # Added FILENAME_REGEX
│   ├── services.py              # Added download_file(), _validate_filename()
│   ├── urls.py                 # Added download URL
│   └── views.py                # New: download_requisito_pdf()
├── core/
│   └── management/
│       └── commands/
│           └── sftp.py       # Added cleanup_cache subcommand
└── Dockerfile                     # Added nginx, cache dir, entrypoint
```

---

## Related Documentation

- [SFTP Host Key Setup](./sftp-host-key.md) — Configuration for SFTP server verification
- [SFTP CLI Commands](../README.md#management-commands) — `sftp ping`, `sftp list`, `sftp cleanup_cache`
- [Django Settings](../sanfelipe/settings/README.md) — Full settings reference
