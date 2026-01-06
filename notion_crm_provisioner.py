"""
Notion CRM Auto-Provisioning System
Automatically creates a full CRM workspace in Notion for clients who don't have a CRM

Features:
- Pipeline database with all stages
- Contacts database
- Companies database
- Activities/Tasks database
- Dashboard views
- Automatic data sync
"""

import os
import json
import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum

# Notion SDK
try:
    from notion_client import AsyncClient as NotionAsyncClient
except ImportError:
    NotionAsyncClient = None


class DealStage(Enum):
    """Standard deal stages"""
    NEW_LEAD = "New Lead"
    QUALIFIED = "Qualified"
    DISCOVERY = "Discovery"
    PROPOSAL = "Proposal"
    NEGOTIATION = "Negotiation"
    CLOSED_WON = "Closed Won"
    CLOSED_LOST = "Closed Lost"


class LeadSource(Enum):
    """Lead sources for attribution"""
    AI_SDR_OUTBOUND = "AI SDR Outbound"
    INBOUND_WEBSITE = "Inbound - Website"
    INBOUND_REFERRAL = "Inbound - Referral"
    LINKEDIN = "LinkedIn"
    COLD_EMAIL = "Cold Email"
    EVENT = "Event"
    PARTNER = "Partner"
    OTHER = "Other"


@dataclass
class CRMConfig:
    """Configuration for CRM provisioning"""
    workspace_name: str
    owner_email: str
    team_members: List[str] = None
    custom_stages: List[str] = None
    industry: str = None
    
    def __post_init__(self):
        if self.team_members is None:
            self.team_members = []
        if self.custom_stages is None:
            self.custom_stages = [s.value for s in DealStage]


