# Content Security Policy (CSP) Implementation Guide

## Overview

This document explains the Django 6.0 Content Security Policy (CSP) implementation for the San Felipe Backoffice Trámites project.

## What is CSP?

Content Security Policy (CSP) is a powerful security feature that helps prevent Cross-Site Scripting (XSS) attacks and other content injection attacks by defining which content sources are trusted. CSP instructs the browser to load, execute, or render resources only from approved sources.

## Security Benefits

1. **XSS Mitigation**: Prevents execution of unauthorized scripts by whitelisting trusted sources
2. **Content Control**: Controls which external resources (scripts, styles, images, fonts) can be loaded
3. **Injection Protection**: Blocks unauthorized content injection attacks
4. **Violation Reporting**: Provides monitoring and debugging capabilities through violation reports
5. **Clickjacking Prevention**: Works with X-Frame-Options to prevent framing attacks
6. **Plugin Blocking**: Prevents plugin-based vulnerabilities (Flash, Java, etc.)

## Configuration Details

### Location

The CSP configuration is implemented in `sanfelipe/settings.py` starting at line 56.

### Modes

The CSP can operate in two modes:

#### 1. Report-Only Mode (Default for Initial Deployment)

Set `DJANGO_CSP_REPORT_ONLY=True` in your `.env` file to enable this mode.

**Benefits:**
- Monitors violations without blocking content
- Allows you to identify potential issues before enforcement
- Safe for initial deployment
- Collects data for debugging

**Usage:**
```bash
# In .env file
DJANGO_CSP_REPORT_ONLY=True
```

#### 2. Enforced Mode (Production)

Set `DJANGO_CSP_REPORT_ONLY=False` (or omit the variable) to enable enforcement.

**Benefits:**
- Actively blocks non-compliant content
- Provides maximum security
- Required for production deployments

**Usage:**
```bash
# In .env file (or omit the variable)
DJANGO_CSP_REPORT_ONLY=False
```

### CSP Directives

The following CSP directives are configured:

| Directive | Value | Purpose |
|-----------|-------|---------|
| `default-src` | `'self'` | Fallback for all content types - allows same origin only |
| `script-src` | `'self' 'nonce-...'` | Scripts from same origin and those with valid nonces |
| `style-src` | `'self' 'unsafe-inline'` | Styles from same origin and inline styles (required for Django admin) |
| `img-src` | `'self' data:` | Images from same origin and data URIs (for base64 images) |
| `font-src` | `'self'` | Fonts from same origin (Django admin static files) |
| `connect-src` | `'self'` | AJAX/Fetch requests to same origin only |
| `object-src` | `'none'` | Blocks all plugins (Flash, Java, etc.) |
| `media-src` | `'self'` | Audio/video from same origin only |
| `frame-src` | `'none'` | Blocks all iframes |
| `frame-ancestors` | `'self'` | Prevents page from being embedded in frames |
| `base-uri` | `'self'` | Restricts base tag to same origin |
| `form-action` | `'self'` | Form submissions to same origin only |
| `manifest-src` | `'self'` | App manifests from same origin only |

### Generated CSP Header

When CSP is enforced, the following header is sent:

```
Content-Security-Policy: default-src 'self'; script-src 'self' 'nonce-SECRET'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; font-src 'self'; connect-src 'self'; object-src 'none'; media-src 'self'; frame-src 'none'; frame-ancestors 'self'; base-uri 'self'; form-action 'self'; manifest-src 'self'
```

## Template Usage

### Using Nonces for Inline Scripts and Styles

When you need to use inline `<script>` or `<style>` tags, you must use the nonce attribute:

```html
<!-- In your Django templates -->
<script nonce="{{ csp_nonce }}">
    // This inline JavaScript will be allowed
    console.log('Hello from inline script!');
</script>

<style nonce="{{ csp_nonce }}">
    /* These inline styles will be allowed */
    .custom-class {
        color: red;
    }
</style>
```

**Important:**
- The `csp_nonce` context variable is automatically provided by the `csp()` context processor
- Each request gets a unique nonce value
- The nonce must match between the CSP header and the inline element
- Nonces are more secure than `unsafe-inline` as they explicitly whitelist specific scripts

### Avoiding Inline Scripts (Recommended)

For better security, avoid inline scripts and styles whenever possible:

