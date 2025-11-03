# Crisp Plugin Deployment Guide

Complete step-by-step guide to deploy the "Forward to Distributor" plugin.

## Prerequisites

### 1. Crisp Developer Account Setup

You need API credentials and developer access:

1. **Go to Crisp Settings**: https://app.crisp.chat/settings/account/
2. **Navigate to "API" section**
3. **Generate new API credentials** with these permissions:
   - `conversation:read` - Read conversation data
   - `conversation:write` - Send messages to conversations
   - `conversation:meta` - Read conversation metadata
   - `website:conversations:get` - Get conversation details

4. **Save credentials** (you already have these in your Railway environment variables)

### 2. Crisp Developer Portal Access

1. Go to https://app.crisp.chat/developer/
2. Create developer account (if not already created)
3. You'll use this portal to upload and activate the plugin

## Step 1: Deploy Backend to Railway

The backend webhook endpoint needs to be live before the plugin can use it.

### Option A: Merge to Main Branch (Recommended)

```bash
# Switch to main branch
git checkout main

# Merge the feature branch
git merge feature/forward-to-distributor-plugin

# Push to main
git push origin main
```

This will trigger automatic deployment to Railway.

### Option B: Deploy Feature Branch Directly

If you want to test the feature branch first:

1. Go to your Railway project
2. Settings → Connect to the feature branch
3. Or push to main when ready

### Verify Deployment

Wait ~2 minutes for deployment, then test the endpoint:

```bash
curl -X POST https://crisp-connector-production.up.railway.app/action/forward-to-distributor/session_test
```

Expected response (400 error is OK - means endpoint exists):
```json
{
  "error": "Customer email not found"
}
```

## Step 2: Create Plugin Icon

You need a 128x128 PNG icon. Choose one of these options:

### Option 1: Use Online Generator (Easiest)
1. Go to https://favicon.io/favicon-generator/
2. Create a simple icon with:
   - Text: "→" or "FWD"
   - Background color: #4A90E2 (blue)
   - Text color: #FFFFFF (white)
3. Download as PNG
4. Resize to 128x128 if needed
5. Save as `crisp-plugin/icon.png`

### Option 2: Use Figma/Canva
1. Create 128x128 canvas
2. Add forward arrow or envelope icon
3. Export as PNG
4. Save as `crisp-plugin/icon.png`

### Option 3: Download Free Icon
1. Go to https://www.flaticon.com/
2. Search for "forward arrow" or "email forward"
3. Download 128x128 PNG (free with attribution)
4. Save as `crisp-plugin/icon.png`

## Step 3: Deploy Plugin to Crisp

### 3.1 Prepare Plugin Files

Make sure you have all files in `crisp-plugin/` directory:
- ✅ `plugin.json`
- ✅ `widget.json`
- ✅ `README.md`
- ⚠️ `icon.png` (you need to create this - see Step 2)

### 3.2 Upload to Crisp Developer Portal

1. **Go to**: https://app.crisp.chat/developer/
2. **Click**: "Create Plugin" or "New Plugin"
3. **Fill in details**:
   - **Name**: Forward to Distributor
   - **Description**: Forward customer conversations to country distributors
   - **Visibility**: **Private** (only your team can use it)
   - **Category**: Customer Support / Productivity

4. **Upload files**:
   - Upload `plugin.json`
   - Upload `widget.json`
   - Upload `icon.png`
   - Add `README.md` content to description (optional)

5. **Set Permissions**:
   - Check: `conversation:read`
   - Check: `conversation:write`

6. **Click**: "Create Plugin" or "Save"

### 3.3 Activate the Plugin

1. After creation, go to plugin settings
2. Click "Activate Plugin" or "Enable"
3. Grant requested permissions
4. The widget will now appear in conversation sidebar

## Step 4: Test the Plugin

### 4.1 Open a Test Conversation

1. Go to your Crisp dashboard
2. Open any conversation that has:
   - Customer email
   - Country information
   - Distributor assigned in your CSV

### 4.2 Check Sidebar Widget

In the right sidebar, you should see:

```
┌─────────────────────────────────┐
│ Distributor Information         │
├─────────────────────────────────┤
│ Country: [Country Name]         │
│ Distributor Email: [email]      │
├─────────────────────────────────┤
│ Actions                          │
├─────────────────────────────────┤
│ [Forward to Distributor] button │
└─────────────────────────────────┘
```

### 4.3 Test the Forward Action

1. Click the "Forward to Distributor" button
2. You should see a success notification
3. Verify the following happened:

**In Crisp conversation:**
- ✅ Assigned to "Golf Tech Helpdesk" agent
- ✅ Customer received message with distributor contact
- ✅ Internal note: "✅ Manually forwarded to distributor: [email]"

**In Email:**
- ✅ Distributor received email with customer inquiry
- ✅ Email includes customer name, email, and message

**In Mailgun Logs:**
- ✅ Email delivery confirmed

### 4.4 Test with Local Script (Optional)

You can also test the backend endpoint directly:

```bash
# Test endpoint availability
python test_forward_action.py

# Test with real session ID
python test_forward_action.py session_abc123xyz
```

## Step 5: Monitor and Troubleshoot

### Check Logs

**Railway logs:**
```bash
# View live logs
railway logs --follow
```

**Look for:**
```
FORWARD TO DISTRIBUTOR ACTION - Session: [session_id]
✅ Successfully forwarded to distributor: [email]
```

### Common Issues

#### Issue 1: "No distributor found"
- **Cause**: Country has no distributor in `country_routing.csv`
- **Fix**: Add distributor email for that country

#### Issue 2: "Customer email not found"
- **Cause**: Conversation metadata missing email
- **Fix**: Ensure conversations are created with customer email

#### Issue 3: Widget not showing
- **Cause**: Plugin not activated or permissions not granted
- **Fix**: Re-activate plugin in Crisp settings

#### Issue 4: 404 Error on button click
- **Cause**: Backend endpoint not deployed
- **Fix**: Verify Railway deployment is complete

#### Issue 5: Email not sent
- **Cause**: Mailgun configuration issue
- **Fix**: Check `MAILGUN_API_KEY` and `MAILGUN_DOMAIN` in Railway

## Step 6: Rollout to Team

Once tested successfully:

1. **Announce to team**: Let your support team know about the new feature
2. **Provide instructions**: Share this guide or create a quick reference
3. **Monitor usage**: Watch for any issues in the first few days
4. **Gather feedback**: Ask team for suggestions

## Quick Reference for Team

### How to Use the Plugin

1. Open customer conversation
2. Check right sidebar for distributor info
3. Click "Forward to Distributor" button
4. Wait for success notification
5. Customer will be notified and assigned to helpdesk

### When to Use

Use the forward button when:
- Customer needs local distributor support
- Product is available in their country
- You want to hand off to regional expert

Don't use when:
- No distributor exists for country (button will show error)
- Already forwarded (avoid duplicate emails)

## Next Steps

After successful deployment:

1. ✅ Document usage in team wiki
2. ✅ Train support team on new feature
3. ✅ Monitor Mailgun delivery rates
4. ✅ Collect feedback from team
5. ✅ Consider analytics (track forward rate by country)

## Support

If you need help:
- Check Railway logs for backend errors
- Check Mailgun logs for email delivery issues
- Check Crisp developer console for plugin errors
- Review this guide for troubleshooting steps

---

**Plugin Version**: 1.0.0  
**Last Updated**: November 2025  
**Maintained by**: BigMax Golf Tech Team

