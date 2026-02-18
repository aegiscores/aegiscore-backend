# AegisCore Backend Setup Guide

This guide walks you through deploying the form backend to Vercel (free) and connecting it to Google Sheets + email notifications.

**What you'll set up:**
- ✅ Google Sheets as database (stores submissions)
- ✅ Resend for email notifications (client confirmations + admin alerts)
- ✅ Vercel serverless function (handles form POST)
- ✅ Updated landing page that submits to your API

**Time required:** ~30 minutes

---

## Step 1: Set Up Google Sheets

### 1.1 Create the spreadsheet
1. Go to [Google Sheets](https://sheets.google.com)
2. Create a new blank spreadsheet
3. Name it: `AegisCore Submissions`
4. In the first row (header row), add these columns exactly:

   ```
   Submission ID | Timestamp | Status | Name | Role | Email | Company | Phone | Domain | Service | Notes
   ```

5. Copy the **Sheet ID** from the URL:
   ```
   https://docs.google.com/spreadsheets/d/[THIS_IS_THE_SHEET_ID]/edit
   ```
   Save this ID — you'll need it later.

### 1.2 Create a Google Cloud service account

1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Create a new project (or select existing): "AegisCore"
3. Enable the **Google Sheets API**:
   - Search for "Google Sheets API" in the search bar
   - Click "Enable"
4. Create a service account:
   - Go to **IAM & Admin → Service Accounts**
   - Click **+ CREATE SERVICE ACCOUNT**
   - Name: `aegiscore-backend`
   - Click **Create and Continue**
   - Skip roles (click Continue)
   - Click **Done**
5. Generate a key:
   - Click on the service account you just created
   - Go to **Keys** tab
   - Click **Add Key → Create New Key**
   - Choose **JSON** format
   - Click **Create** — a file downloads

6. Open the downloaded JSON file. You'll need these values:
   - `client_email` (looks like: `aegiscore-backend@project-id.iam.gserviceaccount.com`)
   - `private_key` (long string starting with `-----BEGIN PRIVATE KEY-----`)

### 1.3 Share the sheet with the service account

1. Open your Google Sheet (`AegisCore Submissions`)
2. Click **Share** (top right)
3. Paste the service account email (`client_email` from JSON)
4. Give it **Editor** access
5. **Uncheck** "Notify people" (it's a service account, not a person)
6. Click **Share**

---

## Step 2: Set Up Resend (Email Service)

1. Go to [resend.com](https://resend.com)
2. Sign up for free account
3. Verify your email
4. Go to **Settings → API Keys**
5. Click **Create API Key**
   - Name: `AegisCore Backend`
   - Permission: **Sending access**
   - Click **Create**
6. Copy the API key (starts with `re_...`)
   - ⚠️ Save this — you can only see it once!

### 2.1 Add a verified domain (optional but recommended)

If you want emails to come from `hello@aegiscore.in` instead of `onboarding@resend.dev`:

1. Go to **Domains** in Resend dashboard
2. Click **Add Domain**
3. Enter: `aegiscore.in` (or your domain)
4. Follow DNS setup instructions
5. Wait for verification (~10 minutes)

**For now:** You can skip this and use the default `onboarding@resend.dev` sender. It works fine for testing.

---

## Step 3: Deploy to Vercel

### 3.1 Install Vercel CLI (if not installed)
```bash
npm install -g vercel
```

### 3.2 Deploy the backend

1. Open terminal/command prompt
2. Navigate to the `aegiscore-backend` folder:
   ```bash
   cd /path/to/aegiscore-backend
   ```

3. Login to Vercel:
   ```bash
   vercel login
   ```

4. Deploy:
   ```bash
   vercel
   ```
   
   It will ask you:
   - **Set up and deploy?** → Yes
   - **Which scope?** → Your personal account
   - **Link to existing project?** → No
   - **Project name?** → `aegiscore-backend` (press Enter)
   - **Directory?** → Press Enter (current directory)
   - **Override settings?** → No

5. Vercel will give you a URL like:
   ```
   https://aegiscore-backend-abc123.vercel.app
   ```
   
   Your API endpoint will be:
   ```
   https://aegiscore-backend-abc123.vercel.app/api/submit
   ```

### 3.3 Add environment variables to Vercel

You need to add your secrets to Vercel (never commit them to code!):

**Option A: Via Vercel Dashboard (recommended)**
1. Go to [vercel.com/dashboard](https://vercel.com/dashboard)
2. Click on your project (`aegiscore-backend`)
3. Go to **Settings → Environment Variables**
4. Add each of these (one by one):

   | Key | Value | Where to get it |
   |-----|-------|-----------------|
   | `RESEND_API_KEY` | `re_xxxxx...` | From Resend dashboard |
   | `GOOGLE_SERVICE_ACCOUNT_EMAIL` | `aegiscore-backend@project.iam.gserviceaccount.com` | From service account JSON (`client_email`) |
   | `GOOGLE_PRIVATE_KEY` | `-----BEGIN PRIVATE KEY-----\n...` | From service account JSON (`private_key`) — copy the entire string including `\n` |
   | `GOOGLE_SHEET_ID` | `1AbCdEf...` | From your Google Sheet URL |
   | `ADMIN_EMAIL` | `your-email@gmail.com` | Your email for admin notifications |

5. Click **Save** after adding each one

**Option B: Via CLI**
```bash
vercel env add RESEND_API_KEY
# Paste your key when prompted
# Choose: Production, Preview, Development (select all)

vercel env add GOOGLE_SERVICE_ACCOUNT_EMAIL
# etc...
```

### 3.4 Redeploy to apply environment variables
```bash
vercel --prod
```

Now your API is live at:
```
https://aegiscore-backend.vercel.app/api/submit
```

---

## Step 4: Update Landing Page

Now you need to update your landing page to POST to the Vercel API instead of just showing a success message.

### 4.1 Edit `aegiscore-landing.html`

Find this section at the bottom of the file:
```javascript
// Form
document.getElementById('assessmentForm').addEventListener('submit',function(e){
  e.preventDefault();
  this.style.display='none';
  document.getElementById('formSuccess').classList.add('show');
  document.getElementById('start').scrollIntoView({behavior:'smooth'});
});
```

**Replace it with:**
```javascript
// Form submission with backend integration
document.getElementById('assessmentForm').addEventListener('submit', async function(e) {
  e.preventDefault();
  
  const submitBtn = this.querySelector('.form-submit');
  const originalText = submitBtn.textContent;
  submitBtn.textContent = 'Submitting...';
  submitBtn.disabled = true;

  // Gather form data
  const formData = {
    name: this.name.value,
    role: this.role.value,
    email: this.email.value,
    company: this.company.value,
    phone: this.phone.value,
    domain: this.domain.value,
    service: this.service.value,
    notes: this.notes.value,
  };

  try {
    // POST to Vercel API
    const response = await fetch('https://YOUR-PROJECT.vercel.app/api/submit', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(formData),
    });

    const result = await response.json();

    if (response.ok) {
      // Success
      this.style.display = 'none';
      document.getElementById('formSuccess').classList.add('show');
      document.getElementById('start').scrollIntoView({behavior:'smooth'});
    } else {
      // Error from API
      throw new Error(result.message || 'Submission failed');
    }
  } catch (error) {
    // Network or API error
    alert('Submission failed: ' + error.message + '\n\nPlease email us directly at hello@aegiscore.in');
    submitBtn.textContent = originalText;
    submitBtn.disabled = false;
  }
});
```

**⚠️ Important:** Replace `YOUR-PROJECT.vercel.app` with your actual Vercel URL!

### 4.2 Redeploy the landing page

If you're hosting on Netlify:
1. Update the HTML file
2. Drag and drop to Netlify again (it will update the existing site)

If you're hosting on Vercel alongside the backend:
```bash
vercel --prod
```

---

## Step 5: Update Admin Dashboard to Read from Google Sheets

Right now the admin dashboard uses mock data. Let's connect it to your real Google Sheet.

### 5.1 Create a read API endpoint

Create `/api/submissions.js`:

```javascript
const { GoogleSpreadsheet } = require('google-spreadsheet');
const { JWT } = require('google-auth-library');

module.exports = async (req, res) => {
  // Simple auth - check for admin password in header
  const authHeader = req.headers.authorization;
  if (authHeader !== `Bearer ${process.env.ADMIN_PASSWORD}`) {
    return res.status(401).json({ error: 'Unauthorized' });
  }

  try {
    const serviceAccountAuth = new JWT({
      email: process.env.GOOGLE_SERVICE_ACCOUNT_EMAIL,
      key: process.env.GOOGLE_PRIVATE_KEY.replace(/\\n/g, '\n'),
      scopes: ['https://www.googleapis.com/auth/spreadsheets'],
    });

    const doc = new GoogleSpreadsheet(
      process.env.GOOGLE_SHEET_ID,
      serviceAccountAuth
    );

    await doc.loadInfo();
    const sheet = doc.sheetsByIndex[0];
    const rows = await sheet.getRows();

    const submissions = rows.map(row => ({
      id: row.get('Submission ID'),
      timestamp: row.get('Timestamp'),
      status: row.get('Status'),
      name: row.get('Name'),
      role: row.get('Role'),
      email: row.get('Email'),
      company: row.get('Company'),
      phone: row.get('Phone'),
      domain: row.get('Domain'),
      service: row.get('Service'),
      notes: row.get('Notes'),
      rowIndex: row.rowIndex, // For updates
    }));

    return res.status(200).json({ submissions });
  } catch (error) {
    console.error('Read error:', error);
    return res.status(500).json({ error: error.message });
  }
};
```

### 5.2 Add ADMIN_PASSWORD to Vercel env vars
```bash
vercel env add ADMIN_PASSWORD
# Enter: aegis2026 (or your chosen password)
```

### 5.3 Update admin dashboard to fetch from API

In `aegiscore-admin.html`, replace the mock `submissions` array with:

```javascript
let submissions = [];

async function loadSubmissions() {
  try {
    const response = await fetch('https://YOUR-PROJECT.vercel.app/api/submissions', {
      headers: {
        'Authorization': 'Bearer aegis2026' // Match your ADMIN_PASSWORD
      }
    });
    const data = await response.json();
    submissions = data.submissions;
    renderSubmissions();
  } catch (error) {
    console.error('Failed to load submissions:', error);
    alert('Failed to load data. Check console.');
  }
}

// Call this after login
function login() {
  // ... existing login code ...
  document.getElementById('loginScreen').style.display = 'none';
  document.getElementById('dashboard').style.display = 'block';
  loadSubmissions(); // ← Add this line
}
```

---

## Step 6: Test Everything

### 6.1 Test form submission
1. Open your landing page
2. Fill out the assessment form
3. Submit
4. You should see:
   - ✅ Success message on landing page
   - ✅ New row in Google Sheet
   - ✅ Confirmation email in your inbox
   - ✅ Admin notification at your email

### 6.2 Test admin dashboard
1. Open admin dashboard
2. Login with password: `aegis2026`
3. You should see the submission you just made
4. Try changing status (New → In Progress → Complete)

---

## Troubleshooting

### Form submission fails
- Check browser console (F12) for errors
- Verify your Vercel API URL is correct in the landing page
- Check Vercel function logs: `vercel logs`

### No email received
- Check spam folder
- Verify Resend API key is correct in Vercel env vars
- Check Vercel function logs for email errors
- Make sure sender email is verified (if using custom domain)

### Google Sheets not updating
- Verify service account email has Editor access to the sheet
- Check that column names match exactly (case-sensitive)
- Verify `GOOGLE_SHEET_ID` in Vercel env vars

### Admin dashboard shows no data
- Check that `/api/submissions.js` is deployed
- Verify `ADMIN_PASSWORD` matches in both code and env vars
- Check browser console for fetch errors
- Try adding `console.log` to the API endpoint

---

## Next Steps

**Once everything is working:**

1. **Update the password** — change `ADMIN_PASSWORD` in Vercel env vars
2. **Secure the admin dashboard** — host it on a separate private URL
3. **Set up custom domain** — connect `aegiscore.in` to Vercel
4. **Add status update API** — so clicking "Start Work" updates Google Sheets
5. **Wire up report generation** — clicking "Generate Report" triggers PDF creation

---

## File Structure

```
aegiscore-backend/
├── api/
│   ├── submit.js          # Form submission handler
│   └── submissions.js     # Read submissions (for admin dashboard)
├── package.json           # Dependencies
├── vercel.json           # Vercel config
├── .env.example          # Template for environment variables
└── SETUP.md              # This file
```

---

## Support

Issues? Questions? Email: hello@aegiscore.in

**Common first-time mistakes:**
- Forgetting to share Google Sheet with service account
- Missing `\n` in private key (must be included as literal `\n` characters)
- Using wrong Vercel URL in landing page form
- Not redeploying after adding environment variables
