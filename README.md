# Crisp Connector

JotForm to Crisp integration webhook server. Automatically creates Crisp conversations from JotForm submissions with geolocation data.

## Features

- 🔗 Receives JotForm webhook submissions
- 📍 IP geolocation lookup via IP2Location
- 💬 Creates Crisp conversations
- 👤 Manages contact profiles
- 🔄 Updates existing contacts

## Quick Start

See [QUICKSTART.md](QUICKSTART.md) for detailed setup instructions.

### Local Development

1. Clone the repository:
```bash
git clone https://github.com/mrehb/crisp-connector.git
cd crisp-connector
```

2. Set up environment variables:
```bash
cp env.example .env
# Edit .env with your API credentials
```

3. Run the server:
```bash
./start.sh
```

The server will start on `http://localhost:5000`

## Deployment

### Railway (Recommended)

[![Deploy on Railway](https://railway.app/button.svg)](https://railway.app/new/template?template=https://github.com/mrehb/crisp-connector)

Or manually:

```bash
# Install Railway CLI
brew install railway

# Login
railway login

# Initialize project
railway init

# Set environment variables
railway variables set CRISP_WEBSITE_ID=your-website-id
railway variables set CRISP_API_IDENTIFIER=your-api-identifier
railway variables set CRISP_API_KEY=your-api-key
railway variables set IP2LOCATION_API_KEY=your-ip2location-key

# Deploy
railway up
```

### Heroku

```bash
heroku create your-app-name
heroku config:set CRISP_WEBSITE_ID=your-id
heroku config:set CRISP_API_IDENTIFIER=your-identifier
heroku config:set CRISP_API_KEY=your-key
heroku config:set IP2LOCATION_API_KEY=your-key
git push heroku main
```

### Other Platforms

- **Fly.io**: `fly launch`
- **DigitalOcean App Platform**: Connect via GitHub
- **Google Cloud Run**: Use Docker deployment
- **AWS Elastic Beanstalk**: Deploy Python application

## Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `CRISP_WEBSITE_ID` | Your Crisp website ID | Yes |
| `CRISP_API_IDENTIFIER` | Crisp API identifier | Yes |
| `CRISP_API_KEY` | Crisp API key | Yes |
| `IP2LOCATION_API_KEY` | IP2Location.io API key | Yes |
| `PORT` | Server port (default: 5000) | No |
| `DEBUG` | Enable debug mode (default: false) | No |

## API Endpoints

- `GET /` - Service information
- `GET /health` - Health check
- `POST /webhook/jotform` - JotForm webhook receiver

## Testing

Test the webhook locally:

```bash
python test_webhook.py
```

Or with curl:

```bash
curl -X POST http://localhost:5000/webhook/jotform \
  -H "Content-Type: application/json" \
  -d '{
    "ip": "8.8.8.8",
    "request": {
      "q3_name": "John Doe",
      "q4_company": "Acme Corp",
      "q6_email": "john@example.com",
      "q7_message": "Test message"
    }
  }'
```

## JotForm Setup

1. Go to your JotForm form
2. Settings → Integrations → Webhooks
3. Add webhook URL: `https://your-domain.com/webhook/jotform`
4. Select "Send Post Data"
5. Save

## Tech Stack

- **Python 3.8+**
- **Flask** - Web framework
- **Gunicorn** - WSGI server
- **Crisp API** - Customer messaging
- **IP2Location.io** - Geolocation service

## File Structure

```
crisp-connector/
├── app.py                 # Main application (Flask server)
├── requirements.txt       # Python dependencies
├── Procfile              # Process configuration
├── railway.json          # Railway configuration
├── start.sh              # Quick start script
├── test_webhook.py       # Test script
├── env.example           # Environment template
├── QUICKSTART.md         # Quick start guide
└── README.md            # This file
```

## Security Notes

- Never commit `.env` file
- Use HTTPS in production
- Consider adding webhook signature verification
- Rotate API keys regularly
- Use environment variables for all secrets

## License

MIT License - feel free to use this for your projects!

## Support

- **Issues**: [GitHub Issues](https://github.com/mrehb/crisp-connector/issues)
- **Crisp API Docs**: https://docs.crisp.chat/api/
- **JotForm Webhooks**: https://www.jotform.com/help/442-how-to-setup-a-webhook

## Contributing

Pull requests are welcome! For major changes, please open an issue first.

---

Made with ❤️ for seamless form integrations

