-- GuardStack Database Initialization Script
-- This script sets up the initial database schema

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "vector";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- Create schemas
CREATE SCHEMA IF NOT EXISTS guardstack;

-- Set search path
SET search_path TO guardstack, public;

-- Models table
CREATE TABLE IF NOT EXISTS models (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    type VARCHAR(50) NOT NULL CHECK (type IN ('genai', 'predictive', 'agentic')),
    provider VARCHAR(100),
    version VARCHAR(100),
    description TEXT,
    endpoint VARCHAR(500),
    status VARCHAR(50) DEFAULT 'active' CHECK (status IN ('active', 'inactive', 'archived')),
    risk_tier VARCHAR(50) DEFAULT 'medium' CHECK (risk_tier IN ('low', 'medium', 'high', 'critical')),
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create index for text search on model name
CREATE INDEX IF NOT EXISTS idx_models_name_trgm ON models USING gin (name gin_trgm_ops);
CREATE INDEX IF NOT EXISTS idx_models_type ON models (type);
CREATE INDEX IF NOT EXISTS idx_models_status ON models (status);

-- Evaluations table
CREATE TABLE IF NOT EXISTS evaluations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    model_id UUID NOT NULL REFERENCES models(id) ON DELETE CASCADE,
    status VARCHAR(50) DEFAULT 'pending' CHECK (status IN ('pending', 'running', 'completed', 'failed', 'cancelled')),
    overall_score DECIMAL(5, 4),
    overall_status VARCHAR(50) CHECK (overall_status IN ('pass', 'warn', 'fail')),
    config JSONB DEFAULT '{}',
    error_message TEXT,
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_evaluations_model_id ON evaluations (model_id);
CREATE INDEX IF NOT EXISTS idx_evaluations_status ON evaluations (status);
CREATE INDEX IF NOT EXISTS idx_evaluations_created_at ON evaluations (created_at DESC);

-- Pillar results table
CREATE TABLE IF NOT EXISTS pillar_results (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    evaluation_id UUID NOT NULL REFERENCES evaluations(id) ON DELETE CASCADE,
    pillar_name VARCHAR(50) NOT NULL,
    score DECIMAL(5, 4),
    status VARCHAR(50) CHECK (status IN ('pass', 'warn', 'fail')),
    metrics JSONB DEFAULT '{}',
    findings JSONB DEFAULT '[]',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_pillar_results_evaluation_id ON pillar_results (evaluation_id);
CREATE INDEX IF NOT EXISTS idx_pillar_results_pillar_name ON pillar_results (pillar_name);

-- Guardrails table
CREATE TABLE IF NOT EXISTS guardrails (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    type VARCHAR(100) NOT NULL,
    description TEXT,
    enabled BOOLEAN DEFAULT true,
    config JSONB DEFAULT '{}',
    applies_to UUID[] DEFAULT '{}',
    triggered_count INTEGER DEFAULT 0,
    last_triggered TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_guardrails_enabled ON guardrails (enabled);
CREATE INDEX IF NOT EXISTS idx_guardrails_type ON guardrails (type);

-- Compliance frameworks table
CREATE TABLE IF NOT EXISTS compliance_frameworks (
    id VARCHAR(100) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    version VARCHAR(50),
    controls JSONB DEFAULT '[]',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Compliance assessments table
CREATE TABLE IF NOT EXISTS compliance_assessments (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    framework_id VARCHAR(100) NOT NULL REFERENCES compliance_frameworks(id) ON DELETE CASCADE,
    model_id UUID REFERENCES models(id) ON DELETE SET NULL,
    control_id VARCHAR(100) NOT NULL,
    status VARCHAR(50) DEFAULT 'not_assessed' CHECK (status IN ('not_assessed', 'implemented', 'partial', 'not_implemented', 'not_applicable')),
    evidence JSONB DEFAULT '[]',
    notes TEXT,
    assessed_at TIMESTAMP WITH TIME ZONE,
    assessed_by VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_compliance_assessments_framework ON compliance_assessments (framework_id);
CREATE INDEX IF NOT EXISTS idx_compliance_assessments_model ON compliance_assessments (model_id);

-- Connectors table
CREATE TABLE IF NOT EXISTS connectors (
    id VARCHAR(100) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    provider VARCHAR(100) NOT NULL,
    status VARCHAR(50) DEFAULT 'disconnected' CHECK (status IN ('connected', 'disconnected', 'error')),
    config JSONB DEFAULT '{}',
    last_sync TIMESTAMP WITH TIME ZONE,
    models_count INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Audit logs table
CREATE TABLE IF NOT EXISTS audit_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    event_type VARCHAR(100) NOT NULL,
    entity_type VARCHAR(100),
    entity_id UUID,
    actor_id VARCHAR(255),
    actor_type VARCHAR(50),
    action VARCHAR(50) NOT NULL,
    details JSONB DEFAULT '{}',
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_audit_logs_entity ON audit_logs (entity_type, entity_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_actor ON audit_logs (actor_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_created_at ON audit_logs (created_at DESC);

-- Embeddings table for vector search
CREATE TABLE IF NOT EXISTS embeddings (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    source_type VARCHAR(100) NOT NULL,
    source_id UUID NOT NULL,
    content TEXT NOT NULL,
    embedding vector(1536),
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_embeddings_source ON embeddings (source_type, source_id);
CREATE INDEX IF NOT EXISTS idx_embeddings_vector ON embeddings USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

-- SPM Inventory table
CREATE TABLE IF NOT EXISTS spm_inventory (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    type VARCHAR(100) NOT NULL,
    provider VARCHAR(100),
    endpoint VARCHAR(500),
    risk_tier VARCHAR(50) DEFAULT 'medium',
    owner VARCHAR(255),
    department VARCHAR(255),
    status VARCHAR(50) DEFAULT 'active',
    config JSONB DEFAULT '{}',
    last_scan TIMESTAMP WITH TIME ZONE,
    discovered_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_spm_inventory_type ON spm_inventory (type);
CREATE INDEX IF NOT EXISTS idx_spm_inventory_status ON spm_inventory (status);

-- SPM Scans table
CREATE TABLE IF NOT EXISTS spm_scans (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    system_id UUID REFERENCES spm_inventory(id) ON DELETE CASCADE,
    status VARCHAR(50) DEFAULT 'pending',
    findings JSONB DEFAULT '[]',
    summary JSONB DEFAULT '{}',
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_spm_scans_system ON spm_scans (system_id);
CREATE INDEX IF NOT EXISTS idx_spm_scans_status ON spm_scans (status);

-- SPM Policies table
CREATE TABLE IF NOT EXISTS spm_policies (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    rules JSONB DEFAULT '[]',
    applies_to JSONB DEFAULT '[]',
    enabled BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Agentic sessions table
CREATE TABLE IF NOT EXISTS agentic_sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    agent_id VARCHAR(255) NOT NULL,
    user_id VARCHAR(255),
    status VARCHAR(50) DEFAULT 'active',
    metadata JSONB DEFAULT '{}',
    started_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    ended_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_agentic_sessions_agent ON agentic_sessions (agent_id);
CREATE INDEX IF NOT EXISTS idx_agentic_sessions_status ON agentic_sessions (status);

-- Agentic interceptions table
CREATE TABLE IF NOT EXISTS agentic_interceptions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id UUID REFERENCES agentic_sessions(id) ON DELETE CASCADE,
    tool_name VARCHAR(255) NOT NULL,
    arguments JSONB DEFAULT '{}',
    status VARCHAR(50) NOT NULL CHECK (status IN ('approved', 'blocked', 'modified')),
    risk_score DECIMAL(5, 4),
    checks JSONB DEFAULT '[]',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_agentic_interceptions_session ON agentic_interceptions (session_id);
CREATE INDEX IF NOT EXISTS idx_agentic_interceptions_status ON agentic_interceptions (status);

-- Update timestamp function
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create triggers for updated_at
CREATE TRIGGER update_models_updated_at
    BEFORE UPDATE ON models
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_evaluations_updated_at
    BEFORE UPDATE ON evaluations
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_guardrails_updated_at
    BEFORE UPDATE ON guardrails
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_compliance_frameworks_updated_at
    BEFORE UPDATE ON compliance_frameworks
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_compliance_assessments_updated_at
    BEFORE UPDATE ON compliance_assessments
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_connectors_updated_at
    BEFORE UPDATE ON connectors
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_spm_inventory_updated_at
    BEFORE UPDATE ON spm_inventory
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_spm_policies_updated_at
    BEFORE UPDATE ON spm_policies
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Insert default compliance frameworks
INSERT INTO compliance_frameworks (id, name, description, version) VALUES
    ('eu-ai-act', 'EU AI Act', 'European Union Artificial Intelligence Act', '2024'),
    ('nist-ai-rmf', 'NIST AI RMF', 'NIST AI Risk Management Framework', '1.0'),
    ('iso-42001', 'ISO/IEC 42001', 'AI Management System Standard', '2023'),
    ('soc2', 'SOC 2 Type II', 'Service Organization Control 2', '2017'),
    ('gdpr', 'GDPR', 'General Data Protection Regulation', '2018'),
    ('ccpa', 'CCPA', 'California Consumer Privacy Act', '2020')
ON CONFLICT (id) DO NOTHING;

-- Insert default connectors
INSERT INTO connectors (id, name, provider, status) VALUES
    ('openai', 'OpenAI', 'openai', 'disconnected'),
    ('anthropic', 'Anthropic', 'anthropic', 'disconnected'),
    ('azure-openai', 'Azure OpenAI', 'azure', 'disconnected'),
    ('aws-bedrock', 'AWS Bedrock', 'aws', 'disconnected'),
    ('huggingface', 'Hugging Face', 'huggingface', 'disconnected'),
    ('ollama', 'Ollama', 'ollama', 'disconnected'),
    ('vllm', 'vLLM', 'vllm', 'disconnected')
ON CONFLICT (id) DO NOTHING;

-- Grant permissions
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA guardstack TO guardstack;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA guardstack TO guardstack;
GRANT USAGE ON SCHEMA guardstack TO guardstack;
