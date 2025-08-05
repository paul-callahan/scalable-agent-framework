-- Create tenant_info table for storing tenant provisioning and lifecycle data
CREATE TABLE tenant_info (
    id VARCHAR(36) PRIMARY KEY,
    tenant_id VARCHAR(50) UNIQUE NOT NULL,
    tenant_name VARCHAR(50) NOT NULL,
    creation_time TIMESTAMP NOT NULL,
    disable_time TIMESTAMP,
    enabled BOOLEAN NOT NULL DEFAULT true,
    provision_notes VARCHAR(512),
    disable_notes VARCHAR(512)
);

-- Create indexes for performance
CREATE INDEX idx_tenant_info_tenant_id ON tenant_info(tenant_id);
CREATE INDEX idx_tenant_info_creation_time ON tenant_info(creation_time);
CREATE INDEX idx_tenant_info_enabled ON tenant_info(enabled);

-- Add comments for documentation
COMMENT ON TABLE tenant_info IS 'Stores tenant provisioning and lifecycle information';
COMMENT ON COLUMN tenant_info.id IS 'Unique identifier for the tenant record';
COMMENT ON COLUMN tenant_info.tenant_id IS 'Unique tenant identifier used across the system';
COMMENT ON COLUMN tenant_info.tenant_name IS 'Human-readable name for the tenant';
COMMENT ON COLUMN tenant_info.creation_time IS 'Timestamp when the tenant was provisioned';
COMMENT ON COLUMN tenant_info.disable_time IS 'Timestamp when the tenant was disabled (null if enabled)';
COMMENT ON COLUMN tenant_info.enabled IS 'Whether the tenant is currently enabled';
COMMENT ON COLUMN tenant_info.provision_notes IS 'Optional notes about the provisioning process';
COMMENT ON COLUMN tenant_info.disable_notes IS 'Optional notes about why the tenant was disabled'; 