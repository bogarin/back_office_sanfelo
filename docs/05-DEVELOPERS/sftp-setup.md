# SFTP Host Key Verification

## What is a host key?

An SSH host key is the server's public key fingerprint. When your Django app
connects to the SFTP server, it verifies the server's identity using this key.
This prevents **Man-in-the-Middle (MITM) attacks** where an attacker intercepts
the connection to steal credentials or data.

Without host key verification, your app trusts **any** server that responds --
even an impostor.

## How to obtain the host key

From any machine that can reach the SFTP server:

```bash
# Get all key types:
ssh-keyscan -t rsa,ed25519,ecdsa-sha2-nistp256 your-sftp-server.com

# Example output:
# your-sftp-server.com ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABgQC7...
# your-sftp-server.com ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAI...
```

Copy **one** of those lines (the full `ssh-rsa AAAA...` or `ssh-ed25519 AAAA...`
string).

## How to configure it

Set the `SFTP_HOST_KEY` environment variable:

```bash
# In .env:
SFTP_HOST_KEY=ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABgQC7...
```

Or use a key from your `known_hosts` file:

```bash
# If you've connected manually before:
cat ~/.ssh/known_hosts | grep your-sftp-server

# Copy the host type + key portion (e.g. "ssh-rsa AAAA...")
```

## Behavior by environment

| Environment | `SFTP_HOST_KEY` set | Behavior |
|-------------|-------------------|----------|
| Production (`DEBUG=False`) | Yes | `RejectPolicy` -- strict verification |
| Production (`DEBUG=False`) | No | **Connection refused** (raises error) |
| Development (`DEBUG=True`) | Yes | `RejectPolicy` -- strict verification |
| Development (`DEBUG=True`) | No | `WarningPolicy` -- logs warning, allows connection |

## When to update the key

The host key changes when:

- The SFTP server is replaced or re-provisioned
- SSH keys are regenerated on the server (rare)
- You migrate to a new SFTP provider

After a key change, update `SFTP_HOST_KEY` in your environment and restart the
application.

## Troubleshooting

### "SFTP_HOST_KEY no está configurado" in production

Add `SFTP_HOST_KEY` to your production environment variables.

### "Host key verification failed"

The server's actual key doesn't match `SFTP_HOST_KEY`. Re-obtain the key with
`ssh-keyscan` and update the environment variable.

### "SFTP_HOST_KEY tiene formato inválido"

Ensure the value is in OpenSSH format: `"ssh-rsa AAAA..."` or
`"ssh-ed25519 AAAA..."` (key type, space, base64 data).

## Security impact

Without host key verification, an attacker on the network path can:

1. Intercept the SSH connection and present a fake host key
2. Capture authentication credentials (password or SSH key passphrase)
3. Read all SFTP data (tramite PDF filenames, sizes)
4. Inject or modify responses

**This is why host key verification is mandatory in production.**
