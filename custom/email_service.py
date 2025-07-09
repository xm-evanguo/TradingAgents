#!/usr/bin/env python3
"""
Email Service for TradingAgents

This module provides email notification functionality for trading analysis results.
Supports HTML and plain text emails with analysis summaries.

Usage:
    from email_service import EmailService
    
    config = {
        "smtp_server": "smtp.gmail.com",
        "smtp_port": 587,
        "sender_email": "your-email@gmail.com",
        "sender_password": "your-app-password",
        "recipients": ["recipient@example.com"]
    }
    
    service = EmailService(config)
    service.send_analysis_results(summary_data)
"""

import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from typing import Dict, List, Any, Optional
import logging
import json

logger = logging.getLogger(__name__)


class EmailService:
    """Email service for sending trading analysis notifications."""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize email service with configuration.
        
        Args:
            config: Email configuration dictionary containing:
                - smtp_server: SMTP server address
                - smtp_port: SMTP server port (default: 587)
                - sender_email: Sender email address
                - sender_password: Sender email password/app password
                - recipients: List of recipient email addresses
                - subject_template: Optional subject template (default: "TradingAgents Analysis Results - {date}")
                - use_tls: Whether to use TLS (default: True)
        """
        self.smtp_server = config.get('smtp_server')
        self.smtp_port = config.get('smtp_port', 587)
        self.sender_email = config.get('sender_email')
        self.sender_password = config.get('sender_password')
        self.recipients = config.get('recipients', [])
        self.subject_template = config.get('subject_template', "TradingAgents Analysis Results - {date}")
        self.use_tls = config.get('use_tls', True)
        
        # Validate configuration
        self._validate_config()
    
    def _validate_config(self):
        """Validate email configuration."""
        required_fields = ['smtp_server', 'sender_email', 'sender_password', 'recipients']
        missing_fields = [field for field in required_fields if not getattr(self, field)]
        
        if missing_fields:
            raise ValueError(f"Missing required email configuration fields: {missing_fields}")
        
        if not self.recipients:
            raise ValueError("At least one recipient email address is required")
        
        # Validate email addresses (basic check)
        all_emails = [self.sender_email] + self.recipients
        for email in all_emails:
            if '@' not in email or '.' not in email:
                raise ValueError(f"Invalid email address: {email}")
    
    def send_email(
        self,
        subject: str,
        body_text: str,
        body_html: Optional[str] = None,
        recipients: Optional[List[str]] = None
    ) -> bool:
        """
        Send an email with the specified content.
        
        Args:
            subject: Email subject
            body_text: Plain text email body
            body_html: Optional HTML email body
            recipients: Optional list of recipients (default: use config recipients)
            
        Returns:
            True if email sent successfully, False otherwise
        """
        try:
            # Use provided recipients or default
            email_recipients = recipients or self.recipients
            
            # Create message
            message = MIMEMultipart("alternative")
            message["Subject"] = subject
            message["From"] = self.sender_email
            message["To"] = ", ".join(email_recipients)
            
            # Add text part
            text_part = MIMEText(body_text, "plain")
            message.attach(text_part)
            
            # Add HTML part if provided
            if body_html:
                html_part = MIMEText(body_html, "html")
                message.attach(html_part)
            
            # Create SMTP session
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                if self.use_tls:
                    server.starttls()
                
                server.login(self.sender_email, self.sender_password)
                
                # Send email
                server.sendmail(
                    self.sender_email,
                    email_recipients,
                    message.as_string()
                )
            
            logger.info(f"Email sent successfully to {len(email_recipients)} recipients")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email: {e}")
            return False
    
    def send_analysis_results(self, summary: Dict[str, Any]) -> bool:
        """
        Send trading analysis results via email.
        
        Args:
            summary: Analysis summary dictionary
            
        Returns:
            True if email sent successfully, False otherwise
        """
        try:
            # Generate subject
            analysis_date = summary.get('analysis_date', datetime.now().strftime('%Y-%m-%d'))
            subject = self.subject_template.format(date=analysis_date)
            
            # Generate email content
            body_text = self._generate_text_body(summary)
            body_html = self._generate_html_body(summary)
            
            return self.send_email(subject, body_text, body_html)
            
        except Exception as e:
            logger.error(f"Failed to send analysis results email: {e}")
            return False
    
    def _generate_text_body(self, summary: Dict[str, Any]) -> str:
        """Generate plain text email body from analysis summary."""
        lines = []
        
        # Header
        lines.append("TradingAgents Analysis Results")
        lines.append("=" * 40)
        lines.append("")
        
        # Summary stats
        lines.append(f"Analysis Date: {summary.get('analysis_date', 'N/A')}")
        lines.append(f"Total Analyzed: {summary.get('total_analyzed', 0)}")
        lines.append(f"Successful: {summary.get('successful', 0)}")
        lines.append(f"Failed: {summary.get('failed', 0)}")
        lines.append(f"Success Rate: {summary.get('success_rate', 0):.1f}%")
        lines.append("")
        
        # Trading signals
        signals = summary.get('signals', {})
        
        if signals.get('buy'):
            lines.append(f"🟢 BUY SIGNALS ({len(signals['buy'])}): {', '.join(signals['buy'])}")
        
        if signals.get('sell'):
            lines.append(f"🔴 SELL SIGNALS ({len(signals['sell'])}): {', '.join(signals['sell'])}")
        
        if signals.get('hold'):
            lines.append(f"🟡 HOLD SIGNALS ({len(signals['hold'])}): {', '.join(signals['hold'])}")
        
        lines.append("")
        
        # Failed tickers
        failed_tickers = summary.get('failed_tickers', [])
        if failed_tickers:
            lines.append(f"⚠️  FAILED ANALYSIS ({len(failed_tickers)}): {', '.join(failed_tickers)}")
            lines.append("")
        
        # Detailed results
        lines.append("Detailed Results:")
        lines.append("-" * 20)
        
        for result in summary.get('detailed_results', []):
            ticker = result.get('ticker', 'N/A')
            success = result.get('success', False)
            
            if success:
                decision = result.get('decision', {})
                action = decision.get('action', 'N/A')
                confidence = decision.get('confidence', 'N/A')
                reasoning = decision.get('reasoning', 'N/A')
                
                lines.append(f"{ticker}: ✅ {action} (Confidence: {confidence})")
                if reasoning and reasoning != 'N/A':
                    # Truncate long reasoning
                    short_reasoning = reasoning[:100] + "..." if len(reasoning) > 100 else reasoning
                    lines.append(f"  Reasoning: {short_reasoning}")
            else:
                error = result.get('error', 'Unknown error')
                lines.append(f"{ticker}: ❌ Failed - {error}")
            
            lines.append("")
        
        # Footer
        lines.append("-" * 40)
        lines.append(f"Generated at: {summary.get('timestamp', datetime.now().isoformat())}")
        lines.append("Powered by TradingAgents")
        
        return "\n".join(lines)
    
    def _generate_html_body(self, summary: Dict[str, Any]) -> str:
        """Generate HTML email body from analysis summary."""
        # CSS styles
        css = """
        <style>
            body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
            .header { background-color: #2c3e50; color: white; padding: 20px; text-align: center; }
            .summary { background-color: #ecf0f1; padding: 15px; margin: 20px 0; border-radius: 5px; }
            .signals { margin: 20px 0; }
            .signal-group { margin: 10px 0; padding: 10px; border-radius: 5px; }
            .buy { background-color: #d5f4e6; border-left: 4px solid #27ae60; }
            .sell { background-color: #fadbd8; border-left: 4px solid #e74c3c; }
            .hold { background-color: #fef9e7; border-left: 4px solid #f39c12; }
            .failed { background-color: #fdedec; border-left: 4px solid #e74c3c; }
            .results-table { width: 100%; border-collapse: collapse; margin: 20px 0; }
            .results-table th, .results-table td { padding: 10px; text-align: left; border-bottom: 1px solid #ddd; }
            .results-table th { background-color: #34495e; color: white; }
            .success { color: #27ae60; font-weight: bold; }
            .failure { color: #e74c3c; font-weight: bold; }
            .footer { background-color: #34495e; color: white; padding: 10px; text-align: center; margin-top: 20px; }
        </style>
        """
        
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>TradingAgents Analysis Results</title>
            {css}
        </head>
        <body>
            <div class="header">
                <h1>TradingAgents Analysis Results</h1>
                <p>Analysis Date: {summary.get('analysis_date', 'N/A')}</p>
            </div>
            
            <div class="summary">
                <h3>Summary Statistics</h3>
                <p><strong>Total Analyzed:</strong> {summary.get('total_analyzed', 0)}</p>
                <p><strong>Successful:</strong> {summary.get('successful', 0)}</p>
                <p><strong>Failed:</strong> {summary.get('failed', 0)}</p>
                <p><strong>Success Rate:</strong> {summary.get('success_rate', 0):.1f}%</p>
            </div>
        """
        
        # Trading signals
        signals = summary.get('signals', {})
        
        if any(signals.values()):
            html += '<div class="signals"><h3>Trading Signals</h3>'
            
            if signals.get('buy'):
                html += f'''
                <div class="signal-group buy">
                    <strong>🟢 BUY SIGNALS ({len(signals['buy'])})</strong><br>
                    {', '.join(signals['buy'])}
                </div>
                '''
            
            if signals.get('sell'):
                html += f'''
                <div class="signal-group sell">
                    <strong>🔴 SELL SIGNALS ({len(signals['sell'])})</strong><br>
                    {', '.join(signals['sell'])}
                </div>
                '''
            
            if signals.get('hold'):
                html += f'''
                <div class="signal-group hold">
                    <strong>🟡 HOLD SIGNALS ({len(signals['hold'])})</strong><br>
                    {', '.join(signals['hold'])}
                </div>
                '''
            
            html += '</div>'
        
        # Failed tickers
        failed_tickers = summary.get('failed_tickers', [])
        if failed_tickers:
            html += f'''
            <div class="signal-group failed">
                <strong>⚠️ FAILED ANALYSIS ({len(failed_tickers)})</strong><br>
                {', '.join(failed_tickers)}
            </div>
            '''
        
        # Detailed results table
        html += '''
        <h3>Detailed Results</h3>
        <table class="results-table">
            <tr>
                <th>Ticker</th>
                <th>Status</th>
                <th>Action</th>
                <th>Confidence</th>
                <th>Notes</th>
            </tr>
        '''
        
        for result in summary.get('detailed_results', []):
            ticker = result.get('ticker', 'N/A')
            success = result.get('success', False)
            
            if success:
                decision = result.get('decision', {})
                action = decision.get('action', 'N/A')
                confidence = decision.get('confidence', 'N/A')
                reasoning = decision.get('reasoning', '')
                short_reasoning = reasoning[:100] + "..." if len(reasoning) > 100 else reasoning
                
                html += f'''
                <tr>
                    <td><strong>{ticker}</strong></td>
                    <td class="success">✅ Success</td>
                    <td>{action}</td>
                    <td>{confidence}</td>
                    <td>{short_reasoning}</td>
                </tr>
                '''
            else:
                error = result.get('error', 'Unknown error')
                html += f'''
                <tr>
                    <td><strong>{ticker}</strong></td>
                    <td class="failure">❌ Failed</td>
                    <td>-</td>
                    <td>-</td>
                    <td>{error}</td>
                </tr>
                '''
        
        html += '''
        </table>
        
        <div class="footer">
            <p>Generated at: ''' + summary.get('timestamp', datetime.now().isoformat()) + '''</p>
            <p>Powered by TradingAgents</p>
        </div>
        
        </body>
        </html>
        '''
        
        return html
    
    def send_test_email(self) -> bool:
        """Send a test email to verify configuration."""
        subject = "TradingAgents Email Service Test"
        body = "This is a test email from TradingAgents email service. If you received this, the configuration is working correctly."
        
        return self.send_email(subject, body)


def main():
    """Command line interface for testing email service."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Email service test")
    parser.add_argument("--config", required=True, help="Email configuration JSON file")
    parser.add_argument("--test", action="store_true", help="Send test email")
    
    args = parser.parse_args()
    
    try:
        with open(args.config, 'r') as f:
            config = json.load(f)
        
        service = EmailService(config)
        
        if args.test:
            success = service.send_test_email()
            if success:
                print("✅ Test email sent successfully!")
            else:
                print("❌ Failed to send test email")
                return 1
        
        return 0
        
    except Exception as e:
        print(f"Error: {e}")
        return 1


if __name__ == "__main__":
    exit(main())
