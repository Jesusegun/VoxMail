# =============================================================================
# MOCK EMAIL FETCHER - mock_email_fetcher.py
# =============================================================================
# This is a testing version of EmailFetcher that works WITHOUT Gmail API
# It generates realistic fake email data so you can test the entire system
# before setting up Google Cloud Console authentication
#
# PURPOSE:
# 1. Test the email processing logic without API dependencies
# 2. Generate realistic email data for AI training and testing
# 3. Demonstrate expected email data structure
# 4. Allow development without Gmail API setup
# =============================================================================

import datetime
import random
from typing import List, Dict, Any

class MockEmailFetcher:
    """
    Mock Email Fetcher for Testing Without Gmail API
    
    This class generates realistic fake email data that matches the structure
    of real Gmail API responses. Perfect for testing and development.
    """
    
    def __init__(self):
        """Initialize the mock email fetcher with test data"""
        
        # Sample senders for realistic email generation
        self.sample_senders = [
            # High priority business contacts
            {"name": "Sarah Johnson", "email": "sarah.johnson@techcorp.com", "priority": "high"},
            {"name": "Michael Chen", "email": "m.chen@bigclient.com", "priority": "high"},
            {"name": "Lisa Rodriguez", "email": "l.rodriguez@partners.com", "priority": "high"},
            {"name": "James Wilson", "email": "james.wilson@supplier.com", "priority": "medium"},
            {"name": "Emily Davis", "email": "e.davis@marketing.com", "priority": "medium"},
            
            # Medium priority contacts
            {"name": "David Brown", "email": "david@consulting.com", "priority": "medium"},
            {"name": "Jennifer Lee", "email": "j.lee@agency.com", "priority": "medium"},
            {"name": "Robert Taylor", "email": "r.taylor@vendor.com", "priority": "medium"},
            
            # Low priority / automated
            {"name": "LinkedIn Notifications", "email": "noreply@linkedin.com", "priority": "low"},
            {"name": "Newsletter Team", "email": "newsletter@techdigest.com", "priority": "low"},
            {"name": "Support Team", "email": "support@software.com", "priority": "low"},
            {"name": "GitHub Notifications", "email": "noreply@github.com", "priority": "low"},
            {"name": "AWS Alerts", "email": "no-reply@aws.amazon.com", "priority": "low"},
        ]
        
        # Sample email subjects categorized by type and priority
        self.email_templates = {
            "high_priority": [
                {"subject": "URGENT: Contract approval needed by EOD", "has_deadline": True, "urgent": True},
                {"subject": "Client meeting moved to tomorrow - please confirm", "has_deadline": True, "has_meeting": True},
                {"subject": "Critical system issue - immediate attention required", "urgent": True, "has_problem": True},
                {"subject": "Board presentation deadline extended to Friday", "has_deadline": True},
                {"subject": "Important: Budget approval required for Q4", "urgent": True, "has_attachment": True},
                {"subject": "ASAP: Vendor contract needs immediate review", "urgent": True, "has_attachment": True},
                {"subject": "Emergency: Server downtime affecting production", "urgent": True, "has_problem": True},
                {"subject": "Deadline reminder: Project deliverables due tomorrow", "has_deadline": True},
            ],
            "medium_priority": [
                {"subject": "Weekly team meeting agenda", "has_meeting": True},
                {"subject": "Project status update - Phase 2", "has_update": True},
                {"subject": "Vendor proposal for review", "has_attachment": True},
                {"subject": "Training session scheduled for next week", "has_meeting": True},
                {"subject": "Monthly report completed", "has_attachment": True},
                {"subject": "Q3 performance review scheduling", "has_meeting": True},
                {"subject": "New software deployment next Tuesday", "has_update": True},
                {"subject": "Client feedback on recent deliverable", "has_update": True},
                {"subject": "Conference call notes and action items", "has_attachment": True},
            ],
            "low_priority": [
                {"subject": "Your LinkedIn weekly digest", "automated": True},
                {"subject": "New features in our latest update", "automated": True},
                {"subject": "Industry newsletter - March edition", "automated": True},
                {"subject": "Webinar invitation: Future of AI", "automated": True},
                {"subject": "Account security update", "automated": True},
                {"subject": "GitHub: 5 new notifications", "automated": True},
                {"subject": "AWS billing statement available", "automated": True},
                {"subject": "Subscription renewal reminder", "automated": True},
            ]
        }
        
        # Sample email body templates
        self.body_templates = {
            "urgent_request": """Hi,

I need your urgent attention on the {topic}. We have a deadline of {deadline} and need to move quickly on this.

{details}

Please review the attached documents and let me know your thoughts by {time}.

Thanks,
{sender_name}""",
            
            "meeting_request": """Hi,

I'd like to schedule a meeting to discuss {topic}. 

Would {time} work for you? The meeting should take about {duration}.

Agenda:
- {agenda_item_1}
- {agenda_item_2}
- {agenda_item_3}

Best regards,
{sender_name}""",
            
            "project_update": """Hi team,

Here's the latest update on {project}:

• Status: {status}
• Progress: {progress}%
• Next milestone: {milestone}
• Issues: {issues}
• Expected completion: {completion_date}

Please let me know if you have any questions or concerns.

{sender_name}""",
            
            "problem_report": """Hi,

We've encountered an issue with {system} that requires immediate attention.

Problem Details:
- Issue: {problem_description}
- Impact: {impact_level}
- Affected users: {affected_count}
- Timeline: {timeline}

I've attached the error logs and initial analysis. Please prioritize this as it's affecting our operations.

Thanks,
{sender_name}""",
            
            "newsletter": """Welcome to this week's {newsletter_name}!

This week's highlights:
• {highlight1}
• {highlight2}  
• {highlight3}

Featured Article: {featured_article}

Industry News:
- {news_item_1}
- {news_item_2}

Read the full newsletter at {link}

Best regards,
The {newsletter_name} Team

To unsubscribe, click here.""",
            
            "standard_business": """Hi,

I wanted to follow up on our previous discussion about {topic}.

{main_content}

{call_to_action}

Please let me know if you need any additional information.

Best regards,
{sender_name}"""
        }
        
        # Content variables for templates
        self.content_variables = {
            "topics": [
                "the Q4 budget allocation", "project timeline review", "client requirements", 
                "system architecture", "team restructuring", "vendor negotiations",
                "compliance audit", "security protocols", "performance metrics"
            ],
            "deadlines": [
                "EOD today", "tomorrow morning", "by Friday", "this week", "next Monday",
                "end of month", "before the meeting", "by noon tomorrow"
            ],
            "times": [
                "tomorrow at 2 PM", "Friday morning", "next Tuesday at 10 AM", "this week",
                "Monday afternoon", "Thursday at 3 PM", "next week sometime"
            ],
            "durations": [
                "30 minutes", "1 hour", "45 minutes", "2 hours", "90 minutes"
            ],
            "projects": [
                "Website Redesign", "Mobile App Development", "Database Migration", 
                "System Upgrade", "Customer Portal", "Analytics Dashboard",
                "Security Enhancement", "Performance Optimization"
            ],
            "statuses": [
                "On track", "Slightly delayed", "Ahead of schedule", "Under review",
                "Pending approval", "In progress", "Completed", "On hold"
            ],
            "problems": [
                "server connectivity", "database performance", "user authentication",
                "payment processing", "data synchronization", "email delivery",
                "mobile app crashes", "API rate limiting"
            ],
            "systems": [
                "the production server", "our CRM system", "the payment gateway",
                "the database cluster", "the mobile application", "the API service"
            ]
        }
        
        print("🎭 MockEmailFetcher initialized with realistic test data")
    
    def get_recent_emails(self, hours: int = 24, include_read: bool = False, 
                         sender_filter: str = None, count: int = None) -> List[Dict[str, Any]]:
        """
        Generate mock recent emails that simulate Gmail API responses
        
        Args:
            hours (int): Hours to look back (affects email timestamps)
            include_read (bool): Include read emails in results
            sender_filter (str): Filter by specific sender
            count (int): Number of emails to generate (default: random 5-15)
            
        Returns:
            List[Dict]: List of mock email data matching real EmailFetcher structure
        """
        
        print(f"🎭 Generating mock emails for last {hours} hours...")
        
        # Determine how many emails to generate
        if count is None:
            # Realistic daily email volume based on time range
            if hours <= 1:
                email_count = random.randint(1, 3)
            elif hours <= 8:
                email_count = random.randint(3, 8)
            elif hours <= 24:
                email_count = random.randint(8, 15)
            else:
                email_count = random.randint(15, 25)
        else:
            email_count = count
            
        print(f"📧 Generating {email_count} mock emails...")
        
        mock_emails = []
        
        for i in range(email_count):
            # Select random priority category with realistic distribution
            priority_category = random.choices(
                ['high_priority', 'medium_priority', 'low_priority'],
                weights=[15, 60, 25],  # Most emails are medium priority
                k=1
            )[0]
            
            # Generate individual email
            mock_email = self._generate_single_email(i + 1, priority_category, hours)
            
            # Apply sender filter if specified
            if sender_filter:
                if sender_filter.lower() not in mock_email['sender_email'].lower():
                    continue
                
            mock_emails.append(mock_email)
        
        # Apply read/unread filter
        if not include_read:
            # Simulate some emails being read (about 30%)
            for email in mock_emails:
                if random.random() < 0.3:
                    email['is_read'] = True
                else:
                    email['is_read'] = False
            
            # Filter out read emails if not including them
            mock_emails = [e for e in mock_emails if not e.get('is_read', False)]
        
        print(f"✅ Generated {len(mock_emails)} mock emails successfully")
        return mock_emails
    
    def _generate_single_email(self, email_index: int, priority_category: str, hours_back: int) -> Dict[str, Any]:
        """
        Generate a single realistic mock email
        
        Args:
            email_index (int): Email number for ID generation
            priority_category (str): Priority category for this email
            hours_back (int): Hours back for timestamp calculation
            
        Returns:
            Dict: Complete mock email data structure
        """
        
        # Select appropriate sender based on priority
        priority_senders = [s for s in self.sample_senders if s["priority"] == priority_category.split('_')[0]]
        if not priority_senders:
            priority_senders = self.sample_senders
        
        sender = random.choice(priority_senders)
        
        # Select email template based on category
        template_data = random.choice(self.email_templates[priority_category])
        
        # Generate timestamp within the lookback period
        now = datetime.datetime.utcnow()
        email_time = now - datetime.timedelta(
            hours=random.randint(1, min(hours_back, 72)),  # Max 72 hours back
            minutes=random.randint(0, 59)
        )
        
        # Generate email body based on template and category
        email_body = self._generate_email_body(template_data, sender['name'], priority_category)
        
        # Extract priority indicators
        priority_indicators = self._extract_mock_priority_indicators(template_data, email_body)
        
        # Determine if email is part of a thread
        is_thread = random.choice([True, False]) if priority_category != 'low_priority' else False
        thread_length = random.randint(2, 5) if is_thread else 1
        
        # Generate attachment information
        has_attachments = template_data.get('has_attachment', False) or random.random() < 0.2
        attachment_info = self._generate_attachment_info() if has_attachments else {
            'count': 0, 'types': [], 'names': []
        }
        
        # Generate mock email data structure that matches real EmailFetcher
        mock_email = {
            # Basic identification
            'id': f'mock_email_{email_index:03d}_{random.randint(1000, 9999)}',
            'message_id': f'<{email_index}.{random.randint(100000, 999999)}@mock.gmail.com>',
            'thread_id': f'thread_{email_index}_{random.randint(100, 999)}' if is_thread else f'thread_{email_index}_{random.randint(100, 999)}',
            
            # Core email content
            'subject': template_data['subject'],
            'sender': f"{sender['name']} <{sender['email']}>",
            'sender_name': sender['name'],
            'sender_email': sender['email'],
            'reply_to': sender['email'],
            'date': email_time.strftime("%a, %d %b %Y %H:%M:%S +0000"),
            'body': email_body,
            'raw_body': email_body[:500],
            
            # Email analysis
            'body_length': len(email_body),
            'has_attachments': has_attachments,
            'attachment_count': attachment_info['count'],
            'attachment_types': attachment_info['types'],
            'attachment_names': attachment_info['names'],
            
            # Thread context
            'is_thread': is_thread,
            'thread_length': thread_length,
            'thread_position': random.randint(1, thread_length) if is_thread else 1,
            
            # Priority and classification hints
            'priority_indicators': priority_indicators,
            'is_automated': template_data.get('automated', False),
            'language': 'en',
            
            # Processing metadata
            'processed_at': datetime.datetime.utcnow().isoformat(),
            'fetcher_version': '1.0_mock',
            'mock_category': priority_category
        }
        
        return mock_email
    
    def _generate_email_body(self, template_data: Dict, sender_name: str, priority_category: str) -> str:
        """Generate realistic email body content based on template and priority"""
        
        # Choose appropriate body template based on email characteristics
        if template_data.get('urgent') or template_data.get('has_deadline'):
            template = self.body_templates['urgent_request']
            body = template.format(
                topic=random.choice(self.content_variables['topics']),
                deadline=random.choice(self.content_variables['deadlines']),
                time=random.choice(self.content_variables['times']),
                details=self._generate_urgent_details(),
                sender_name=sender_name
            )
        
        elif template_data.get('has_meeting'):
            template = self.body_templates['meeting_request']
            body = template.format(
                topic=random.choice(self.content_variables['topics']),
                time=random.choice(self.content_variables['times']),
                duration=random.choice(self.content_variables['durations']),
                agenda_item_1=random.choice(['Budget review', 'Timeline planning', 'Resource allocation']),
                agenda_item_2=random.choice(['Risk assessment', 'Progress updates', 'Next steps']),
                agenda_item_3=random.choice(['Action items', 'Q&A session', 'Follow-up planning']),
                sender_name=sender_name
            )
        
        elif template_data.get('has_update'):
            template = self.body_templates['project_update']
            body = template.format(
                project=random.choice(self.content_variables['projects']),
                status=random.choice(self.content_variables['statuses']),
                progress=random.randint(25, 95),
                milestone=random.choice(['Testing phase', 'User acceptance', 'Deployment', 'Final review']),
                issues=random.choice(['None reported', 'Minor bug fixes needed', 'Waiting for approval', 'Resource constraints']),
                completion_date=random.choice(['Next Friday', 'End of month', 'Q4', 'Early next quarter']),
                sender_name=sender_name
            )
        
        elif template_data.get('has_problem'):
            template = self.body_templates['problem_report']
            body = template.format(
                system=random.choice(self.content_variables['systems']),
                problem_description=random.choice([
                    'Service intermittently unavailable',
                    'Performance degradation observed',
                    'Authentication errors occurring',
                    'Data synchronization failures'
                ]),
                impact_level=random.choice(['High', 'Medium', 'Critical']),
                affected_count=random.choice(['50+ users', 'All users', 'Premium customers', 'Internal team']),
                timeline=random.choice(['Started 2 hours ago', 'Ongoing since morning', 'Reported at 3 PM']),
                sender_name=sender_name
            )
        
        elif template_data.get('automated'):
            template = self.body_templates['newsletter']
            body = template.format(
                newsletter_name=random.choice(['Tech Weekly', 'Industry Insights', 'Product Updates', 'News Digest']),
                highlight1=random.choice(['New AI breakthroughs', 'Market trends analysis', 'Product launches']),
                highlight2=random.choice(['Expert interviews', 'Case studies', 'Best practices']),
                highlight3=random.choice(['Upcoming events', 'Resource downloads', 'Community highlights']),
                featured_article=random.choice([
                    'The Future of Remote Work',
                    'AI in Business: A Practical Guide',
                    'Cybersecurity Trends 2024'
                ]),
                news_item_1=random.choice([
                    'Major tech acquisition announced',
                    'New regulation changes',
                    'Industry conference dates released'
                ]),
                news_item_2=random.choice([
                    'Startup funding round completed',
                    'Research breakthrough published',
                    'Partnership announcement'
                ]),
                link='https://newsletter.example.com'
            )
        
        else:
            # Default business email
            template = self.body_templates['standard_business']
            body = template.format(
                topic=random.choice(self.content_variables['topics']),
                main_content=self._generate_standard_content(),
                call_to_action=random.choice([
                    'Please let me know your thoughts on this.',
                    'I\'d appreciate your feedback by Friday.',
                    'Let me know if you need any clarification.',
                    'Looking forward to your response.'
                ]),
                sender_name=sender_name
            )
        
        return body
    
    def _generate_urgent_details(self) -> str:
        """Generate additional details for urgent emails"""
        details = [
            "This is blocking our progress on the main deliverable.",
            "The client has specifically requested an update on this.",
            "We've already extended the deadline once and can't do so again.",
            "This impacts multiple team members and external stakeholders."
        ]
        return random.choice(details)
    
    def _generate_standard_content(self) -> str:
        """Generate content for standard business emails"""
        contents = [
            "I've been reviewing the latest developments and wanted to get your input on the next steps.",
            "Following up on our conversation from last week, I have some additional information to share.",
            "I wanted to touch base on the current status and see if there are any blockers I can help with.",
            "After discussing with the team, we have a few recommendations to consider.",
            "I've analyzed the current situation and have some suggestions for moving forward."
        ]
        return random.choice(contents)
    
    def _generate_attachment_info(self) -> Dict[str, Any]:
        """Generate realistic attachment information"""
        # Common business file types
        file_types = ['pdf', 'docx', 'xlsx', 'pptx', 'zip', 'png', 'jpg']
        file_names = [
            'quarterly_report.pdf', 'budget_analysis.xlsx', 'project_timeline.docx',
            'presentation_slides.pptx', 'technical_specs.pdf', 'screenshot.png',
            'data_export.csv', 'contract_draft.docx', 'invoice.pdf'
        ]
        
        attachment_count = random.randint(1, 3)
        selected_names = random.sample(file_names, min(attachment_count, len(file_names)))
        selected_types = [name.split('.')[-1] for name in selected_names]
        
        return {
            'count': attachment_count,
            'types': list(set(selected_types)),  # Remove duplicates
            'names': selected_names
        }
    
    def _extract_mock_priority_indicators(self, template_data: Dict, body: str) -> List[str]:
        """Generate realistic priority indicators for mock emails"""
        
        indicators = []
        
        # Check template flags
        if template_data.get('urgent'):
            indicators.append('urgent_keyword_subject: urgent')
        
        if template_data.get('has_deadline'):
            indicators.append('urgent_keyword_subject: deadline')
            
        if template_data.get('automated'):
            indicators.append('automated_email')
        
        if template_data.get('has_attachment'):
            indicators.append('has_important_attachments')
        
        if template_data.get('has_meeting'):
            indicators.append('meeting_coordination_required')
        
        # Check body content for additional indicators
        body_lower = body.lower()
        
        if any(word in body_lower for word in ['asap', 'immediate', 'critical', 'urgent']):
            indicators.append('urgent_keyword_body: urgent')
        
        if any(word in body_lower for word in ['deadline', 'eod', 'by friday', 'tomorrow']):
            indicators.append('urgent_keyword_body: deadline')
        
        if any(word in body_lower for word in ['ceo', 'director', 'manager', 'client']):
            indicators.append('vip_sender_indicators')
            
        return indicators
    
    def get_email_details(self, message_id: str) -> Dict[str, Any]:
        """
        Mock version of get_email_details for testing
        
        Args:
            message_id (str): Mock message ID
            
        Returns:
            Dict: Mock email details
        """
        
        print(f"🎭 Getting mock email details for ID: {message_id}")
        
        # Generate a single mock email based on the ID
        try:
            email_index = int(message_id.split('_')[-2]) if 'mock_email_' in message_id else random.randint(1, 100)
        except:
            email_index = random.randint(1, 100)
            
        priority_category = random.choice(['high_priority', 'medium_priority', 'low_priority'])
        
        return self._generate_single_email(email_index, priority_category, 24)

