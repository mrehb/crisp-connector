# Testing Guide - Email Forwarding Feature

## Pre-Testing Checklist

Before you begin testing, ensure you have:

- ✅ Mailgun account set up
- ✅ Domain verified in Mailgun
- ✅ Mailgun API key obtained
- ✅ Environment variables configured
- ✅ Mailgun route created for conversation+*@domain
- ✅ Dependencies installed (`pip install -r requirements.txt`)

---

## Test Plan

### Phase 1: Local Server Testing

#### Step 1: Start the Server

```bash
# Make sure you're on the feature branch
git branch
# Should show: * distribute-email-forwarding

# Copy environment config
cp env.example .env

# Edit .env with your Mailgun credentials
nano .env

# Install dependencies
pip install -r requirements.txt

# Start server
python app.py
```

**Expected Output:**
```
INFO - Loaded routing data for 248 countries from CSV
INFO - Starting Crisp Integration server on port 5000
 * Running on http://0.0.0.0:5000
```

#### Step 2: Health Check

```bash
curl http://localhost:5000/health
```

**Expected Response:**
```json
{
  "status": "healthy",
  "timestamp": "2025-10-29T...",
  "service": "Crisp Integration"
}
```

#### Step 3: Service Info Check

```bash
curl http://localhost:5000/
```

**Expected Response:**
```json
{
  "service": "JotForm to Crisp Integration",
  "version": "2.0.0 - Email Forwarding",
  "endpoints": {
    "webhook": "/webhook/jotform",
    "mailgun_incoming": "/webhook/mailgun-incoming",
    ...
  },
  "features": [
    "Email forwarding via Mailgun",
    "Three-way email threading",
    ...
  ]
}
```

---

### Phase 2: Webhook Testing

#### Step 1: Run Test Script

```bash
python test_email_forwarding.py
```

**Expected Output:**
```
✅ SUCCESS! Webhook processed successfully.

📋 What to check now:
1. Crisp Dashboard: Look for new conversation
2. Mailgun Dashboard: Look for sent email
3. Email Inbox: Check distributor and customer received emails
```

#### Step 2: Check Server Logs

Look for these log entries:

```
================================================================================
Processing contact with EMAIL FORWARDING approach
================================================================================
Customer: John Doe (john.doe@example.com)
Location: New York, United States
Routing for US: agent_id=xxx, distributor=cs.us@bigmaxgolf.com
Routing strategy: agent=YES, distributor_email=YES
✅ Created Crisp conversation: session_xxx
✅ Updated Crisp metadata
✅ Assigned to agent: xxx
✅ Posted note to Crisp
Email sent successfully via Mailgun - ID: xxx
  To: cs.us@bigmaxgolf.com
  CC: john.doe@example.com
✅ Email sent via Mailgun to distributor
================================================================================
✅ Successfully processed with email forwarding
================================================================================
```

---

### Phase 3: Crisp Verification

#### Check 1: Conversation Created

1. Go to Crisp Dashboard → Conversations
2. Look for newest conversation
3. Verify:
   - ✅ Customer email: `john.doe@example.com`
   - ✅ Customer name: `John Doe`
   - ✅ Segment: `EmailForwarding`
   - ✅ Location shows: New York, United States

#### Check 2: Conversation Metadata

Click on conversation → View Details → Custom Data:

```json
{
  "customer_email": "john.doe@example.com",
  "customer_name": "John Doe",
  "distributor_email": "cs.us@bigmaxgolf.com",
  "routing_method": "email_forwarding",
  "form_message": "Customer's original message...",
  "form_country": "United States",
  "form_city": "New York"
}
```

#### Check 3: Agent Assignment

- ✅ Conversation should be assigned to correct agent
- ✅ Agent determined by country routing in CSV

---

### Phase 4: Mailgun Verification

#### Check 1: Mailgun Logs

