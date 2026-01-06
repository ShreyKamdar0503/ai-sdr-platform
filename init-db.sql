-- AI SDR Platform - Database Initialization
-- This script creates the core tables for the platform

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Workspaces table
CREATE TABLE IF NOT EXISTS workspaces (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    workspace_id VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    mode VARCHAR(50) DEFAULT 'saas' CHECK (mode IN ('saas', 'paas')),
    n8n_base_url VARCHAR(500),
    config JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Leads table
CREATE TABLE IF NOT EXISTS leads (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    workspace_id VARCHAR(255) REFERENCES workspaces(workspace_id),
    email VARCHAR(255) NOT NULL,
    first_name VARCHAR(255),
    last_name VARCHAR(255),
    company VARCHAR(255),
    title VARCHAR(255),
    source VARCHAR(255),
    score INTEGER DEFAULT 0,
    status VARCHAR(50) DEFAULT 'new',
    research_data JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create index on workspace_id and email
CREATE INDEX IF NOT EXISTS idx_leads_workspace ON leads(workspace_id);
CREATE INDEX IF NOT EXISTS idx_leads_email ON leads(email);

-- Email sequences table
CREATE TABLE IF NOT EXISTS email_sequences (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    lead_id UUID REFERENCES leads(id),
    workspace_id VARCHAR(255) REFERENCES workspaces(workspace_id),
    variant VARCHAR(50),
    subject VARCHAR(500),
    body TEXT,
    scheduled_at TIMESTAMP WITH TIME ZONE,
    sent_at TIMESTAMP WITH TIME ZONE,
    opened_at TIMESTAMP WITH TIME ZONE,
    clicked_at TIMESTAMP WITH TIME ZONE,
    replied_at TIMESTAMP WITH TIME ZONE,
    status VARCHAR(50) DEFAULT 'draft',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Agent executions log
CREATE TABLE IF NOT EXISTS agent_executions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    workspace_id VARCHAR(255),
    lead_id UUID REFERENCES leads(id),
    agent_name VARCHAR(100) NOT NULL,
    input_data JSONB,
    output_data JSONB,
    cost_usd DECIMAL(10, 6) DEFAULT 0,
    duration_ms INTEGER,
    status VARCHAR(50) DEFAULT 'success',
    error_message TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_agent_exec_workspace ON agent_executions(workspace_id);
CREATE INDEX IF NOT EXISTS idx_agent_exec_lead ON agent_executions(lead_id);

-- GTM events log
CREATE TABLE IF NOT EXISTS gtm_events (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    workspace_id VARCHAR(255),
    event_type VARCHAR(100) NOT NULL,
    payload JSONB,
    decisions JSONB,
    actions JSONB,
    processed_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_gtm_events_workspace ON gtm_events(workspace_id);
CREATE INDEX IF NOT EXISTS idx_gtm_events_type ON gtm_events(event_type);

-- x402 transactions log
CREATE TABLE IF NOT EXISTS x402_transactions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    workspace_id VARCHAR(255),
    wallet_address VARCHAR(100),
    network VARCHAR(50),
    asset VARCHAR(20) DEFAULT 'USDC',
    amount_raw VARCHAR(50),
    amount_usd DECIMAL(10, 6),
    pay_to VARCHAR(100),
    tx_hash VARCHAR(100),
    status VARCHAR(50) DEFAULT 'pending',
    agent_name VARCHAR(100),
    endpoint VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_x402_wallet ON x402_transactions(wallet_address);
CREATE INDEX IF NOT EXISTS idx_x402_status ON x402_transactions(status);

-- n8n workflow mappings (for PaaS mode)
CREATE TABLE IF NOT EXISTS n8n_workflow_mappings (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    workspace_id VARCHAR(255) REFERENCES workspaces(workspace_id),
    action_name VARCHAR(100) NOT NULL,
    webhook_url VARCHAR(500) NOT NULL,
    is_active BOOLEAN DEFAULT true,
    last_triggered_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(workspace_id, action_name)
);

-- API usage metrics
CREATE TABLE IF NOT EXISTS api_usage (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    workspace_id VARCHAR(255),
    endpoint VARCHAR(255) NOT NULL,
    method VARCHAR(10) NOT NULL,
    status_code INTEGER,
    response_time_ms INTEGER,
    request_size_bytes INTEGER,
    response_size_bytes INTEGER,
    ip_address VARCHAR(50),
    user_agent TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_api_usage_workspace ON api_usage(workspace_id);
CREATE INDEX IF NOT EXISTS idx_api_usage_created ON api_usage(created_at);

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create triggers for updated_at
CREATE TRIGGER update_workspaces_updated_at
    BEFORE UPDATE ON workspaces
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_leads_updated_at
    BEFORE UPDATE ON leads
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Insert default demo workspace
INSERT INTO workspaces (workspace_id, name, mode, config)
VALUES ('demo-workspace', 'Demo Workspace', 'saas', '{"auto_approval_threshold": 90}')
ON CONFLICT (workspace_id) DO NOTHING;

-- Create additional database for n8n (if using PostgreSQL for n8n)
-- Note: This requires superuser privileges
-- CREATE DATABASE ai_sdr_n8n;
