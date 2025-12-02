import React from 'react';
import './PrivacyPolicy.css';

/**
 * ✅ GDPR: Privacy Policy Page
 * Legal requirement under GDPR Article 13 & 14
 * 
 * Discloses:
 * - Data collection practices
 * - Usage and sharing
 * - Retention periods
 * - User rights (access, deletion, portability)
 * - Contact information
 */
const PrivacyPolicy = () => {
  const lastUpdated = "November 17, 2025";
  const companyName = "KnowAllEdge";
  const companyEmail = "privacy@KNOWALLEDGE.com";
  
  return (
    <div className="privacy-policy-container">
      <div className="privacy-policy-content">
        <h1>Privacy Policy</h1>
        <p className="last-updated">Last Updated: {lastUpdated}</p>

        <section className="policy-section">
          <h2>1. Introduction</h2>
          <p>
            Welcome to {companyName}. We respect your privacy and are committed to protecting 
            your personal data. This privacy policy explains how we collect, use, store, and 
            protect your information when you use our service.
          </p>
          <p>
            This policy complies with the EU General Data Protection Regulation (GDPR), California 
            Consumer Privacy Act (CCPA), and other applicable privacy laws.
          </p>
        </section>

        <section className="policy-section">
          <h2>2. Data Controller</h2>
          <p>
            <strong>{companyName}</strong> is the data controller responsible for your personal data.
          </p>
          <p>Contact us at: <a href={`mailto:${companyEmail}`}>{companyEmail}</a></p>
        </section>

        <section className="policy-section">
          <h2>3. What Data We Collect</h2>
          
          <h3>3.1 Information You Provide</h3>
          <ul>
            <li><strong>Account Data:</strong> Email address, username, password (encrypted)</li>
            <li><strong>Profile Data:</strong> Optional display name, preferences, settings</li>
            <li><strong>User Content:</strong> Topics, queries, interaction history</li>
          </ul>

          <h3>3.2 Automatically Collected Data</h3>
          <ul>
            <li><strong>Usage Data:</strong> Pages visited, features used, interaction patterns</li>
            <li><strong>Technical Data:</strong> IP address, browser type, device information</li>
            <li><strong>Analytics Data:</strong> Performance metrics, error logs (anonymized)</li>
            <li><strong>Cookies:</strong> See our Cookie Policy for details</li>
          </ul>

          <h3>3.3 Data We Do NOT Collect</h3>
          <ul>
            <li>Precise geolocation without consent</li>
            <li>Sensitive personal data (health, biometrics, etc.)</li>
            <li>Payment information (we don't process payments directly)</li>
          </ul>
        </section>

        <section className="policy-section">
          <h2>4. How We Use Your Data</h2>
          
          <h3>4.1 Legal Bases (GDPR)</h3>
          <p>We process your data based on:</p>
          <ul>
            <li><strong>Contract:</strong> To provide our services to you</li>
            <li><strong>Consent:</strong> For analytics and optional features (you can withdraw anytime)</li>
            <li><strong>Legitimate Interest:</strong> To improve our service and prevent fraud</li>
            <li><strong>Legal Obligation:</strong> To comply with laws and regulations</li>
          </ul>

          <h3>4.2 Specific Uses</h3>
          <ul>
            <li><strong>Service Delivery:</strong> Process your queries, generate AI responses</li>
            <li><strong>Authentication:</strong> Verify your identity, maintain sessions</li>
            <li><strong>Personalization:</strong> Remember your preferences, customize experience</li>
            <li><strong>Analytics:</strong> Understand usage patterns, improve features (anonymized)</li>
            <li><strong>Security:</strong> Detect fraud, prevent abuse, protect users</li>
            <li><strong>Communication:</strong> Send service updates, respond to inquiries</li>
          </ul>
        </section>

        <section className="policy-section">
          <h2>5. Third-Party Data Sharing</h2>
          
          <h3>5.1 Google Gemini AI</h3>
          <p className="highlight-warning">
            <strong>⚠️ Important:</strong> When you use our AI features, your queries are sent to 
            Google Gemini API for processing. Google may process this data according to their own 
            <a href="https://policies.google.com/privacy" target="_blank" rel="noopener noreferrer">
              Privacy Policy
            </a>.
          </p>
          <ul>
            <li><strong>Data Shared:</strong> Your queries, context for AI responses</li>
            <li><strong>Purpose:</strong> Generate intelligent responses</li>
            <li><strong>Retention:</strong> Per Google's data retention policy</li>
            <li><strong>Control:</strong> You can opt out by not using AI features</li>
          </ul>

          <h3>5.2 Other Service Providers</h3>
          <p>We may share data with:</p>
          <ul>
            <li><strong>Hosting Providers:</strong> To store and serve your data securely</li>
            <li><strong>Analytics Services:</strong> To understand usage (anonymized data only)</li>
            <li><strong>Security Services:</strong> To protect against threats</li>
          </ul>
          <p>All third parties are contractually required to protect your data and use it only for specified purposes.</p>

          <h3>5.3 We Do NOT Sell Your Data</h3>
          <p className="highlight-success">
            <strong>✅ We never sell, rent, or trade your personal information to third parties for marketing purposes.</strong>
          </p>
        </section>

        <section className="policy-section">
          <h2>6. Data Retention</h2>
          
          <h3>6.1 Retention Periods</h3>
          <table className="retention-table">
            <thead>
              <tr>
                <th>Data Type</th>
                <th>Retention Period</th>
                <th>Reason</th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <td>Account Data</td>
                <td>Until account deletion</td>
                <td>Service delivery</td>
              </tr>
              <tr>
                <td>User Content</td>
                <td>30 days after deletion</td>
                <td>Backup & recovery</td>
              </tr>
              <tr>
                <td>Session Data</td>
                <td>7 days</td>
                <td>Security & analytics</td>
              </tr>
              <tr>
                <td>Cache Data</td>
                <td>24 hours</td>
                <td>Performance</td>
              </tr>
              <tr>
                <td>Error Logs</td>
                <td>90 days</td>
                <td>Debugging & improvement</td>
              </tr>
              <tr>
                <td>Analytics Data</td>
                <td>365 days (anonymized)</td>
                <td>Long-term insights</td>
              </tr>
            </tbody>
          </table>

          <h3>6.2 Automatic Deletion</h3>
          <p>
            Data is automatically deleted after retention periods expire. You can request earlier 
            deletion by exercising your rights (see Section 8).
          </p>
        </section>

        <section className="policy-section">
          <h2>7. Data Security</h2>
          <p>We implement industry-standard security measures:</p>
          <ul>
            <li><strong>Encryption:</strong> All data encrypted at rest (AES-256) and in transit (TLS 1.3)</li>
            <li><strong>Access Control:</strong> Role-based access, multi-factor authentication</li>
            <li><strong>Monitoring:</strong> 24/7 security monitoring, intrusion detection</li>
            <li><strong>Auditing:</strong> Regular security audits and penetration testing</li>
            <li><strong>Incident Response:</strong> Documented breach notification procedures</li>
          </ul>
          <p>
            Despite our efforts, no system is 100% secure. If we detect a breach affecting your data, 
            we will notify you within 72 hours as required by law.
          </p>
        </section>

        <section className="policy-section">
          <h2>8. Your Rights (GDPR & CCPA)</h2>
          
          <h3>8.1 Right to Access</h3>
          <p>
            Request a copy of all personal data we hold about you. 
            <a href="/settings#data-export"> Export your data here</a>.
          </p>

          <h3>8.2 Right to Rectification</h3>
          <p>
            Correct inaccurate or incomplete data. 
            <a href="/settings#profile"> Update your profile here</a>.
          </p>

          <h3>8.3 Right to Erasure ("Right to be Forgotten")</h3>
          <p>
            Request deletion of your personal data. 
            <a href="/settings#delete-account"> Delete your account here</a>.
          </p>
          <p className="highlight-warning">
            <strong>Note:</strong> Some data may be retained for legal compliance (e.g., financial records, 
            legal disputes) as permitted by law.
          </p>

          <h3>8.4 Right to Data Portability</h3>
          <p>
            Receive your data in a machine-readable format (JSON). 
            <a href="/settings#data-export"> Download here</a>.
          </p>

          <h3>8.5 Right to Object</h3>
          <p>
            Object to processing based on legitimate interest. 
            Contact us at <a href={`mailto:${companyEmail}`}>{companyEmail}</a>.
          </p>

          <h3>8.6 Right to Restrict Processing</h3>
          <p>
            Request temporary restriction of processing while we verify accuracy or legitimacy.
          </p>

          <h3>8.7 Right to Withdraw Consent</h3>
          <p>
            Withdraw consent for optional data processing anytime in 
            <a href="/settings#privacy"> Privacy Settings</a>.
          </p>

          <h3>8.8 Right to Lodge a Complaint</h3>
          <p>
            File a complaint with your local data protection authority if you believe we've violated 
            your rights. EU users can contact their 
            <a href="https://edpb.europa.eu/about-edpb/about-edpb/members_en" target="_blank" rel="noopener noreferrer">
              national supervisory authority
            </a>.
          </p>
        </section>

        <section className="policy-section">
          <h2>9. Cookies and Tracking</h2>
          <p>We use cookies for:</p>
          <ul>
            <li><strong>Essential:</strong> Authentication, security (cannot be disabled)</li>
            <li><strong>Functional:</strong> Remember preferences (optional, requires consent)</li>
            <li><strong>Analytics:</strong> Understand usage patterns (optional, anonymized)</li>
            <li><strong>Performance:</strong> Optimize loading times (optional)</li>
          </ul>
          <p>
            Manage your cookie preferences in our 
            <a href="#" onClick={(e) => { e.preventDefault(); window.location.reload(); }}> Cookie Banner</a>.
          </p>
        </section>

        <section className="policy-section">
          <h2>10. International Data Transfers</h2>
          <p>
            Your data may be transferred to and processed in countries outside your jurisdiction. 
            We ensure adequate safeguards:
          </p>
          <ul>
            <li><strong>EU-US:</strong> Standard Contractual Clauses (SCCs) or adequacy decisions</li>
            <li><strong>Other:</strong> Binding Corporate Rules or equivalent protections</li>
          </ul>
        </section>

        <section className="policy-section">
          <h2>11. Children's Privacy</h2>
          <p>
            Our service is not directed at children under 16. We do not knowingly collect data from 
            children. If you believe we've collected data from a child, contact us immediately at 
            <a href={`mailto:${companyEmail}`}>{companyEmail}</a>.
          </p>
        </section>

        <section className="policy-section">
          <h2>12. Changes to This Policy</h2>
          <p>
            We may update this policy periodically. Material changes will be notified via:
          </p>
          <ul>
            <li>Email to your registered address</li>
            <li>Prominent notice on our website</li>
            <li>Updated "Last Updated" date at the top</li>
          </ul>
          <p>
            Continued use after changes constitutes acceptance. If you disagree, please stop using 
            our service and request account deletion.
          </p>
        </section>

        <section className="policy-section">
          <h2>13. Contact Us</h2>
          <p>For privacy questions or to exercise your rights:</p>
          <ul>
            <li><strong>Email:</strong> <a href={`mailto:${companyEmail}`}>{companyEmail}</a></li>
            <li><strong>Data Protection Officer:</strong> dpo@KNOWALLEDGE.com</li>
            <li><strong>Response Time:</strong> Within 30 days (GDPR requirement)</li>
          </ul>
          <p>
            For urgent security issues: <a href="mailto:security@KNOWALLEDGE.com">security@KNOWALLEDGE.com</a>
          </p>
        </section>

        <section className="policy-section legal-footer">
          <h2>14. Legal Information</h2>
          <p>
            <strong>Governing Law:</strong> This policy is governed by the laws of [Your Jurisdiction].
          </p>
          <p>
            <strong>Compliance:</strong> GDPR (EU), CCPA (California), ePrivacy Directive, PIPEDA (Canada).
          </p>
          <p>
            <strong>Effective Date:</strong> {lastUpdated}
          </p>
        </section>

        <div className="policy-actions">
          <a href="/settings#data-export" className="btn btn-primary">
            Export My Data
          </a>
          <a href="/settings#delete-account" className="btn btn-danger">
            Delete My Account
          </a>
          <a href="/" className="btn btn-secondary">
            Back to Home
          </a>
        </div>
      </div>
    </div>
  );
};

export default PrivacyPolicy;