1. Go to [Mailgun Dashboard](https://app.mailgun.com)
2. Navigate to **Sending** → **Logs**
3. Look for recent email

Verify:
- ✅ Status: Delivered
- ✅ To: distributor email (e.g., `cs.us@bigmaxgolf.com`)
- ✅ Tags: `jotform-integration`, `distributor-forwarding`
- ✅ Message-ID exists

#### Check 2: Email Headers

Click on the email in Mailgun logs → View Details:

Verify headers include:
- ✅ `From`: BigMax Golf Support <support@your-domain.com>
- ✅ `To`: cs.us@bigmaxgolf.com
- ✅ `Cc`: john.doe@example.com
- ✅ `Reply-To`: conversation+session_xxx@your-domain.com
- ✅ `X-Crisp-Session-ID`: session_xxx

---

### Phase 5: Email Inbox Verification

#### Check 1: Distributor Email

Have distributor check their inbox:

Expected email should have:
- ✅ Subject: "New Customer Inquiry - John Doe (US)"
- ✅ From: BigMax Golf Support
- ✅ CC: john.doe@example.com (customer)
- ✅ Beautiful HTML formatting with customer info
- ✅ Customer message clearly displayed

#### Check 2: Customer Email

Have customer check their inbox:

Expected email should:
- ✅ Same email as distributor received
- ✅ Shows they are CC'd
- ✅ Can see distributor's email address
- ✅ Can reply to conversation

---

### Phase 6: Reply Testing (Critical!)

This is where the email forwarding really proves itself.

#### Test 6.1: Distributor Replies

1. Have distributor **reply to the email** (just hit Reply, not Reply All)
2. Write a test message: "Thank you for your inquiry. I will get back to you soon."
3. Send

**Expected Flow:**
```
Distributor hits Reply
    ↓
Email goes to: conversation+session_xxx@your-domain.com
    ↓
Mailgun route catches it
    ↓
Webhook: /webhook/mailgun-incoming receives it
    ↓
Your server:
  - Extracts session ID
  - Identifies sender as distributor
  - Posts to Crisp
  - Forwards to customer
    ↓
Customer receives distributor's reply ✅
Crisp shows the reply ✅
```

**Verify:**
1. Check server logs:
   ```
   ================================================================================
   INCOMING EMAIL from Mailgun
   ================================================================================
   From: cs.us@bigmaxgolf.com
   To: conversation+session_xxx@your-domain.com
   Session ID: session_xxx
   Reply from DISTRIBUTOR -> forwarding to customer: john.doe@example.com
   ✅ Posted email reply to Crisp
   ✅ Forwarded reply to: john.doe@example.com
   ```

2. Check Crisp conversation:
   - ✅ New message appears: "📧 Email Reply Received"
   - ✅ Shows distributor's reply content

3. Check customer email:
   - ✅ Received distributor's reply
   - ✅ Reply is properly threaded

#### Test 6.2: Customer Replies

1. Have customer **reply to the email thread**
2. Write a test message: "Great, thank you! Looking forward to hearing from you."
3. Send

**Expected Flow:**
```
Customer hits Reply
    ↓
Email goes to: conversation+session_xxx@your-domain.com
    ↓
Mailgun route catches it
    ↓
Webhook receives it
    ↓
Your server:
  - Identifies sender as customer
  - Posts to Crisp
  - Forwards to distributor
    ↓
Distributor receives customer's reply ✅
Crisp shows the reply ✅
```

**Verify:**
1. Check server logs:
   ```
   Reply from CUSTOMER -> forwarding to distributor: cs.us@bigmaxgolf.com
   ✅ Posted email reply to Crisp
   ✅ Forwarded reply to: cs.us@bigmaxgolf.com
   ```

2. Check Crisp conversation:
   - ✅ Customer's reply appears

3. Check distributor email:
   - ✅ Received customer's reply
   - ✅ Reply is properly threaded

#### Test 6.3: Multiple Reply Thread

Continue the conversation with 3-4 back-and-forth messages:

```
Customer → Distributor → Customer → Distributor
```

**Verify:**
- ✅ All messages reach both parties
- ✅ All messages appear in Crisp
- ✅ Email threading is maintained
- ✅ No messages lost
- ✅ No need to use "Reply All"

---

### Phase 7: Different Country Testing

#### Test Multiple Countries

Use the test script:

```bash
python test_email_forwarding.py
# When prompted, choose 'y' for country routing tests
```

This tests:
- 🇺🇸 United States
- 🇬🇧 United Kingdom  
- 🇩🇪 Germany
- 🇦🇺 Australia

**Verify for each:**
1. Correct distributor email used (check CSV)
2. Correct agent assigned (if available)
3. Email sent successfully
4. Conversation created in Crisp

---

### Phase 8: Edge Case Testing

#### Test 8.1: Country with No Routing

Edit test to use a country without routing (e.g., Antarctica "AQ"):

```python
test_payload["ip"] = "0.0.0.0"  # Unknown location
```

**Expected:**
- ✅ Falls back to Crisp-only processing
- ✅ No email sent (no distributor available)
- ✅ Conversation still created in Crisp
- ✅ Log shows: "Using fallback: Crisp-only processing"

#### Test 8.2: Country with Email Only (No Agent)

Find country in CSV with email but no agent_id:

```csv
DE,,office@golftech.at
```

**Expected:**
- ✅ Email sent to distributor
- ✅ No agent assigned in Crisp
- ✅ Conversation still created
- ✅ Log shows: "Routing strategy: agent=NO, distributor_email=YES"

#### Test 8.3: Invalid Email Address

Temporarily set distributor email to invalid:

```csv
US,agent-id,invalid-email
```

**Expected:**
- ✅ Crisp conversation still created
- ❌ Email fails to send
- ✅ Error logged but webhook returns 200
- ✅ System doesn't crash

---

### Phase 9: Performance Testing

#### Load Test

Send 10 webhooks in quick succession:

```bash
for i in {1..10}; do
  python test_email_forwarding.py &
done
wait
```

**Verify:**
- ✅ All 10 processed successfully
- ✅ No rate limiting errors
- ✅ All emails sent
- ✅ All Crisp conversations created
- ✅ No duplicate emails

---

### Phase 10: Mailgun Route Testing

#### Test Route Configuration

Send test email directly to catch-all:

```bash
# Method 1: Using mail command (Linux/Mac)
echo "Test reply" | mail -s "Test" conversation+test_session_123@your-domain.com

# Method 2: Using Mailgun API
curl -s --user 'api:YOUR_API_KEY' \
  https://api.mailgun.net/v3/YOUR_DOMAIN/messages \
  -F from='test@example.com' \
  -F to='conversation+test_session_123@YOUR_DOMAIN' \
  -F subject='Test Reply' \
  -F text='This is a test reply'
```

**Expected:**
1. Check webhook logs for incoming email
2. Verify session ID extraction
3. Check error handling (session doesn't exist)

---

## Test Results Checklist

Mark each as complete when verified:

### Core Functionality
- [ ] Server starts without errors
- [ ] Health check passes
- [ ] Service info shows email forwarding features
- [ ] Webhook processes JotForm submissions
- [ ] Country routing works correctly
- [ ] CSV file loads successfully

### Crisp Integration
- [ ] Conversations created in Crisp
- [ ] Correct metadata stored
- [ ] Segments applied correctly
- [ ] Agents assigned when available
- [ ] Messages posted to Crisp
- [ ] Geolocation data stored

### Email Sending
- [ ] Emails sent via Mailgun
- [ ] Distributor receives emails
- [ ] Customer CC'd on emails
- [ ] HTML formatting works
- [ ] Reply-To header correct
- [ ] Email threading maintained

### Reply Handling
- [ ] Mailgun route configured
- [ ] Incoming webhook receives replies
- [ ] Session ID extracted correctly
- [ ] Replies posted to Crisp
- [ ] Replies forwarded to correct party
- [ ] Distributor replies reach customer
- [ ] Customer replies reach distributor
- [ ] Multiple back-and-forth works

### Edge Cases
- [ ] Countries without routing handled
- [ ] Email-only routing works
- [ ] Agent-only routing works
- [ ] Invalid emails handled gracefully
- [ ] Missing session IDs handled
- [ ] Unknown senders handled

### Performance
- [ ] Multiple simultaneous webhooks work
- [ ] No duplicate emails sent
- [ ] No database/memory leaks
- [ ] Response times acceptable (<2s)

---

## Troubleshooting During Testing

### Problem: Emails not sending

**Check:**
```bash
# Verify environment variables
python -c "import os; from dotenv import load_dotenv; load_dotenv(); print(f\"API Key: {os.getenv('MAILGUN_API_KEY')[:10]}...\")"

# Test Mailgun directly
curl -s --user 'api:YOUR_API_KEY' \
  https://api.mailgun.net/v3/YOUR_DOMAIN/messages \
  -F from='test@YOUR_DOMAIN' \
  -F to='your@email.com' \
  -F subject='Test' \
  -F text='Test email'
```

### Problem: Replies not forwarding

**Check:**
1. Mailgun route exists and is active
2. Webhook URL is publicly accessible
3. Check Mailgun → Routes → Test Route
4. Verify Reply-To header in sent emails

### Problem: Session ID not found

**Check:**
1. Look at email headers in Mailgun logs
2. Verify Reply-To format: `conversation+{id}@domain`
3. Check webhook logs for extraction logic
4. Verify session_id format is correct

---

## Success Criteria

The feature is ready to deploy when:

✅ All core functionality tests pass  
✅ All Crisp integration tests pass  
✅ All email sending tests pass  
✅ All reply handling tests pass  
✅ All edge cases handled gracefully  
✅ Performance is acceptable  
✅ Documentation is complete  
✅ No critical bugs found  

---

## Next Steps After Testing

1. **Stage Testing**: Deploy to staging environment
2. **Real User Test**: Test with actual distributor/customer
3. **Monitor**: Watch logs for any issues
4. **Document Issues**: Create issues for any bugs found
5. **Iterate**: Fix bugs and retest
6. **Production Deploy**: Merge to main and deploy

---

## Test Sign-Off

| Test Phase | Status | Tester | Date | Notes |
|------------|--------|--------|------|-------|
| Phase 1: Local Server | ⬜ | | | |
| Phase 2: Webhook | ⬜ | | | |
| Phase 3: Crisp | ⬜ | | | |
| Phase 4: Mailgun | ⬜ | | | |
| Phase 5: Email Inbox | ⬜ | | | |
| Phase 6: Reply Testing | ⬜ | | | |
| Phase 7: Countries | ⬜ | | | |
| Phase 8: Edge Cases | ⬜ | | | |
| Phase 9: Performance | ⬜ | | | |
| Phase 10: Routes | ⬜ | | | |

**Final Approval**: ⬜ Ready for production

---

Good luck with testing! 🚀
