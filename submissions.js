// api/submissions.js - Read submissions from Google Sheets
// Used by admin dashboard to display all form submissions

const { GoogleSpreadsheet } = require('google-spreadsheet');
const { JWT } = require('google-auth-library');

module.exports = async (req, res) => {
  // Simple password-based auth
  const authHeader = req.headers.authorization;
  const expectedAuth = `Bearer ${process.env.ADMIN_PASSWORD || 'aegis2026'}`;
  
  if (authHeader !== expectedAuth) {
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
    const sheet = doc.sheetsByIndex[0]; // First sheet
    const rows = await sheet.getRows();

    // Map rows to submission objects
    const submissions = rows.map(row => ({
      id: row.get('Submission ID') || '',
      timestamp: row.get('Timestamp') || '',
      status: row.get('Status') || 'new',
      name: row.get('Name') || '',
      role: row.get('Role') || '',
      email: row.get('Email') || '',
      company: row.get('Company') || '',
      phone: row.get('Phone') || '',
      domain: row.get('Domain') || '',
      service: row.get('Service') || '',
      notes: row.get('Notes') || '',
      rowIndex: row.rowIndex, // For future updates
    }));

    // Sort by timestamp descending (newest first)
    submissions.sort((a, b) => {
      return new Date(b.timestamp) - new Date(a.timestamp);
    });

    return res.status(200).json({ 
      success: true,
      count: submissions.length,
      submissions 
    });

  } catch (error) {
    console.error('Read submissions error:', error);
    return res.status(500).json({ 
      error: 'Failed to read submissions',
      message: error.message 
    });
  }
};
