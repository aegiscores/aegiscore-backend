# AegisCore Backend

Form backend for AegisCore landing page. Handles form submissions, stores data in Google Sheets, and sends email notifications.

## What This Does

When someone fills out the assessment form on your landing page:
1. **POST** request hits `/api/submit`
2. Data is saved to **Google Sheets** (your database)
3. **Confirmation email** sent to client via Resend
4. **Admin notification** sent to you
5. Client sees success message

Your admin dashboard reads from the same Google Sheet to display all submissions.

## Files

```
aegiscore-backend/
├── api/
│   ├── submit.js          # Handles form POST, saves to Sheets, sends emails
│   └── submissions.js     # Reads all submissions (for admin dashboard)
├── package.json           # Node dependencies
├── vercel.json           # Vercel deployment config
├── .env.example          # Template for your environment variables
├── SETUP.md              # Full deployment guide (START HERE)
└── README.md             # This file
```

## Quick Start

1. **Read SETUP.md first** — it has the full walkthrough
2. Set up Google Sheets (5 mins)
3. Create Resend account (2 mins)
4. Deploy to Vercel (5 mins)
5. Add environment variables (5 mins)
6. Update landing page to use your API (2 mins)
7. Test everything (5 mins)

**Total time: ~30 minutes**

## Tech Stack

- **Vercel** — Serverless functions (free tier)
- **Google Sheets** — Database (free)
- **Resend** — Email service (free tier: 3000 emails/month)
- **Node.js** — Runtime

## Environment Variables Required

You need to add these to Vercel (not in code):

```
RESEND_API_KEY=re_xxxxx...
GOOGLE_SERVICE_ACCOUNT_EMAIL=service@project.iam.gserviceaccount.com
GOOGLE_PRIVATE_KEY=-----BEGIN PRIVATE KEY-----...
GOOGLE_SHEET_ID=1AbCdEf...
ADMIN_EMAIL=your-email@gmail.com
ADMIN_PASSWORD=aegis2026
```

See SETUP.md for where to get each of these.

## API Endpoints

Once deployed, you'll have:

**POST** `/api/submit`
- Receives form submissions from landing page
- Body: `{ name, email, company, domain, service, role?, phone?, notes? }`
- Returns: `{ success: true, submissionId: "SUB-123456" }`

**GET** `/api/submissions`
- Returns all submissions from Google Sheets
- Requires: `Authorization: Bearer <ADMIN_PASSWORD>` header
- Returns: `{ success: true, submissions: [...] }`

## Testing Locally

```bash
# Install dependencies
npm install

# Install Vercel CLI
npm install -g vercel

# Run locally
vercel dev
```

Your API will be at: `http://localhost:3000/api/submit`

## Deployment

```bash
# Login to Vercel
vercel login

# Deploy
vercel

# Deploy to production
vercel --prod
```

Your API will be at: `https://your-project.vercel.app/api/submit`

## Costs

Everything is free until you scale:

- **Vercel** — Free tier: 100GB bandwidth/month, unlimited API calls
- **Google Sheets** — Free: 10 million cells per sheet
- **Resend** — Free tier: 3,000 emails/month, 100 emails/day

At 10 submissions/day = 300/month, you're well within free limits for months.

## Next Steps

After deployment:
1. Update landing page form to POST to your Vercel API
2. Update admin dashboard to read from `/api/submissions`
3. Test end-to-end flow
4. Add custom domain (optional)
5. Set up status update API (future enhancement)

## Support

Questions? Email: hello@aegiscore.in
redeploy
redeploy trigger
redeploy trigger
redeploy again
