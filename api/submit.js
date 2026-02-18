// api/submit.js - Vercel Serverless Function
// Handles form submissions from landing page

const { GoogleSpreadsheet } = require('google-spreadsheet');
const { JWT } = require('google-auth-library');
const { Resend } = require('resend');

// Initialize Resend
const resend = new Resend(process.env.RESEND_API_KEY);

// CORS headers
const headers = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Methods': 'POST, OPTIONS',
  'Access-Control-Allow-Headers': 'Content-Type',
};

module.exports = async (req, res) => {
  // Handle preflight
  if (req.method === 'OPTIONS') {
    return res.status(200).json({ ok: true });
  }

  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  try {
    const {
      name,
      role,
      email,
      company,
      phone,
      domain,
      service,
      notes
    } = req.body;

    // Validate required fields
    if (!name || !email || !company || !domain || !service) {
      return res.status(400).json({ 
        error: 'Missing required fields',
        required: ['name', 'email', 'company', 'domain', 'service']
      });
    }

    // Generate submission ID
    const timestamp = new Date().toISOString();
    const submissionId = `SUB-${Date.now().toString().slice(-6)}`;

    // ─────────────────────────────────────────────
    // SAVE TO GOOGLE SHEETS
    // ─────────────────────────────────────────────
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
    const sheet = doc.sheetsByIndex[0]; // First sheet

    // Add row
    await sheet.addRow({
      'Submission ID': submissionId,
      'Timestamp': timestamp,
      'Status': 'new',
      'Name': name,
      'Role': role || '',
      'Email': email,
      'Company': company,
      'Phone': phone || '',
      'Domain': domain,
      'Service': service,
      'Notes': notes || '',
    });

    console.log(`✓ Saved to Google Sheets: ${submissionId}`);

    // ─────────────────────────────────────────────
    // SEND CONFIRMATION EMAIL
    // ─────────────────────────────────────────────
    const serviceLabel = {
      snapshot: 'Security Snapshot — ₹9,999',
      vapt: 'Web App VAPT — ₹24,999',
      custom: 'Custom Engagement',
      unsure: 'Help Me Decide',
    }[service] || service;

    const emailHtml = `
<!DOCTYPE html>
<html>
<head>
  <style>
    body { font-family: 'Helvetica Neue', Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; }
    .header { background: #07080b; color: #e8ecf0; padding: 32px 24px; border-top: 3px solid #00e87a; }
    .logo { font-size: 24px; font-weight: bold; letter-spacing: 2px; }
    .logo .accent { color: #00e87a; }
    .content { padding: 32px 24px; background: #f9fafb; }
    .content h2 { color: #07080b; margin-top: 0; }
    .info-table { width: 100%; background: white; border: 1px solid #e5e7eb; border-radius: 4px; margin: 20px 0; }
    .info-row { display: flex; border-bottom: 1px solid #e5e7eb; }
    .info-row:last-child { border-bottom: none; }
    .info-label { width: 140px; padding: 12px 16px; background: #f3f4f6; font-weight: 600; font-size: 13px; color: #6b7280; }
    .info-value { padding: 12px 16px; font-size: 14px; }
    .cta { display: inline-block; background: #00e87a; color: #07080b; padding: 14px 28px; text-decoration: none; font-weight: bold; border-radius: 4px; margin: 20px 0; }
    .footer { padding: 24px; text-align: center; color: #6b7280; font-size: 13px; }
    .footer a { color: #00e87a; text-decoration: none; }
  </style>
</head>
<body>
  <div class="header">
    <div class="logo">AEGIS<span class="accent">CORE</span></div>
  </div>
  <div class="content">
    <h2>Assessment Request Received ✓</h2>
    <p>Hi ${name},</p>
    <p>Thank you for requesting a security assessment from AegisCore. We've received your submission and will get back to you within <strong>24 hours</strong> with:</p>
    <ul>
      <li>Scoping confirmation</li>
      <li>Authorization agreement to sign</li>
      <li>Timeline and next steps</li>
    </ul>

    <div class="info-table">
      <div class="info-row">
        <div class="info-label">Submission ID</div>
        <div class="info-value">${submissionId}</div>
      </div>
      <div class="info-row">
        <div class="info-label">Company</div>
        <div class="info-value">${company}</div>
      </div>
      <div class="info-row">
        <div class="info-label">Domain</div>
        <div class="info-value">${domain}</div>
      </div>
      <div class="info-row">
        <div class="info-label">Service</div>
        <div class="info-value">${serviceLabel}</div>
      </div>
    </ul>

    <p style="margin-top: 28px;"><strong>What happens next?</strong></p>
    <p>Our security team will review your submission and reach out via email (<strong>${email}</strong>) with a detailed scope and authorization agreement. No testing will begin until you've signed the agreement.</p>

    <p style="margin-top: 24px; font-size: 13px; color: #6b7280;">Questions? Reply to this email or contact us at <a href="mailto:hello@aegiscore.in" style="color: #00e87a;">hello@aegiscore.in</a></p>
  </div>
  <div class="footer">
    <p><strong>AegisCore</strong> — Security Testing for Startups</p>
    <p><a href="mailto:hello@aegiscore.in">hello@aegiscore.in</a> • aegiscore.in</p>
    <p style="font-size: 11px; color: #9ca3af; margin-top: 16px;">
      This email was sent because you submitted an assessment request at aegiscore.in.<br>
      If you didn't make this request, you can safely ignore this email.
    </p>
  </div>
</body>
</html>
    `;

    try {
      await resend.emails.send({
        from: 'AegisCore <hello@aegiscore.in>', // Update with your verified domain
        to: email,
        subject: `Assessment Request Received — ${submissionId}`,
        html: emailHtml,
      });
      console.log(`✓ Confirmation email sent to ${email}`);
    } catch (emailError) {
      console.error('Email send failed:', emailError);
      // Don't fail the request if email fails
    }

    // ─────────────────────────────────────────────
    // SEND INTERNAL NOTIFICATION
    // ─────────────────────────────────────────────
    const internalNotif = `
<!DOCTYPE html>
<html>
<head>
  <style>
    body { font-family: monospace; background: #07080b; color: #e8ecf0; padding: 20px; }
    .container { max-width: 600px; margin: 0 auto; background: #0e1016; border: 1px solid #1e2330; border-radius: 4px; padding: 24px; }
    h2 { color: #00e87a; margin-top: 0; }
    .field { margin: 12px 0; }
    .label { color: #6b7589; font-size: 12px; text-transform: uppercase; }
    .value { color: #e8ecf0; font-size: 14px; margin-top: 4px; }
    .cta { display: inline-block; background: #00e87a; color: #07080b; padding: 12px 24px; text-decoration: none; font-weight: bold; border-radius: 4px; margin-top: 20px; }
  </style>
</head>
<body>
  <div class="container">
    <h2>🔔 New Assessment Request</h2>
    <div class="field"><div class="label">ID</div><div class="value">${submissionId}</div></div>
    <div class="field"><div class="label">Company</div><div class="value">${company}</div></div>
    <div class="field"><div class="label">Contact</div><div class="value">${name} — ${role || 'No role'}</div></div>
    <div class="field"><div class="label">Email</div><div class="value">${email}</div></div>
    <div class="field"><div class="label">Phone</div><div class="value">${phone || 'Not provided'}</div></div>
    <div class="field"><div class="label">Domain</div><div class="value">${domain}</div></div>
    <div class="field"><div class="label">Service</div><div class="value">${serviceLabel}</div></div>
    <div class="field"><div class="label">Notes</div><div class="value">${notes || 'None'}</div></div>
    <a href="YOUR_ADMIN_DASHBOARD_URL" class="cta">View in Dashboard →</a>
  </div>
</body>
</html>
    `;

    try {
      await resend.emails.send({
        from: 'AegisCore Notifications <notifications@aegiscore.in>',
        to: process.env.ADMIN_EMAIL, // Your email
        subject: `🔔 New Request: ${company} — ${serviceLabel}`,
        html: internalNotif,
      });
      console.log('✓ Admin notification sent');
    } catch (notifError) {
      console.error('Admin notification failed:', notifError);
    }

    // ─────────────────────────────────────────────
    // RESPONSE
    // ─────────────────────────────────────────────
    return res.status(200).json({
      success: true,
      submissionId,
      message: 'Request received. Check your email for confirmation.',
    });

  } catch (error) {
    console.error('Submission error:', error);
    return res.status(500).json({
      error: 'Submission failed',
      message: error.message,
    });
  }
};