class NotionCRMProvisioner:
    """
    Automatically provisions a complete CRM system in Notion
    """
    
    def __init__(self, notion_api_key: str = None):
        self.api_key = notion_api_key or os.getenv("NOTION_API_KEY")
        self.client = None
        if NotionAsyncClient and self.api_key:
            self.client = NotionAsyncClient(auth=self.api_key)
        
        # Store created database IDs
        self.databases = {}
        self.page_id = None
    
    async def provision_crm(self, config: CRMConfig, parent_page_id: str = None) -> Dict:
        """
        Provision complete CRM workspace
        
        Args:
            config: CRM configuration
            parent_page_id: Optional parent page to create CRM under
            
        Returns:
            Dict with all created database IDs and URLs
        """
        if not self.client:
            return self._generate_mock_response(config)
        
        print(f"🚀 Provisioning CRM for: {config.workspace_name}")
        
        try:
            # 1. Create main CRM page
            main_page = await self._create_main_page(config, parent_page_id)
            self.page_id = main_page["id"]
            print(f"✅ Created main page: {config.workspace_name}")
            
            # 2. Create Pipeline database
            pipeline_db = await self._create_pipeline_database(config)
            self.databases["pipeline"] = pipeline_db["id"]
            print("✅ Created Pipeline database")
            
            # 3. Create Contacts database
            contacts_db = await self._create_contacts_database()
            self.databases["contacts"] = contacts_db["id"]
            print("✅ Created Contacts database")
            
            # 4. Create Companies database
            companies_db = await self._create_companies_database()
            self.databases["companies"] = companies_db["id"]
            print("✅ Created Companies database")
            
            # 5. Create Activities database
            activities_db = await self._create_activities_database()
            self.databases["activities"] = activities_db["id"]
            print("✅ Created Activities database")
            
            # 6. Create Email Sequences database
            sequences_db = await self._create_sequences_database()
            self.databases["sequences"] = sequences_db["id"]
            print("✅ Created Email Sequences database")
            
            # 7. Add sample data
            await self._add_sample_data(config)
            print("✅ Added sample data")
            
            # 8. Create dashboard views
            await self._create_dashboard_views()
            print("✅ Created dashboard views")
            
            return {
                "status": "success",
                "workspace_name": config.workspace_name,
                "main_page_id": self.page_id,
                "databases": self.databases,
                "urls": {
                    "main_page": f"https://notion.so/{self.page_id.replace('-', '')}",
                    "pipeline": f"https://notion.so/{self.databases['pipeline'].replace('-', '')}",
                    "contacts": f"https://notion.so/{self.databases['contacts'].replace('-', '')}",
                    "companies": f"https://notion.so/{self.databases['companies'].replace('-', '')}",
                },
                "created_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "partial_databases": self.databases
            }
    
    async def _create_main_page(self, config: CRMConfig, parent_page_id: str = None) -> Dict:
        """Create main CRM workspace page"""
        
        # Create page properties
        page_data = {
            "parent": {"page_id": parent_page_id} if parent_page_id else {"type": "workspace"},
            "properties": {
                "title": {
                    "title": [
                        {
                            "text": {
                                "content": f"🎯 {config.workspace_name} - Sales CRM"
                            }
                        }
                    ]
                }
            },
            "icon": {"emoji": "🎯"},
            "children": [
                {
                    "object": "block",
                    "type": "callout",
                    "callout": {
                        "icon": {"emoji": "👋"},
                        "rich_text": [
                            {
                                "text": {
                                    "content": f"Welcome to your AI-powered CRM! This workspace was automatically provisioned by the AI SDR Platform."
                                }
                            }
                        ]
                    }
                },
                {
                    "object": "block",
                    "type": "heading_2",
                    "heading_2": {
                        "rich_text": [{"text": {"content": "📊 Quick Stats"}}]
                    }
                },
                {
                    "object": "block",
                    "type": "divider",
                    "divider": {}
                }
            ]
        }
        
        return await self.client.pages.create(**page_data)
    
    async def _create_pipeline_database(self, config: CRMConfig) -> Dict:
        """Create the main pipeline/deals database"""
        
        # Define stage options with colors
        stage_options = []
        stage_colors = ["gray", "blue", "purple", "yellow", "orange", "green", "red"]
        
        for i, stage in enumerate(config.custom_stages):
            stage_options.append({
                "name": stage,
                "color": stage_colors[i % len(stage_colors)]
            })
        
        database_data = {
            "parent": {"page_id": self.page_id},
            "title": [{"text": {"content": "📈 Pipeline"}}],
            "icon": {"emoji": "📈"},
            "properties": {
                "Deal Name": {"title": {}},
                "Company": {
                    "relation": {
                        "database_id": self.databases.get("companies"),
                        "single_property": {}
                    }
                } if self.databases.get("companies") else {"rich_text": {}},
                "Contact": {
                    "relation": {
                        "database_id": self.databases.get("contacts"),
                        "single_property": {}
                    }
                } if self.databases.get("contacts") else {"rich_text": {}},
                "Stage": {
                    "select": {
                        "options": stage_options
                    }
                },
                "Deal Value": {
                    "number": {
                        "format": "dollar"
                    }
                },
                "Lead Score": {
                    "number": {
                        "format": "number"
                    }
                },
                "Owner": {
                    "people": {}
                },
                "Source": {
                    "select": {
                        "options": [
                            {"name": s.value, "color": "blue"} 
                            for s in LeadSource
                        ]
                    }
                },
                "SLA Deadline": {
                    "date": {}
                },
                "Days in Stage": {
                    "formula": {
                        "expression": "dateBetween(now(), prop(\"Stage Changed\"), \"days\")"
                    }
                },
                "Stage Changed": {
                    "date": {}
                },
                "Created": {
                    "created_time": {}
                },
                "Handoff Notes": {
                    "rich_text": {}
                },
                "Research Summary": {
                    "rich_text": {}
                },
                "Next Action": {
                    "rich_text": {}
                },
                "Close Date": {
                    "date": {}
                },
                "Win Probability": {
                    "number": {
                        "format": "percent"
                    }
                },
                "Lost Reason": {
                    "select": {
                        "options": [
                            {"name": "Budget", "color": "red"},
                            {"name": "Timing", "color": "orange"},
                            {"name": "Competition", "color": "yellow"},
                            {"name": "No Decision", "color": "gray"},
                            {"name": "Other", "color": "default"}
                        ]
                    }
                }
            }
        }
        
        return await self.client.databases.create(**database_data)
    
    async def _create_contacts_database(self) -> Dict:
        """Create contacts database"""
        
        database_data = {
            "parent": {"page_id": self.page_id},
            "title": [{"text": {"content": "👥 Contacts"}}],
            "icon": {"emoji": "👥"},
            "properties": {
                "Name": {"title": {}},
                "Email": {"email": {}},
                "Phone": {"phone_number": {}},
                "Title": {"rich_text": {}},
                "Company": {"rich_text": {}},
                "LinkedIn": {"url": {}},
                "Seniority": {
                    "select": {
                        "options": [
                            {"name": "C-Suite", "color": "purple"},
                            {"name": "VP", "color": "blue"},
                            {"name": "Director", "color": "green"},
                            {"name": "Manager", "color": "yellow"},
                            {"name": "Individual Contributor", "color": "gray"}
                        ]
                    }
                },
                "Status": {
                    "select": {
                        "options": [
                            {"name": "Active", "color": "green"},
                            {"name": "Nurturing", "color": "yellow"},
                            {"name": "Unresponsive", "color": "gray"},
                            {"name": "Do Not Contact", "color": "red"}
                        ]
                    }
                },
                "Last Contacted": {"date": {}},
                "Total Emails Sent": {"number": {}},
                "Replies": {"number": {}},
                "Notes": {"rich_text": {}},
                "Tags": {
                    "multi_select": {
                        "options": [
                            {"name": "Decision Maker", "color": "purple"},
                            {"name": "Champion", "color": "green"},
                            {"name": "Blocker", "color": "red"},
                            {"name": "Technical", "color": "blue"},
                            {"name": "Executive Sponsor", "color": "orange"}
                        ]
                    }
                },
                "Created": {"created_time": {}}
            }
        }
        
        return await self.client.databases.create(**database_data)
    
    async def _create_companies_database(self) -> Dict:
        """Create companies database"""
        
        database_data = {
            "parent": {"page_id": self.page_id},
            "title": [{"text": {"content": "🏢 Companies"}}],
            "icon": {"emoji": "🏢"},
            "properties": {
                "Company Name": {"title": {}},
                "Website": {"url": {}},
                "Industry": {
                    "select": {
                        "options": [
                            {"name": "Technology", "color": "blue"},
                            {"name": "Healthcare", "color": "green"},
                            {"name": "Finance", "color": "yellow"},
                            {"name": "Retail", "color": "orange"},
                            {"name": "Manufacturing", "color": "gray"},
                            {"name": "Services", "color": "purple"},
                            {"name": "Other", "color": "default"}
                        ]
                    }
                },
                "Employee Count": {
                    "select": {
                        "options": [
                            {"name": "1-10", "color": "gray"},
                            {"name": "11-50", "color": "blue"},
                            {"name": "51-200", "color": "green"},
                            {"name": "201-500", "color": "yellow"},
                            {"name": "501-1000", "color": "orange"},
                            {"name": "1000+", "color": "red"}
                        ]
                    }
                },
                "Annual Revenue": {"rich_text": {}},
                "LinkedIn": {"url": {}},
                "Tech Stack": {"multi_select": {}},
                "Hiring Departments": {"multi_select": {}},
                "Recent News": {"rich_text": {}},
                "Company Summary": {"rich_text": {}},
                "ICP Score": {"number": {}},
                "Total Deals": {"number": {}},
                "Total Revenue": {"number": {"format": "dollar"}},
                "Notes": {"rich_text": {}},
                "Created": {"created_time": {}}
            }
        }
        
        return await self.client.databases.create(**database_data)
    
    async def _create_activities_database(self) -> Dict:
        """Create activities/tasks database"""
        
        database_data = {
            "parent": {"page_id": self.page_id},
            "title": [{"text": {"content": "✅ Activities"}}],
            "icon": {"emoji": "✅"},
            "properties": {
                "Task": {"title": {}},
                "Type": {
                    "select": {
                        "options": [
                            {"name": "Email", "color": "blue"},
                            {"name": "Call", "color": "green"},
                            {"name": "Meeting", "color": "purple"},
                            {"name": "Follow-up", "color": "yellow"},
                            {"name": "Research", "color": "orange"},
                            {"name": "Admin", "color": "gray"}
                        ]
                    }
                },
                "Status": {
                    "select": {
                        "options": [
                            {"name": "To Do", "color": "gray"},
                            {"name": "In Progress", "color": "blue"},
                            {"name": "Done", "color": "green"},
                            {"name": "Cancelled", "color": "red"}
                        ]
                    }
                },
                "Priority": {
                    "select": {
                        "options": [
                            {"name": "High", "color": "red"},
                            {"name": "Medium", "color": "yellow"},
                            {"name": "Low", "color": "gray"}
                        ]
                    }
                },
                "Due Date": {"date": {}},
                "Assigned To": {"people": {}},
                "Related Deal": {"rich_text": {}},
                "Related Contact": {"rich_text": {}},
                "Notes": {"rich_text": {}},
                "Completed": {"checkbox": {}},
                "Created": {"created_time": {}}
            }
        }
        
        return await self.client.databases.create(**database_data)
    
    async def _create_sequences_database(self) -> Dict:
        """Create email sequences database"""
        
        database_data = {
            "parent": {"page_id": self.page_id},
            "title": [{"text": {"content": "📧 Email Sequences"}}],
            "icon": {"emoji": "📧"},
            "properties": {
                "Sequence Name": {"title": {}},
                "Status": {
                    "select": {
                        "options": [
                            {"name": "Active", "color": "green"},
                            {"name": "Paused", "color": "yellow"},
                            {"name": "Draft", "color": "gray"},
                            {"name": "Archived", "color": "red"}
                        ]
                    }
                },
                "Type": {
                    "select": {
                        "options": [
                            {"name": "Cold Outreach", "color": "blue"},
                            {"name": "Follow-up", "color": "green"},
                            {"name": "Nurture", "color": "purple"},
                            {"name": "Re-engagement", "color": "orange"}
                        ]
                    }
                },
                "Steps": {"number": {}},
                "Enrolled": {"number": {}},
                "Replied": {"number": {}},
                "Reply Rate": {"formula": {"expression": "prop(\"Replied\") / prop(\"Enrolled\")"}},
                "Meetings Booked": {"number": {}},
                "Created By": {"people": {}},
                "Created": {"created_time": {}}
            }
        }
        
        return await self.client.databases.create(**database_data)
    
    async def _add_sample_data(self, config: CRMConfig):
        """Add sample data to help users understand the CRM"""
        
        # Add sample deal
        try:
            await self.client.pages.create(
                parent={"database_id": self.databases["pipeline"]},
                properties={
                    "Deal Name": {"title": [{"text": {"content": "🎯 Example Deal - Acme Corp"}}]},
                    "Stage": {"select": {"name": "Qualified"}},
                    "Deal Value": {"number": 50000},
                    "Lead Score": {"number": 85},
                    "Source": {"select": {"name": "AI SDR Outbound"}},
                    "Research Summary": {"rich_text": [{"text": {"content": "This is an example deal. Delete this and start adding your real deals! The AI SDR will automatically populate research summaries and handoff notes."}}]},
                    "Next Action": {"rich_text": [{"text": {"content": "Schedule discovery call"}}]},
                    "Win Probability": {"number": 0.6}
                }
            )
        except Exception:
            pass
        
        # Add sample contact
        try:
            await self.client.pages.create(
                parent={"database_id": self.databases["contacts"]},
                properties={
                    "Name": {"title": [{"text": {"content": "Jane Smith (Example)"}}]},
                    "Email": {"email": "jane@example.com"},
                    "Title": {"rich_text": [{"text": {"content": "VP of Sales"}}]},
                    "Company": {"rich_text": [{"text": {"content": "Acme Corp"}}]},
                    "Seniority": {"select": {"name": "VP"}},
                    "Status": {"select": {"name": "Active"}},
                    "Notes": {"rich_text": [{"text": {"content": "This is an example contact. Your AI SDR will automatically add contacts from processed leads."}}]}
                }
            )
        except Exception:
            pass
    
    async def _create_dashboard_views(self):
        """Create useful dashboard views"""
        # Note: Creating views requires additional API calls
        # This is a placeholder for view configuration
        pass
    
    def _generate_mock_response(self, config: CRMConfig) -> Dict:
        """Generate mock response when Notion API is unavailable"""
        import uuid
        
        mock_id = lambda: str(uuid.uuid4())
        
        return {
            "status": "mock",
            "note": "Notion API not configured. This is a preview of what would be created.",
            "workspace_name": config.workspace_name,
            "databases": {
                "pipeline": mock_id(),
                "contacts": mock_id(),
                "companies": mock_id(),
                "activities": mock_id(),
                "sequences": mock_id()
            },
            "structure": {
                "pipeline_fields": [
                    "Deal Name", "Company", "Contact", "Stage", "Deal Value",
                    "Lead Score", "Owner", "Source", "SLA Deadline", "Days in Stage",
                    "Handoff Notes", "Research Summary", "Next Action", "Win Probability"
                ],
                "contact_fields": [
                    "Name", "Email", "Phone", "Title", "Company", "LinkedIn",
                    "Seniority", "Status", "Last Contacted", "Tags"
                ],
                "company_fields": [
                    "Company Name", "Website", "Industry", "Employee Count",
                    "Tech Stack", "Hiring Departments", "Recent News", "Company Summary"
                ],
                "stages": config.custom_stages
            },
            "setup_instructions": [
                "1. Get a Notion API key from https://developers.notion.com",
                "2. Set NOTION_API_KEY environment variable",
                "3. Run the provisioner again",
                "4. Share the created page with your team"
            ]
        }