# =============================================================================
# TESTING AND DEMONSTRATION
# =============================================================================

def test_mock_email_fetcher():
    """Test the mock email fetcher functionality"""
    
    print("=" * 70)
    print("🧪 MOCK EMAIL FETCHER TEST")
    print("=" * 70)
    
    # Create mock fetcher instance
    print("🎭 Creating MockEmailFetcher...")
    mock_fetcher = MockEmailFetcher()
    
    # Test basic email generation
    print("\n📧 Testing basic email generation...")
    mock_emails = mock_fetcher.get_recent_emails(hours=24, count=10)
    
    print(f"\n📊 RESULTS:")
    print(f"   📧 Mock emails generated: {len(mock_emails)}")
    
    # Analyze the generated emails
    high_priority = [e for e in mock_emails if any('urgent' in str(indicator) for indicator in e['priority_indicators'])]
    has_attachments = [e for e in mock_emails if e['has_attachments']]
    is_threaded = [e for e in mock_emails if e['is_thread']]
    automated_emails = [e for e in mock_emails if e['is_automated']]
    
    print(f"\n📈 EMAIL ANALYSIS:")
    print(f"   🔥 High priority emails: {len(high_priority)}")
    print(f"   📎 Emails with attachments: {len(has_attachments)}")
    print(f"   🧵 Threaded emails: {len(is_threaded)}")
    print(f"   🤖 Automated emails: {len(automated_emails)}")
    
    # Display sample emails
    print(f"\n📝 SAMPLE EMAILS:")
    for i, email in enumerate(mock_emails[:3], 1):
        print(f"\n   📧 Email {i}:")
        print(f"      From: {email['sender_name']}")
        print(f"      Subject: {email['subject']}")
        print(f"      Priority indicators: {email['priority_indicators']}")
        print(f"      Body preview: {email['body'][:100]}...")
        if email['has_attachments']:
            print(f"      Attachments: {', '.join(email['attachment_names'])}")
    
    # Test different time ranges
    print(f"\n🕐 Testing different time ranges...")
    for hours in [1, 8, 24, 72]:
        emails = mock_fetcher.get_recent_emails(hours=hours, count=5)
        print(f"   Last {hours} hours: {len(emails)} emails")
    
    # Test sender filtering
    print(f"\n🔍 Testing sender filtering...")
    filtered_emails = mock_fetcher.get_recent_emails(
        hours=24, 
        sender_filter="sarah.johnson@techcorp.com",
        count=10
    )
    print(f"   📧 Filtered emails (Sarah Johnson): {len(filtered_emails)}")
    
    # Test individual email details
    print(f"\n🔍 Testing individual email details...")
    if mock_emails:
        sample_id = mock_emails[0]['id']
        email_details = mock_fetcher.get_email_details(sample_id)
        print(f"   📧 Retrieved email details for: {email_details['sender_name']}")
    
    print(f"\n✅ Mock email fetcher test completed successfully!")
    print(f"🎯 This demonstrates the exact data structure your AI agent will receive!")

