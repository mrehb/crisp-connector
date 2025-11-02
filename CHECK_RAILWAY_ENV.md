# Check Railway Environment Variables

The most likely reason emails aren't being sent is missing or incorrect Mailgun environment variables in Railway.

## How to check Railway environment variables

1. Go to: https://railway.app/
2. Open your project
3. Click on your service
4. Go to: **Variables** tab
5. Verify these variables are set:

### Required Mailgun Variables

```
MAILGUN_API_KEY=key-xxxxxxxxxxxxxxxxxxxxx
MAILGUN_DOMAIN=mg.us.bigmaxgolf.com
MAILGUN_FROM_EMAIL=support@mg.us.bigmaxgolf.com
MAILGUN_FROM_NAME=BigMax Golf Support
```

## Common issues

### 1. Variables not set
- If these variables are missing, emails will fail silently
- Add them in Railway Variables tab
- Redeploy after adding

### 2. Wrong API key format
- Should start with `key-`
- Get it from Mailgun: https://app.mailgun.com/ → Settings → API Keys
- Use the **Private API Key** (not public)

### 3. Wrong domain
- Should match your Mailgun domain exactly
- Check Mailgun: Sending → Domains

## How to verify from Railway logs

After setting variables, redeploy and check logs for:

```
📧 send_email_via_mailgun called:
   MAILGUN_DOMAIN: mg.us.bigmaxgolf.com
   MAILGUN_API_KEY configured: Yes
```

If it says `MAILGUN_API_KEY configured: No`, the variable is not set in Railway.

## Next steps

1. Check Railway Variables tab
2. If missing, add the Mailgun variables
3. Redeploy (Railway usually auto-redeploys when variables change)
4. Run test again
5. Check logs for "Email sent successfully via Mailgun"