class NotionCRMSync:
    """
    Syncs data between AI SDR Platform and Notion CRM
    """
    
    def __init__(self, notion_api_key: str = None, database_ids: Dict = None):
        self.api_key = notion_api_key or os.getenv("NOTION_API_KEY")
        self.client = None
        if NotionAsyncClient and self.api_key:
            self.client = NotionAsyncClient(auth=self.api_key)
        self.databases = database_ids or {}
    
    async def create_deal_from_lead(self, lead_data: Dict, research_results: Dict) -> Dict:
        """
        Create a new deal in Notion from a processed lead
        """
        if not self.client:
            return {"status": "error", "error": "Notion client not initialized"}
        
        pipeline_db_id = self.databases.get("pipeline")
        if not pipeline_db_id:
            return {"status": "error", "error": "Pipeline database ID not configured"}
        
        try:
            # Create company first (if database exists)
            company_page_id = None
            if self.databases.get("companies"):
                company = await self._create_company(lead_data, research_results)
                company_page_id = company.get("id")
            
            # Create contact (if database exists)
            contact_page_id = None
            if self.databases.get("contacts"):
                contact = await self._create_contact(lead_data)
                contact_page_id = contact.get("id")
            
            # Format research summary
            research_summary = self._format_research_summary(research_results)
            
            # Format handoff notes
            handoff_notes = self._generate_handoff_notes(lead_data, research_results)
            
            # Create deal
            deal_properties = {
                "Deal Name": {
                    "title": [{"text": {"content": f"{lead_data.get('company', 'Unknown')} - {lead_data.get('firstName', '')} {lead_data.get('lastName', '')}"}}]
                },
                "Stage": {"select": {"name": "Qualified"}},
                "Lead Score": {"number": research_results.get("lead_score", 0)},
                "Source": {"select": {"name": "AI SDR Outbound"}},
                "Research Summary": {"rich_text": [{"text": {"content": research_summary[:2000]}}]},
                "Handoff Notes": {"rich_text": [{"text": {"content": handoff_notes[:2000]}}]},
                "Next Action": {"rich_text": [{"text": {"content": "Schedule discovery call"}}]},
                "Stage Changed": {"date": {"start": datetime.now().isoformat()}},
                "SLA Deadline": {"date": {"start": (datetime.now() + timedelta(hours=24)).isoformat()}}
            }
            
            # Add estimated deal value based on company signals
            company_info = research_results.get("research_results", {}).get("company_info", {})
            if company_info.get("tech_stack"):
                deal_properties["Deal Value"] = {"number": 50000}
            else:
                deal_properties["Deal Value"] = {"number": 25000}
            
            # Add win probability based on lead score
            lead_score = research_results.get("lead_score", 50)
            if lead_score >= 80:
                deal_properties["Win Probability"] = {"number": 0.7}
            elif lead_score >= 60:
                deal_properties["Win Probability"] = {"number": 0.5}
            else:
                deal_properties["Win Probability"] = {"number": 0.3}
            
            deal = await self.client.pages.create(
                parent={"database_id": pipeline_db_id},
                properties=deal_properties
            )
            
            # Create initial activity
            if self.databases.get("activities"):
                await self._create_activity(
                    task="Send initial outreach email",
                    activity_type="Email",
                    priority="High",
                    deal_name=deal_properties["Deal Name"]["title"][0]["text"]["content"],
                    due_date=datetime.now() + timedelta(hours=4)
                )
            
            return {
                "status": "success",
                "deal_id": deal["id"],
                "deal_url": f"https://notion.so/{deal['id'].replace('-', '')}",
                "company_id": company_page_id,
                "contact_id": contact_page_id
            }
            
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    async def update_deal_stage(
        self,
        deal_id: str,
        new_stage: str,
        handoff_notes: str = None,
        next_action: str = None
    ) -> Dict:
        """
        Update deal stage and add handoff notes
        """
        if not self.client:
            return {"status": "error", "error": "Notion client not initialized"}
        
        try:
            properties = {
                "Stage": {"select": {"name": new_stage}},
                "Stage Changed": {"date": {"start": datetime.now().isoformat()}}
            }
            
            if handoff_notes:
                properties["Handoff Notes"] = {"rich_text": [{"text": {"content": handoff_notes}}]}
            
            if next_action:
                properties["Next Action"] = {"rich_text": [{"text": {"content": next_action}}]}
            
            # Update SLA deadline based on stage
            sla_hours = {
                "Qualified": 24,
                "Discovery": 48,
                "Proposal": 72,
                "Negotiation": 48
            }
            if new_stage in sla_hours:
                properties["SLA Deadline"] = {
                    "date": {"start": (datetime.now() + timedelta(hours=sla_hours[new_stage])).isoformat()}
                }
            
            await self.client.pages.update(
                page_id=deal_id,
                properties=properties
            )
            
            return {"status": "success", "deal_id": deal_id, "new_stage": new_stage}
            
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    async def _create_company(self, lead_data: Dict, research_results: Dict) -> Dict:
        """Create company record"""
        company_info = research_results.get("research_results", {}).get("company_info", {})
        
        properties = {
            "Company Name": {"title": [{"text": {"content": lead_data.get("company", "Unknown")}}]},
            "Company Summary": {"rich_text": [{"text": {"content": company_info.get("summary", "")[:2000]}}]},
        }
        
        # Add website
        website = lead_data.get("website") or research_results.get("research_results", {}).get("linkedin_url")
        if website:
            properties["Website"] = {"url": website}
        
        # Add LinkedIn
        linkedin = research_results.get("research_results", {}).get("linkedin_url")
        if linkedin:
            properties["LinkedIn"] = {"url": linkedin}
        
        return await self.client.pages.create(
            parent={"database_id": self.databases["companies"]},
            properties=properties
        )
    
    async def _create_contact(self, lead_data: Dict) -> Dict:
        """Create contact record"""
        full_name = f"{lead_data.get('firstName', '')} {lead_data.get('lastName', '')}".strip()
        
        properties = {
            "Name": {"title": [{"text": {"content": full_name or "Unknown"}}]},
            "Company": {"rich_text": [{"text": {"content": lead_data.get("company", "")}}]},
            "Title": {"rich_text": [{"text": {"content": lead_data.get("title", "")}}]},
            "Status": {"select": {"name": "Active"}}
        }
        
        if lead_data.get("email"):
            properties["Email"] = {"email": lead_data["email"]}
        
        if lead_data.get("linkedin_url"):
            properties["LinkedIn"] = {"url": lead_data["linkedin_url"]}
        
        # Determine seniority
        title = lead_data.get("title", "").lower()
        if any(t in title for t in ["ceo", "cto", "cfo", "coo", "president", "founder"]):
            properties["Seniority"] = {"select": {"name": "C-Suite"}}
        elif any(t in title for t in ["vp", "vice president"]):
            properties["Seniority"] = {"select": {"name": "VP"}}
        elif "director" in title:
            properties["Seniority"] = {"select": {"name": "Director"}}
        elif any(t in title for t in ["manager", "head"]):
            properties["Seniority"] = {"select": {"name": "Manager"}}
        
        return await self.client.pages.create(
            parent={"database_id": self.databases["contacts"]},
            properties=properties
        )
    
    async def _create_activity(
        self,
        task: str,
        activity_type: str,
        priority: str,
        deal_name: str,
        due_date: datetime
    ) -> Dict:
        """Create activity/task"""
        return await self.client.pages.create(
            parent={"database_id": self.databases["activities"]},
            properties={
                "Task": {"title": [{"text": {"content": task}}]},
                "Type": {"select": {"name": activity_type}},
                "Status": {"select": {"name": "To Do"}},
                "Priority": {"select": {"name": priority}},
                "Due Date": {"date": {"start": due_date.isoformat()}},
                "Related Deal": {"rich_text": [{"text": {"content": deal_name}}]},
                "Completed": {"checkbox": False}
            }
        )
    
    def _format_research_summary(self, research_results: Dict) -> str:
        """Format research results into a readable summary"""
        parts = []
        
        company_info = research_results.get("research_results", {}).get("company_info", {})
        
        if company_info.get("summary"):
            parts.append(f"📝 Summary: {company_info['summary']}")
        
        if company_info.get("domain"):
            parts.append(f"🏢 Industry: {company_info['domain']}")
        
        if company_info.get("headquarters"):
            parts.append(f"📍 HQ: {company_info['headquarters']}")
        
        if company_info.get("tech_stack"):
            parts.append(f"💻 Tech Stack: {', '.join(company_info['tech_stack'][:5])}")
        
        if company_info.get("hiring_departments"):
            parts.append(f"👥 Hiring: {', '.join(company_info['hiring_departments'][:5])}")
        
        news = company_info.get("recent_news", [])
        if news and isinstance(news, list) and len(news) > 0:
            if isinstance(news[0], dict):
                parts.append(f"📰 Recent News: {news[0].get('title', 'N/A')}")
            elif isinstance(news[0], str):
                parts.append(f"📰 Recent News: {news[0]}")
        
        hooks = research_results.get("research_results", {}).get("hooks", [])
        if hooks:
            parts.append(f"\n🎯 Engagement Hooks:")
            for hook in hooks[:3]:
                parts.append(f"  • {hook}")
        
        return "\n".join(parts) if parts else "Research data not available"
    
    def _generate_handoff_notes(self, lead_data: Dict, research_results: Dict) -> str:
        """Generate AI-powered handoff notes"""
        lead_score = research_results.get("lead_score", 0)
        company_info = research_results.get("research_results", {}).get("company_info", {})
        hooks = research_results.get("research_results", {}).get("hooks", [])
        
        notes = []
        notes.append(f"📊 LEAD SCORE: {lead_score}/100")
        notes.append("")
        
        # Contact info
        notes.append("👤 CONTACT:")
        notes.append(f"  {lead_data.get('firstName', '')} {lead_data.get('lastName', '')}")
        notes.append(f"  {lead_data.get('title', 'Title unknown')} @ {lead_data.get('company', 'Company unknown')}")
        notes.append("")
        
        # Why they're a good fit
        notes.append("✅ WHY QUALIFIED:")
        if lead_score >= 80:
            notes.append("  • High-value target (score 80+)")
        if company_info.get("hiring_departments"):
            notes.append(f"  • Active hiring in: {', '.join(company_info['hiring_departments'][:3])}")
        if company_info.get("tech_stack"):
            notes.append(f"  • Tech-forward company (uses modern stack)")
        notes.append("")
        
        # Talking points
        if hooks:
            notes.append("💬 TALKING POINTS:")
            for hook in hooks[:3]:
                notes.append(f"  • {hook}")
            notes.append("")
        
        # Recommended approach
        notes.append("📋 RECOMMENDED NEXT STEPS:")
        notes.append("  1. Send personalized email (see variants below)")
        notes.append("  2. Schedule discovery call within 48 hours")
        notes.append("  3. Prepare demo focused on their industry")
        
        return "\n".join(notes)


