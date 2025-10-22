# Crisp API Permissions Analysis

## Current Issues Identified

### 1. ❌ List People Profiles - 405 Method Not Allowed
**Endpoint:** `GET /v1/website/{website_id}/people/profile?search_text={email}`

**Error:** 
```
405 Client Error: Method Not Allowed for url: 
https://api.crisp.chat/v1/website/0bf95c47-0a42-48eb-9517-79ff1cc431d9/people/profile?search_text=maxxi.reiter%40gmail.com
```

**What This Means:**
- The API endpoint might not be available with current API tier/permissions
- Or the endpoint structure has changed in the API version

**Required Permission:**
- Need access to search/list people profiles
- May require "People API" access or higher tier

**Impact:**
- Cannot check if contact already exists before creating conversation
- Always creates new profile instead of updating existing ones

---

### 2. ❌ Set Conversation State - 403 Forbidden
**Endpoint:** `PATCH /v1/website/{website_id}/conversation/{session_id}/state`

**Error:**
```
403 Client Error: Forbidden for url: 
https://api.crisp.chat/v1/website/0bf95c47-0a42-48eb-9517-79ff1cc431d9/conversation/session_id/state
```

**What This Means:**
- Current API key does NOT have permission to change conversation state
- Cannot set conversations to "unresolved", "resolved", or "pending"

**Required Permission:**
- Need `conversation:state:write` or similar permission
- May require operator-level access (not plugin tier)

**Impact:**
- New conversations remain in default state
- Cannot automatically mark them as "unresolved" requiring attention

---

### 3. ❌ Send Message in Conversation - 400 Bad Request
**Endpoint:** `POST /v1/website/{website_id}/conversation/{session_id}/message`

**Error:**
```
400 Client Error: Bad Request for url: 
https://api.crisp.chat/v1/website/0bf95c47-0a42-48eb-9517-79ff1cc431d9/conversation/session_id/message
```

**What This Means:**
- The message payload format is incorrect OR
- Missing required permission to send messages as "user" with origin "email"

**Required Permission:**
- Need `message:send` permission
- May need ability to impersonate users (send as user, not operator)

**Impact:**
- The form message content is not being posted to the conversation
- Conversation is created but empty (no message content)

---

## What IS Working ✅

1. **Create Conversation** - 200 OK
   - Endpoint: `POST /v1/website/{website_id}/conversation`
   - Successfully creates new conversation
   - Returns valid session_id

2. **Update Conversation Metadata** - 200 OK
   - Endpoint: `PATCH /v1/website/{website_id}/conversation/{session_id}/meta`
   - Successfully updates: email, nickname, subject, segments, IP, geolocation
   - All contact info is being saved

3. **IP Geolocation Lookup** - 200 OK
   - External API working perfectly
   - Getting city, region, country, coordinates

---

## Recommended Actions

### Immediate (Workarounds):
1. **Remove the "List People Profiles" check** - Always treat as new contact
2. **Skip setting conversation state** - Let Crisp use default state
3. **Fix message sending** - Try alternative payload format or different endpoint

### Long-term (API Key Permissions):
1. **Contact Crisp Support** to upgrade API permissions
2. **Request these specific permissions:**
   - `people:profile:read` - To search existing contacts
   - `conversation:state:write` - To set conversation states
   - `message:send:user` - To send messages as user (from email origin)

### Alternative Approach:
- Use Make.com for the actual message sending (it has the permissions)
- Use this script just to collect and forward data to Make webhook
- Or use Crisp's REST API with a higher-tier API key

---

## Testing Notes

**Test performed:** 2025-10-22 19:23:20
- Email: maxxi.reiter@gmail.com
- Name: Maxxi Reiter
- Session ID: session_277e5b1c-32da-43ad-9c88-03e322bf9185

**Result:** Conversation created with metadata, but no message content visible in Crisp dashboard.

