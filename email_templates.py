# =============================================================================
# EMAIL TEMPLATES - email_templates.py
# =============================================================================
# Day 3: HTML Email Digest Templates with Interactive Buttons
# 
# This module creates beautiful, responsive HTML email templates that:
# 1. Work perfectly in Gmail (your primary target)
# 2. Showcase all your sophisticated AI features
# 3. Use progressive disclosure to balance information hierarchy
# 4. Include interactive buttons for send/edit/archive actions
# 5. Are mobile-optimized and email-client compatible
#
# INTEGRATION WITH YOUR AI SYSTEM:
# - Uses data structure from CompleteEmailAgent.process_daily_emails()
# - Displays advanced_reply, contextual_insights, tone_analysis, etc.
# - Preserves all sophisticated AI features you've built
# =============================================================================

import re
from datetime import datetime
from typing import Dict, List, Any, Optional
from urllib.parse import quote

# =============================================================================
# EMAIL STYLING CONFIGURATION
# =============================================================================

# Gmail-optimized color scheme (email-safe hex codes)
COLORS = {
    'primary_navy': '#1a365d',
    'high_priority': '#dc2626',
    'medium_priority': '#d97706', 
    'low_priority': '#6b7280',
    'success_green': '#059669',
    'edit_blue': '#2563eb',
    'background': '#f8fafc',
    'text_dark': '#1f2937',
    'text_medium': '#4b5563',
    'text_light': '#6b7280',
    'border_light': '#e5e7eb',
    'card_bg': '#ffffff',
    'insights_bg': '#f0f7ff',
    'urgent_bg': '#fef2f2',
    'medium_bg': '#fffbf0',
    'low_bg': '#f0fff4'
}

# Typography settings for email compatibility
TYPOGRAPHY = {
    'font_family': '-apple-system, BlinkMacSystemFont, "Segoe UI", Arial, sans-serif',
    'heading_size': '20px',
    'body_size': '14px',
    'small_size': '12px',
    'button_size': '14px',
    'line_height': '1.5'
}

# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def calculate_time_ago(date_str: str) -> str:
    """Calculate human-readable time ago from date string"""
    try:
        if isinstance(date_str, str):
            # Try to parse various date formats
            for fmt in ['%Y-%m-%dT%H:%M:%S.%f', '%Y-%m-%dT%H:%M:%S', '%a, %d %b %Y %H:%M:%S %z']:
                try:
                    email_date = datetime.strptime(date_str.split('+')[0].split('Z')[0], fmt)
                    break
                except ValueError:
                    continue
            else:
                return "recently"
        else:
            email_date = date_str
        
        now = datetime.now()
        diff = now - email_date
        
        if diff.days > 0:
            return f"{diff.days}d ago"
        elif diff.seconds > 3600:
            hours = diff.seconds // 3600
            return f"{hours}h ago"
        elif diff.seconds > 60:
            minutes = diff.seconds // 60
            return f"{minutes}m ago"
        else:
            return "just now"
    except:
        return "recently"

def truncate_text(text: str, max_length: int = 100) -> str:
    """Truncate text to specified length with ellipsis"""
    if not text:
        return ""
    
    if len(text) <= max_length:
        return text
    
    # Try to break at word boundary
    truncated = text[:max_length]
    last_space = truncated.rfind(' ')
    
    if last_space > max_length * 0.8:  # If we can break reasonably close to limit
        return truncated[:last_space] + "..."
    else:
        return truncated + "..."

def get_priority_indicator(priority_level: str) -> Dict[str, str]:
    """Get priority indicator styling and text"""
    indicators = {
        'High': {'emoji': '🔥', 'color': COLORS['high_priority'], 'text': 'HIGH PRIORITY'},
        'Medium': {'emoji': '⚡', 'color': COLORS['medium_priority'], 'text': 'MEDIUM PRIORITY'},
        'Low': {'emoji': '💤', 'color': COLORS['low_priority'], 'text': 'LOW PRIORITY'}
    }
    return indicators.get(priority_level, indicators['Medium'])

# =============================================================================
# CORE EMAIL TEMPLATE FUNCTIONS
# =============================================================================

