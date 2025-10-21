# Quick Start Guide - Crisp Integration

Get up and running in 5 minutes! 🚀

## Prerequisites

- Python 3.8+ installed
- Crisp account with API access
- JotForm account
- IP2Location.io account (free tier works)

## 1. Get API Credentials

### Crisp API Credentials

1. Log in to [Crisp](https://app.crisp.chat/)
2. Go to **Settings** → **API**
3. Create a new API key
4. Save these values:
   - Website ID
   - API Identifier
   - API Key

### IP2Location API Key

1. Sign up at [IP2Location.io](https://www.ip2location.io/)
2. Get your API key from the dashboard
3. Free tier: 30,000 requests/month

## 2. Configure Environment

Copy the example environment file:

```bash
cp env.example .env
```

Edit `.env` with your credentials:

```bash
CRISP_WEBSITE_ID=your-website-id
CRISP_API_IDENTIFIER=your-api-identifier
CRISP_API_KEY=your-api-key
IP2LOCATION_API_KEY=your-ip2location-key
```

## 3. Run the Server

### Option A: Quick Start Script (Recommended)

```bash
./start.sh
```

This script will:
- Create a virtual environment
- Install dependencies
- Start the server

### Option B: Manual Start

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run the server
python crisp_integration.py
```

### Option C: Docker

```bash
# Copy env.example to .env and configure it first
docker-compose up -d
```

## 4. Test the Integration

Run the test script:

```bash
python test_webhook.py
```

Or test manually:

```bash
curl http://localhost:5000/health
```

## 5. Configure JotForm

1. Go to your JotForm form
2. Click **Settings** → **Integrations**
3. Find **Webhooks**
4. Add webhook URL:
   - Development: `http://your-public-url:5000/webhook/jotform`
   - Production: `https://your-domain.com/webhook/jotform`
5. Select "Send Post Data"
6. Save

### Making Local Development Public

For testing, use [ngrok](https://ngrok.com/):

```bash
# Install ngrok
brew install ngrok  # macOS
# or download from https://ngrok.com/

# Start tunnel
ngrok http 5000

# Use the HTTPS URL in JotForm webhook settings
# Example: https://abc123.ngrok.io/webhook/jotform
```

## 6. Verify It Works

1. Submit a test form in JotForm
2. Check server logs for processing
3. Check Crisp dashboard for new conversation
4. Verify contact information and geolocation

## Common Issues

### Server won't start

**Problem**: Port 5000 already in use

**Solution**: Change port in `.env`:
```bash
PORT=8000
```

### API Authentication Failed

**Problem**: Invalid Crisp credentials

**Solution**: 
- Verify credentials in Crisp dashboard
- Make sure you copied them correctly to `.env`
- Check for extra spaces or quotes

### Webhook not receiving data

**Problem**: JotForm webhook not reaching server

**Solution**:
- Use ngrok for local development
- Check firewall settings
- Verify webhook URL in JotForm

### IP Geolocation not working

**Problem**: Empty geolocation data

**Solution**:
- Verify IP2Location API key
- Check if API quota exceeded
- Private/internal IPs won't have location data

## Production Deployment

### Deploy to Cloud

See `README_SCRIPT.md` for detailed deployment guides:
- Heroku
- AWS EC2
- DigitalOcean
- Docker

### Quick Heroku Deploy

```bash
# Install Heroku CLI
brew tap heroku/brew && brew install heroku

# Login
heroku login

# Create app
heroku create your-app-name

# Set environment variables
heroku config:set CRISP_WEBSITE_ID=your-id
heroku config:set CRISP_API_IDENTIFIER=your-identifier
heroku config:set CRISP_API_KEY=your-key
heroku config:set IP2LOCATION_API_KEY=your-key

# Deploy
git init
git add .
git commit -m "Deploy Crisp integration"
git push heroku main

# Open app
heroku open
```

Your webhook URL will be: `https://your-app-name.herokuapp.com/webhook/jotform`

## Next Steps

- [ ] Set up SSL certificate for production
- [ ] Configure Nginx reverse proxy (optional)
- [ ] Set up monitoring and logging
- [ ] Configure rate limiting
- [ ] Add webhook signature verification
- [ ] Customize form field mappings

## Support

- **Main Documentation**: See `README_SCRIPT.md`
- **Crisp API**: https://docs.crisp.chat/api/
- **JotForm Webhooks**: https://www.jotform.com/help/442-how-to-setup-a-webhook

## Test Data

Test form submission payload:

```json
{
  "ip": "8.8.8.8",
  "request": {
    "q3_name": "John Doe",
    "q4_company": "Acme Corp",
    "q6_email": "john@example.com",
    "q7_message": "Test message"
  }
}
```

Send test request:

```bash
curl -X POST http://localhost:5000/webhook/jotform \
  -H "Content-Type: application/json" \
  -d @test_payload.json
```

## Files Overview

- `crisp_integration.py` - Main application script
- `requirements.txt` - Python dependencies
- `start.sh` - Quick start script
- `test_webhook.py` - Test script
- `.env` - Configuration (create from env.example)
- `Dockerfile` - Docker image
- `docker-compose.yml` - Docker Compose config
- `Procfile` - Heroku deployment config
- `nginx.conf` - Nginx configuration example
- `crisp-integration.service` - Systemd service file

---

**Ready to go!** 🎉

If you encounter any issues, check `README_SCRIPT.md` for detailed troubleshooting.

