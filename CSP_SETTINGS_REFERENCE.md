# Django 6.0 CSP Settings Reference

## Quick Reference of Changes to `sanfelipe/settings.py`

### 1. Import CSP Utilities (Line 14)
```python
# Import CSP utilities for Django 6.0 Content Security Policy support
from django.utils.csp import CSP
```

### 2. Add CSP Configuration (Lines 55-170)
```python
# =============================================================================
# CONTENT SECURITY POLICY (CSP) - Django 6.0 Native Support
# =============================================================================

CSP_REPORT_MODE = env.bool('DJANGO_CSP_REPORT_ONLY', default=False)

if CSP_REPORT_MODE:
    # Report-only mode
    SECURE_CSP_REPORT_ONLY = {
        "default-src": [CSP.SELF],
        "script-src": [CSP.SELF, CSP.NONCE],
        "style-src": [CSP.SELF, CSP.UNSAFE_INLINE],
        "img-src": [CSP.SELF, "data:"],
        "font-src": [CSP.SELF],
        "connect-src": [CSP.SELF],
        "object-src": [CSP.NONE],
        "media-src": [CSP.SELF],
        "frame-src": [CSP.NONE],
        "frame-ancestors": [CSP.SELF],
        "base-uri": [CSP.SELF],
        "form-action": [CSP.SELF],
        "manifest-src": [CSP.SELF],
    }
    SECURE_CSP = None
else:
    # Enforced mode
    SECURE_CSP = {
        "default-src": [CSP.SELF],
        "script-src": [CSP.SELF, CSP.NONCE],
        "style-src": [CSP.SELF, CSP.UNSAFE_INLINE],
        "img-src": [CSP.SELF, "data:"],
        "font-src": [CSP.SELF],
        "connect-src": [CSP.SELF],
        "object-src": [CSP.NONE],
        "media-src": [CSP.SELF],
        "frame-src": [CSP.NONE],
        "frame-ancestors": [CSP.SELF],
        "base-uri": [CSP.SELF],
        "form-action": [CSP.SELF],
        "manifest-src": [CSP.SELF],
    }
    SECURE_CSP_REPORT_ONLY = None
```

### 3. Add CSP Middleware (Line 196)
```python
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.middleware.csp.ContentSecurityPolicyMiddleware',  # NEW
    'django.contrib.sessions.middleware.SessionMiddleware',
    # ... rest of middleware
]
```

### 4. Add CSP Context Processor (Line 230)
```python
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'django.template.context_processors.csp',  # NEW
            ],
        },
    },
]
```

## Environment Configuration (`.env`)

### For Report-Only Mode (Testing)
```bash
DJANGO_CSP_REPORT_ONLY=True
```

### For Enforced Mode (Production)
```bash
DJANGO_CSP_REPORT_ONLY=False
```
or simply omit the variable (defaults to False)

## Generated CSP Header

When enforced, the following header is sent:

```
Content-Security-Policy: default-src 'self'; script-src 'self' 'nonce-SECRET'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; font-src 'self'; connect-src 'self'; object-src 'none'; media-src 'self'; frame-src 'none'; frame-ancestors 'self'; base-uri 'self'; form-action 'self'; manifest-src 'self'
```

## Template Usage

### Inline Script
```html
<script nonce="{{ csp_nonce }}">
    // JavaScript code
</script>
```

### Inline Style
```html
<style nonce="{{ csp_nonce }}">
    /* CSS code */
</style>
```

### External Resources
```html
<script src="{% static 'js/main.js' %}" defer></script>
<link rel="stylesheet" href="{% static 'css/styles.css' %}">
<img src="{% static 'images/logo.png' %}" alt="Logo">
```

## CSP Constants Reference

| Constant | Value | Description |
|----------|-------|-------------|
| `CSP.SELF` | `'self'` | Allow same origin only |
| `CSP.NONE` | `'none'` | Block all |
| `CSP.NONCE` | `'nonce-...'` | Allow elements with matching nonce |
| `CSP.UNSAFE_INLINE` | `'unsafe-inline'` | Allow inline content (use sparingly) |
| `CSP.UNSAFE_EVAL` | `'unsafe-eval'` | Allow eval() (never use) |

## Common CSP Violations and Solutions

### 1. Inline Script Blocked
```
Content Security Policy: The page's settings blocked an inline script
```
**Solution**: Add `nonce="{{ csp_nonce }}"` to the script tag

### 2. Inline Style Blocked
```
Content Security Policy: The page's settings blocked an inline style
```
**Solution**: Add `nonce="{{ csp_nonce }}"` to the style tag

### 3. External Script Blocked
```
Content Security Policy: The page's settings blocked a resource
```
**Solution**: Add domain to `script-src` directive (e.g., `"script-src": [CSP.SELF, "https://cdn.example.com"]`)

### 4. External Font Blocked
```
Content Security Policy: The page's settings blocked a font resource
```
**Solution**: Add domain to `font-src` directive

### 5. Data URI Image Blocked
```
Content Security Policy: The page's settings blocked a data: resource
```
**Solution**: Add `data:` to `img-src` (already configured)

## Verification Checklist

- [x] CSP middleware added to MIDDLEWARE
- [x] CSP context processor added to TEMPLATES
- [x] CSP policy configured in settings
- [x] Environment variable added to .env.example
- [x] Documentation created (CSP_IMPLEMENTATION.md)
- [x] Example template created (templates/csp_example.html)
- [x] Summary document created (CSP_IMPLEMENTATION_SUMMARY.md)

## Next Steps

1. Set `DJANGO_CSP_REPORT_ONLY=True` in `.env`
2. Run development server
3. Open browser DevTools Console
4. Navigate through the application
5. Check for CSP violation messages
6. Fix any violations found
7. Repeat until no violations appear
8. Switch to enforced mode in production

## Testing Commands

```bash
# Start development server
python manage.py runserver

# Check environment variable
echo $DJANGO_CSP_REPORT_ONLY

# Run tests (when CSP tests are added)
python manage.py test
```

## Quick Troubleshooting

| Problem | Solution |
|---------|----------|
| Inline scripts blocked | Add `nonce="{{ csp_nonce }}"` |
| Inline styles blocked | Add `nonce="{{ csp_nonce }}"` |
| External resources blocked | Add domain to appropriate CSP directive |
| Everything blocked | Check CSP_REPORT_MODE setting |
| Django admin broken | Verify `unsafe-inline` in style-src |
| Font Awesome not loading | Add font domains to font-src |

## Security Levels

| Level | Description | When to Use |
|-------|-------------|-------------|
| Report-Only | Monitor only, don't block | Initial deployment, testing |
| Enforced | Block non-compliant content | Production, after testing |
| Permissive | Allow everything | Never (defeats purpose) |

## Best Practices

1. ✅ Always start with report-only mode
2. ✅ Use nonces for inline content
3. ✅ Minimize inline scripts/styles
4. ✅ Prefer external files
5. ✅ Monitor violations regularly
6. ✅ Document policy exceptions
7. ✅ Keep policy simple and clear
8. ❌ Never use `unsafe-eval`
9. ❌ Avoid `unsafe-inline` when possible
10. ❌ Don't allow overly permissive sources