def create_digest_email(digest_data: Dict[str, Any], base_url: str) -> str:
    """
    Create the main HTML digest email integrating all your AI features
    
    This showcases your sophisticated AI system while maintaining
    clean mobile-friendly design with progressive disclosure.
    """
    
    print("📧 Creating HTML digest email with AI features...")
    
    # Extract data from your AI system
    high_priority = digest_data.get('high_priority', [])
    medium_priority = digest_data.get('medium_priority', [])
    low_priority = digest_data.get('low_priority', [])
    processing_summary = digest_data.get('processing_summary', {})
    user_id = digest_data.get('user_id', 'unknown')
    user_prefs = digest_data.get('user_preferences', {})
    
    # Generate date header
    today = datetime.now()
    date_header = today.strftime("%A, %B %d, %Y")
    
    # Start building HTML
    html = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="x-apple-disable-message-reformatting">
    <title>VoxMail Daily Digest</title>
    <!--[if mso]>
    <noscript>
        <xml>
            <o:OfficeDocumentSettings>
                <o:AllowPNG/>
                <o:PixelsPerInch>96</o:PixelsPerInch>
            </o:OfficeDocumentSettings>
        </xml>
    </noscript>
    <![endif]-->
    <style>
        /* Email-safe CSS styles */
        body {{
            margin: 0;
            padding: 0;
            background-color: {COLORS['background']};
            font-family: {TYPOGRAPHY['font_family']};
            font-size: {TYPOGRAPHY['body_size']};
            line-height: {TYPOGRAPHY['line_height']};
            color: {COLORS['text_dark']};
            -webkit-text-size-adjust: 100%;
            -ms-text-size-adjust: 100%;
        }}
        table {{
            border-collapse: collapse;
            mso-table-lspace: 0pt;
            mso-table-rspace: 0pt;
        }}
        .container {{
            max-width: 600px;
            margin: 0 auto;
            background-color: {COLORS['card_bg']};
        }}
        .header {{
            background: linear-gradient(135deg, {COLORS['primary_navy']} 0%, #2563eb 100%);
            color: white;
            padding: 24px 20px;
            text-align: center;
        }}
        .content {{
            padding: 20px;
        }}
        .ai-highlights {{
            background-color: {COLORS['insights_bg']};
            border-radius: 8px;
            padding: 16px;
            margin-bottom: 24px;
            border-left: 4px solid {COLORS['edit_blue']};
        }}
        .priority-section {{
            margin-bottom: 24px;
        }}
        .priority-header {{
            background-color: {COLORS['background']};
            padding: 12px 16px;
            border-radius: 6px;
            margin-bottom: 12px;
            font-weight: 600;
        }}
        .email-card {{
            border: 1px solid {COLORS['border_light']};
            border-radius: 8px;
            margin-bottom: 12px;
            background-color: {COLORS['card_bg']};
            overflow: hidden;
            word-wrap: break-word;
            word-break: break-word;
        }}
        .email-card-header {{
            padding: 16px;
            border-bottom: 1px solid {COLORS['border_light']};
        }}
        .email-card-content {{
            padding: 16px;
        }}
        .sender-info {{
            display: flex;
            align-items: center;
            margin-bottom: 8px;
            flex-wrap: wrap;
            gap: 8px;
        }}
        .sender-name {{
            font-weight: 600;
            color: {COLORS['text_dark']};
            flex: 1;
            min-width: 0;
            word-break: break-word;
        }}
        .vip-badge {{
            background-color: {COLORS['success_green']};
            color: white;
            padding: 2px 6px;
            border-radius: 4px;
            font-size: {TYPOGRAPHY['small_size']};
            font-weight: 500;
            white-space: nowrap;
            flex-shrink: 0;
        }}
        .priority-badge {{
            padding: 2px 6px;
            border-radius: 4px;
            font-size: {TYPOGRAPHY['small_size']};
            font-weight: 500;
            white-space: nowrap;
            flex-shrink: 0;
        }}
        .email-subject {{
            font-weight: 600;
            color: {COLORS['text_dark']};
            margin-bottom: 8px;
            font-size: 15px;
            word-wrap: break-word;
            word-break: break-word;
            overflow-wrap: break-word;
        }}
        .email-meta {{
            color: {COLORS['text_light']};
            font-size: {TYPOGRAPHY['small_size']};
            margin-bottom: 12px;
            word-wrap: break-word;
        }}
        .ai-summary {{
            background-color: {COLORS['background']};
            padding: 12px;
            border-radius: 6px;
            margin-bottom: 12px;
            border-left: 3px solid {COLORS['edit_blue']};
            word-wrap: break-word;
            word-break: break-word;
            overflow-wrap: break-word;
        }}
        .ai-summary-label {{
            font-weight: 600;
            color: {COLORS['text_medium']};
            margin-bottom: 4px;
            font-size: {TYPOGRAPHY['small_size']};
        }}
        .button-container {{
            margin-top: 16px;
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
        }}
        .btn {{
            display: inline-block;
            padding: 8px 16px;
            border-radius: 6px;
            text-decoration: none;
            font-weight: 600;
            font-size: 13px;
            border: none;
            cursor: pointer;
            white-space: nowrap;
            text-align: center;
            min-width: 70px;
            color: #ffffff !important;
        }}
        .btn-send {{
            background-color: {COLORS['success_green']};
            color: #ffffff !important;
        }}
        .btn-edit {{
            background-color: {COLORS['edit_blue']};
            color: #ffffff !important;
        }}
        .btn-details {{
            background-color: {COLORS['text_light']};
            color: #ffffff !important;
        }}
        .insights-list {{
            margin: 8px 0;
            word-wrap: break-word;
        }}
        .insight-item {{
            margin: 4px 0;
            color: {COLORS['text_medium']};
            font-size: {TYPOGRAPHY['small_size']};
            word-wrap: break-word;
            word-break: break-word;
        }}
        .footer {{
            background-color: {COLORS['background']};
            padding: 20px;
            text-align: center;
            color: {COLORS['text_light']};
            font-size: {TYPOGRAPHY['small_size']};
        }}
        @media only screen and (max-width: 600px) {{
            .container {{ width: 100% !important; }}
            .content {{ padding: 16px !important; }}
            .button-container {{ 
                flex-direction: row !important;
                justify-content: flex-start !important;
            }}
            .btn {{ 
                flex: 0 1 auto !important;
                padding: 8px 12px !important;
                font-size: 12px !important;
                min-width: 60px !important;
                margin-bottom: 8px !important; 
                box-sizing: border-box !important;
            }}
            .sender-info {{
                flex-direction: column !important;
                align-items: flex-start !important;
            }}
            .email-subject {{
                font-size: 14px !important;
                line-height: 1.4 !important;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <!-- Header -->
        <div class="header">
            <h1 style="margin: 0; font-size: {TYPOGRAPHY['heading_size']};">📧 VoxMail Daily Digest</h1>
            <p style="margin: 8px 0 0 0; opacity: 0.9;">{date_header}</p>
        </div>

        <!-- Content -->
        <div class="content">
"""

    # Add processing summary stats
    stats = processing_summary
    if stats:
        html += f"""
            <!-- Processing Summary -->
            <div style="background-color: {COLORS['background']}; padding: 16px; border-radius: 6px; margin-bottom: 24px; text-align: center;">
                <strong>{stats.get('total_processed', 0)} emails processed</strong> • 
                <span style="color: {COLORS['high_priority']};">{len(high_priority)} high</span> • 
                <span style="color: {COLORS['medium_priority']};">{len(medium_priority)} medium</span> • 
                <span style="color: {COLORS['low_priority']};">{len(low_priority)} low priority</span>
            </div>
"""

    # Add High Priority Section
    if high_priority:
        priority_info = get_priority_indicator('High')
        html += f"""
            <!-- High Priority Section -->
            <div class="priority-section">
                <div class="priority-header" style="color: {priority_info['color']};">
                    {priority_info['emoji']} {priority_info['text']} ({len(high_priority)})
                </div>
"""
        
        for email in high_priority:
            html += generate_email_card_html(email, user_id, base_url, user_prefs, expanded=True)
        
        html += "            </div>\n"

    # Add Medium Priority Section  
    if medium_priority:
        priority_info = get_priority_indicator('Medium')
        html += f"""
            <!-- Medium Priority Section -->
            <div class="priority-section">
                <div class="priority-header" style="color: {priority_info['color']};">
                    {priority_info['emoji']} {priority_info['text']} ({len(medium_priority)})
                </div>
"""
        
        for email in medium_priority:
            html += generate_email_card_html(email, user_id, base_url, user_prefs, expanded=False)
        
        html += "            </div>\n"

    # Add Low Priority Section (Simple List)
    if low_priority:
        priority_info = get_priority_indicator('Low')
        html += f"""
            <!-- Low Priority Section -->
            <div class="priority-section">
                <div class="priority-header" style="color: {priority_info['color']};">
                    {priority_info['emoji']} {priority_info['text']} ({len(low_priority)})
                </div>
"""
        
        # Show all low priority emails in minimal format
        for email in low_priority:
            html += generate_low_priority_item_html(email)
        
        html += "            </div>\n"

    # Add footer
    html += f"""
        </div>

        <!-- Footer -->
        <div class="footer">
            <p>Powered by VoxMail - AI Email Assistant</p>
            <p><a href="{base_url}/settings/{user_id}" style="color: {COLORS['edit_blue']};">Update Settings</a></p>
        </div>
    </div>
</body>
</html>"""

    print(f"✅ HTML digest email created: {len(html)} characters")
    return html

def generate_email_card_html(email: Dict[str, Any], user_id: str, base_url: str, 
                           user_prefs: Dict[str, Any], expanded: bool = False, 
                           minimal: bool = False) -> str:
    """
    Generate HTML for individual email card showcasing all AI features
    
    This preserves and displays all your sophisticated AI processing:
    - AI summary (always visible)
    - Advanced reply with tone matching
    - Contextual insights  
    - Thread analysis
    - Priority reasoning
    """
    
    # Extract email data (from your AI system structure)
    email_id = email.get('id', 'unknown')
    sender_name = email.get('sender_name', 'Unknown Sender')
    sender_email = email.get('sender_email', '')
    subject = email.get('subject', 'No Subject')
    ai_summary = email.get('ai_summary', '')
    priority_level = email.get('priority_level', 'Medium')
    has_attachments = email.get('has_attachments', False)
    attachment_count = email.get('attachment_count', 0)
    date_str = email.get('date', '')
    
    # Advanced AI data
    advanced_reply = email.get('advanced_reply', {}) or {}
    contextual_insights = email.get('contextual_insights', [])
    tone_analysis = email.get('tone_analysis', {})
    thread_analysis = email.get('thread_analysis', {})
    priority_reasons = email.get('priority_reasons', [])
    
    # Calculate time ago
    time_ago = calculate_time_ago(date_str)
    
    # Get priority styling
    priority_info = get_priority_indicator(priority_level)
    
    # Determine if this is a VIP sender (from thread analysis)
    is_vip = thread_analysis.get('relationship_type') in ['established', 'vip'] or 'vip' in sender_email.lower()
    
    card_html = f"""
                <div class="email-card">
                    <div class="email-card-header">
                        <div class="sender-info">
                            <span class="sender-name">{sender_name}</span>
"""
    
    # Add VIP badge if applicable
    if is_vip:
        card_html += '                            <span class="vip-badge">VIP</span>\n'
    
    # Add priority badge
    card_html += f"""                            <span class="priority-badge" style="background-color: {priority_info['color']}; color: white;">{priority_info['emoji']}</span>
                        </div>
                        <div class="email-subject">{truncate_text(subject, 80)}</div>
                        <div class="email-meta">
                            ⏰ {time_ago}"""
    
    # Add attachment indicator
    if has_attachments:
        card_html += f' • 📎 {attachment_count} attachment{"s" if attachment_count > 1 else ""}'
    
    # Add thread indicator
    if thread_analysis.get('is_continuation'):
        thread_length = thread_analysis.get('length', 1)
        card_html += f' • 🧵 Thread ({thread_length} emails)'
    
    card_html += """
                        </div>
                    </div>
                    <div class="email-card-content">
"""

    # AI Summary (always visible as per your requirements)
    if ai_summary:
        card_html += f"""
                        <div class="ai-summary">
                            <div class="ai-summary-label">🤖 AI Summary</div>
                            <div>{ai_summary}</div>
                        </div>
"""

    # Show additional AI insights if expanded or high priority
    if expanded or priority_level == 'High' or user_prefs.get('show_insights_by_default', False):
        # Thread analysis (only show if thread is complex)
        if thread_analysis.get('is_continuation') and thread_analysis.get('conversation_stage') in ['extended', 'escalated']:
            stage = thread_analysis.get('conversation_stage', 'ongoing')
            urgency_escalation = thread_analysis.get('urgency_escalation', False)
            
            card_html += f"""
                        <div class="insights-list">
                            <div style="font-weight: 600; color: {COLORS['text_medium']}; margin-bottom: 4px;">🧵 Thread Status:</div>
                            <div class="insight-item">• Conversation stage: {stage}</div>
"""
            if urgency_escalation:
                card_html += '                            <div class="insight-item">• ⚠️ Urgency has escalated</div>\n'
            
            card_html += "                        </div>\n"

    # Draft reply preview (if available)
    primary_reply = advanced_reply.get('primary_reply', '')
    if primary_reply and not minimal:
        reply_preview = truncate_text(primary_reply, 100)
        card_html += f"""
                        <div style="background-color: {COLORS['background']}; padding: 12px; border-radius: 6px; margin-top: 12px; border-left: 3px solid {COLORS['success_green']};">
                            <div style="font-weight: 600; color: {COLORS['text_medium']}; margin-bottom: 4px;">✍️ Draft Reply Ready</div>
                            <div style="font-style: italic; color: {COLORS['text_medium']};">"{reply_preview}"</div>
                        </div>
"""

    # Action buttons
    if not minimal:
        card_html += """
                        <div class="button-container">
"""
        
        # Send reply button (if reply available)
        if primary_reply:
            send_url = f"{base_url}/send/{user_id}/{email_id}"
            card_html += f'                            <a href="{send_url}" class="btn btn-send">✓ Send</a>\n'
        
        # Edit reply button
        edit_url = f"{base_url}/edit/{user_id}/{email_id}"
        card_html += f'                            <a href="{edit_url}" class="btn btn-edit">✏️ Edit</a>\n'
        
        # More details button (for collapsed cards)
        if not expanded:
            details_url = f"{base_url}/details/{user_id}/{email_id}"
            card_html += f'                            <a href="{details_url}" class="btn btn-details">+ More</a>\n'
        
        card_html += "                        </div>\n"
    
    card_html += """                    </div>
                </div>
"""
    
    return card_html

def generate_low_priority_item_html(email: Dict[str, Any]) -> str:
    """
    Generate minimal HTML for low priority email items
    
    Creates a clean, scannable format with sender + truncated summary
    """
    sender_name = email.get('sender_name', 'Unknown Sender')
    subject = email.get('subject', 'No Subject')
    ai_summary = email.get('ai_summary', '')
    
    # Use subject if no AI summary
    if not ai_summary:
        ai_summary = truncate_text(subject, 60)
    else:
        ai_summary = truncate_text(ai_summary, 120)
    
    # Clean format for low priority items
    item_html = f"""
                <div style="margin: 8px 0; padding: 12px; background-color: {COLORS['background']}; border-radius: 6px; border-left: 3px solid {COLORS['low_priority']}; word-wrap: break-word; overflow-wrap: break-word;">
                    <div style="font-weight: 600; color: {COLORS['text_dark']}; margin-bottom: 4px; word-break: break-word;">
                        🔹 {truncate_text(subject, 50)} - {sender_name}
                    </div>
                    <div style="color: {COLORS['text_medium']}; font-size: {TYPOGRAPHY['small_size']}; word-wrap: break-word;">
                        📧 {ai_summary}
                    </div>
                </div>
"""
    
    return item_html

# =============================================================================
# ADDITIONAL EMAIL TEMPLATES
# =============================================================================

def create_action_success_template() -> str:
    """Template for successful actions"""
    return """
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Action Successful</title>
    <style>
        body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Arial, sans-serif; }
        .container { max-width: 500px; margin: 50px auto; padding: 20px; text-align: center; }
        .success { color: #059669; font-size: 24px; margin-bottom: 16px; }
        .message { color: #374151; margin-bottom: 24px; }
        .btn { background: #2563eb; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; }
    </style>
</head>
<body>
    <div class="container">
        <div class="success">✅ Success!</div>
        <div class="message">{{ action }} completed successfully{{ ' for "' + email_subject + '"' if email_subject else '' }}.</div>
        <a href="mailto:" class="btn">Back to Email</a>
    </div>
</body>
</html>
"""

def create_action_error_template() -> str:
    """Template for action errors"""
    return """
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Action Error</title>
    <style>
        body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Arial, sans-serif; }
        .container { max-width: 500px; margin: 50px auto; padding: 20px; text-align: center; }
        .error { color: #dc2626; font-size: 24px; margin-bottom: 16px; }
        .message { color: #374151; margin-bottom: 24px; }
        .btn { background: #2563eb; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; }
    </style>
</head>
<body>
    <div class="container">
        <div class="error">❌ Error</div>
        <div class="message">Failed to {{ action }}: {{ error }}</div>
        <a href="mailto:" class="btn">Back to Email</a>
    </div>
</body>
</html>
"""

# =============================================================================
# MODULE END
# =============================================================================