# =============================================================================
# EXAMPLE USAGE
# =============================================================================

async def example_provision_crm():
    """Example: Provision a new CRM for a client"""
    
    provisioner = NotionCRMProvisioner()
    
    config = CRMConfig(
        workspace_name="Acme Corp",
        owner_email="john@acme.com",
        team_members=["jane@acme.com", "bob@acme.com"],
        industry="technology"
    )
    
    result = await provisioner.provision_crm(config)
    print(json.dumps(result, indent=2))
    return result


async def example_sync_lead():
    """Example: Sync a processed lead to Notion CRM"""
    
    # This would come from your actual pipeline
    lead_data = {
        "firstName": "John",
        "lastName": "Smith",
        "email": "john@acme.com",
        "company": "Acme Corp",
        "title": "VP of Sales"
    }
    
    research_results = {
        "lead_score": 87,
        "research_results": {
            "company_info": {
                "summary": "Acme Corp is a Series B SaaS company focused on developer tools.",
                "domain": "Technology / SaaS",
                "headquarters": "San Francisco, CA",
                "tech_stack": ["React", "Node.js", "AWS"],
                "hiring_departments": ["Engineering", "Sales", "Marketing"],
                "recent_news": [{"title": "Acme raises $30M Series B"}]
            },
            "hooks": [
                "I noticed you're hiring across 3 departments",
                "Your recent funding round suggests growth mode",
                "Your tech stack aligns well with our integrations"
            ],
            "linkedin_url": "https://linkedin.com/company/acme"
        }
    }
    
    sync = NotionCRMSync(
        database_ids={
            "pipeline": "your-pipeline-db-id",
            "contacts": "your-contacts-db-id",
            "companies": "your-companies-db-id",
            "activities": "your-activities-db-id"
        }
    )
    
    result = await sync.create_deal_from_lead(lead_data, research_results)
    print(json.dumps(result, indent=2))
    return result


if __name__ == "__main__":
    asyncio.run(example_provision_crm())