```html
<!-- Instead of inline scripts -->
{# Load static JavaScript files #}
<script src="{% static 'js/main.js' %}" defer></script>

<!-- Instead of inline styles -->
<link rel="stylesheet" href="{% static 'css/custom.css' %}">
```

## Deployment Strategy

### Step 1: Initial Testing (Report-Only Mode)

1. Set `DJANGO_CSP_REPORT_ONLY=True` in `.env`
2. Deploy to staging/test environment
3. Monitor browser console for CSP violations
4. Fix any reported violations

### Step 2: Monitor and Adjust

1. Review CSP violation reports
2. Update CSP directives as needed
3. Ensure all functionality works correctly
4. Test thoroughly with Django admin interface

### Step 3: Production Deployment (Enforced Mode)

1. Set `DJANGO_CSP_REPORT_ONLY=False` in `.env`
2. Deploy to production
3. Monitor for any unexpected violations
4. Adjust policy if legitimate content is blocked

## Testing

### Manual Testing

1. Open browser developer tools (F12)
2. Navigate to Console tab
3. Look for CSP violation messages
4. In Report-Only mode, violations are logged but not blocked
5. In Enforced mode, violations are blocked and logged

### Automated Testing

```python
# tests/test_csp.py
from django.test import Client, override_settings

def test_csp_header_present():
    """Test that CSP header is sent in response."""
    client = Client()
    response = client.get('/admin/')

    if not override_settings(DEBUG=False):
        assert 'Content-Security-Policy' in response

def test_csp_report_only_mode():
    """Test report-only mode CSP header."""
    with override_settings(
        DJANGO_CSP_REPORT_ONLY=True,
        SECURE_CSP_REPORT_ONLY={'default-src': ["'self'"]},
        SECURE_CSP=None
    ):
        client = Client()
        response = client.get('/admin/')
        assert 'Content-Security-Policy-Report-Only' in response
```

## Django Admin Considerations

The Django admin interface has been tested and configured to work with this CSP policy:

- **Inline Styles**: The admin uses some inline styles, so `unsafe-inline` is allowed in `style-src`
- **Static Resources**: All admin JavaScript and CSS are served from `STATIC_URL`
- **Icons**: Font Awesome icons are loaded from static files
- **Images**: User-uploaded images use `data:` URIs and are allowed

## Troubleshooting

### Common Issues

1. **Inline scripts blocked**
   - **Solution**: Use `nonce="{{ csp_nonce }}"` attribute on script tags

2. **Inline styles blocked**
   - **Solution**: Use `nonce="{{ csp_nonce }}"` attribute or move to external CSS file

3. **External resources blocked**
   - **Solution**: Add trusted domain to appropriate CSP directive
   - Example: `"script-src": [CSP.SELF, "https://cdn.example.com"]`

4. **Data URIs blocked**
   - **Solution**: Add `data:` to `img-src` directive
   - Already configured: `"img-src": [CSP.SELF, "data:"]`

5. **AJAX requests blocked**
   - **Solution**: Ensure API endpoints are on same origin or add to `connect-src`

### Violation Report Format

When a CSP violation occurs, you'll see messages like:

```
Content Security Policy: The page's settings blocked an inline script (...) because it violates the following directive: "script-src 'self' 'nonce-SECRET'"
```

## Best Practices

1. **Start with Report-Only Mode**: Always test in report-only mode before enforcement
2. **Be Conservative**: Only allow what you need, not everything
3. **Use Nonces**: Prefer nonces over `unsafe-inline` for scripts
4. **Avoid Inline Content**: Move inline code to external files when possible
5. **Monitor Violations**: Set up violation reporting endpoint in production
6. **Keep Policies Simple**: Complex policies are harder to maintain and debug
7. **Document Exceptions**: Comment why specific sources are allowed

## Additional Resources

- [MDN CSP Documentation](https://developer.mozilla.org/en-US/docs/Web/HTTP/CSP)
- [Django 6.0 CSP Documentation](https://docs.djangoproject.com/en/6.0/topics/security/#content-security-policy)
- [OWASP CSP Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Content_Security_Policy_Cheat_Sheet.html)
- [CSP Evaluator](https://csp-evaluator.withgoogle.com/) - Tool to analyze CSP policies

## Support

For questions or issues related to CSP implementation:
1. Check the browser console for violation messages
2. Review this documentation
3. Consult Django's official CSP documentation
4. Contact the security team if you need to add new trusted sources
