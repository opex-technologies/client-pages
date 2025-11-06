-- opex_dev.clients table schema
-- Master list of Opex Technologies clients
-- Created: November 5, 2025

CREATE TABLE IF NOT EXISTS `opex-data-lake-k23k4y98m.opex_dev.clients` (
  -- Primary identifier
  client_id STRING NOT NULL,

  -- Client information
  name STRING NOT NULL,
  category STRING,  -- Industry vertical (Healthcare, Finance, Retail, etc.)

  -- Branding
  logo_url STRING,  -- URL to client's logo (for customized reports)

  -- Contact information
  primary_contact_name STRING,
  primary_contact_email STRING,
  primary_contact_phone STRING,

  -- Company details
  company_size STRING,  -- Enterprise, Mid-Market, SMB
  employee_count INT64,
  headquarters_location STRING,

  -- Opex relationship
  account_manager STRING,  -- Opex employee managing this client
  client_since TIMESTAMP,

  -- Metadata
  created_at TIMESTAMP NOT NULL,  -- Set by application to CURRENT_TIMESTAMP()
  updated_at TIMESTAMP,

  -- Status
  is_active BOOLEAN NOT NULL,  -- Default TRUE, set in application (can be deactivated without deletion)

  -- Statistics (can be populated by analytics)
  project_count INT64,  -- Default 0, set in application (how many evaluation projects for this client)
  last_project_date TIMESTAMP,

  -- Notes
  notes STRING  -- Internal notes about the client
)
OPTIONS(
  description="Master list of Opex Technologies clients"
);

-- Indexes (create separately):
-- CREATE INDEX idx_clients_name ON opex_dev.clients(name);
-- CREATE INDEX idx_clients_category ON opex_dev.clients(category);
-- CREATE INDEX idx_clients_active ON opex_dev.clients(is_active);

-- Usage:
-- This table can be used to:
-- 1. Track which client requested which provider evaluations
-- 2. Generate client-specific reports with branding
-- 3. Analyze client engagement and project history
-- 4. Customize form templates and scoring criteria per client

-- Client vs Provider:
-- "Client" = Opex Technologies customer (the company requesting evaluations)
-- "Provider" = Vendor being evaluated on behalf of the client

-- Example Scenario:
-- Client: "Acme Healthcare" requests evaluation of providers
-- Providers being evaluated: AT&T, Verizon, Cato Networks (for SASE solution)
-- Forms sent to providers, responses scored, reports delivered to Acme Healthcare

-- Permission Integration:
-- Users can be granted permissions scoped to specific clients
-- E.g., User X can only view/score data for "Acme Healthcare" client
-- This is managed via auth.permission_groups (company field = client_id)