# =============================================================================
# COMPARISON WITH REAL EMAIL FETCHER
# =============================================================================

def compare_with_real_fetcher():
    """Show how MockEmailFetcher matches real EmailFetcher structure"""
    
    print("=" * 70)
    print("🔄 MOCK vs REAL EMAIL FETCHER COMPARISON")
    print("=" * 70)
    
    mock_fetcher = MockEmailFetcher()
    mock_email = mock_fetcher.get_recent_emails(count=1)[0]
    
    print("📋 Email Data Structure (identical to real Gmail API):")
    print("\nBasic Information:")
    print(f"  ✅ ID: {mock_email['id']}")
    print(f"  ✅ Subject: {mock_email['subject']}")
    print(f"  ✅ Sender: {mock_email['sender_name']} ({mock_email['sender_email']})")
    print(f"  ✅ Date: {mock_email['date']}")
    
    print("\nContent Analysis:")
    print(f"  ✅ Body length: {mock_email['body_length']} characters")
    print(f"  ✅ Language: {mock_email['language']}")
    print(f"  ✅ Is automated: {mock_email['is_automated']}")
    
    print("\nAttachments:")
    print(f"  ✅ Has attachments: {mock_email['has_attachments']}")
    print(f"  ✅ Attachment count: {mock_email['attachment_count']}")
    print(f"  ✅ Attachment types: {mock_email['attachment_types']}")
    
    print("\nThread Information:")
    print(f"  ✅ Is thread: {mock_email['is_thread']}")
    print(f"  ✅ Thread length: {mock_email['thread_length']}")
    print(f"  ✅ Thread position: {mock_email['thread_position']}")
    
    print("\nPriority Analysis:")
    print(f"  ✅ Priority indicators: {mock_email['priority_indicators']}")
    
    print("\n🎯 This exact structure works seamlessly with your AI processing system!")

if __name__ == '__main__':
    """Run tests when file is executed directly"""
    test_mock_email_fetcher()
    print("\n" + "="*70)
    compare_with_real_fetcher()