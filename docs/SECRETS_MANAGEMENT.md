# SMEFlow Secrets Management Strategy

## Overview

This document defines the comprehensive secrets management strategy for SMEFlow platform, covering development, staging, and production environments with multi-tenant isolation and African market compliance requirements.

---

## 🔐 Security Principles

### Core Requirements
- **Zero Trust**: No secrets in source code, logs, or configuration files
- **Least Privilege**: Minimal access scope per service and tenant
- **Defense in Depth**: Multiple layers of protection and encryption
- **Audit Trail**: Complete logging of secret access and modifications
- **Regional Compliance**: CBN (Nigeria), POPIA (South Africa), GDPR adherence

### Multi-Tenant Isolation
- **Tenant-Scoped Secrets**: Each tenant's credentials isolated and encrypted
- **Cross-Tenant Prevention**: No tenant can access another's secrets
- **Regional Data Residency**: Secrets stored in compliance with local regulations
- **Granular Access Control**: Role-based access tied to Keycloak authentication

---

## 🌍 Environment-Specific Strategies

### Development Environment

**Approach**: Local `.env` files with gitignore protection

**Implementation**:
```bash
# .env (gitignored)
DATABASE_URL=postgresql+asyncpg://smeflow:smeflow123@localhost:5432/smeflow
REDIS_PASSWORD=dev_redis_pass
KEYCLOAK_CLIENT_SECRET=dev_keycloak_secret
OPENAI_API_KEY=sk-dev-key-here
N8N_API_KEY=dev_n8n_key

# African Market Integration Keys (Development)
MPESA_CONSUMER_KEY=dev_mpesa_key
MPESA_CONSUMER_SECRET=dev_mpesa_secret
PAYSTACK_SECRET_KEY=sk_test_paystack_key
JUMIA_API_KEY=dev_jumia_key
```

**Security Measures**:
- `.env` files never committed to version control
- `.env.example` templates provided without actual secrets
- Local encryption for sensitive development keys
- Regular rotation of development credentials (monthly)

### Staging Environment

**Approach**: Docker Secrets with encrypted storage

**Implementation**:
```yaml
# docker-compose.staging.yml
version: '3.8'
services:
  smeflow-api:
    secrets:
      - database_url
      - redis_password
      - keycloak_client_secret
      - openai_api_key
      - mpesa_credentials
      - paystack_secret

secrets:
  database_url:
    external: true
  redis_password:
    external: true
  keycloak_client_secret:
    external: true
  openai_api_key:
    external: true
  mpesa_credentials:
    external: true
  paystack_secret:
    external: true
```

**Security Measures**:
- Docker secrets mounted as read-only files
- Secrets encrypted at rest using Docker Swarm encryption
- Access restricted to specific services only
- Automated secret rotation every 60 days

### Production Environment

**Approach**: HashiCorp Vault with Kubernetes integration

**Implementation**:
```yaml
# kubernetes/secrets-config.yaml
apiVersion: v1
kind: SecretProviderClass
metadata:
  name: smeflow-secrets
spec:
  provider: vault
  parameters:
    vaultAddress: "https://vault.smeflow.com"
    roleName: "smeflow-production"
    objects: |
      - objectName: "database-url"
        secretPath: "secret/smeflow/database"
        secretKey: "url"
      - objectName: "openai-api-key"
        secretPath: "secret/smeflow/llm"
        secretKey: "openai_key"
      - objectName: "mpesa-credentials"
        secretPath: "secret/smeflow/payments/mpesa"
        secretKey: "credentials"
```

**Security Measures**:
- Vault transit encryption for secrets at rest
- Dynamic secret generation where possible
- Short-lived tokens (15-minute TTL)
- Automated rotation every 30 days for critical secrets
- Audit logging to SigNoz and compliance systems

---

## 🔑 Secret Categories & Rotation Policies

### Database & Infrastructure Secrets
**Rotation Cycle**: 90 days
**Examples**: PostgreSQL passwords, Redis auth, internal service tokens

```bash
# Rotation Command Example
vault kv put secret/smeflow/database \
  url="postgresql+asyncpg://smeflow:$(generate_password)@postgres:5432/smeflow" \
  rotation_date="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
```

### LLM Provider API Keys
**Rotation Cycle**: 60 days
**Examples**: OpenAI, Anthropic, Google API keys

**Monitoring**: Track usage patterns and cost anomalies
**Fallback**: Multiple provider keys for redundancy

### African Market Integration Secrets
**Rotation Cycle**: 30 days (high-risk due to financial nature)
**Examples**: M-Pesa, Paystack, Jumia API credentials

**Special Requirements**:
- CBN compliance for Nigerian payment credentials
- POPIA compliance for South African financial data
- Encrypted storage with regional data residency

### Authentication & Authorization
**Rotation Cycle**: 30 days
**Examples**: Keycloak client secrets, Cerbos policy tokens, JWT signing keys

**Zero-Downtime Rotation**:
```bash
# JWT Key Rotation Strategy
# 1. Generate new key
vault kv put secret/smeflow/auth jwt_key_new="$(generate_jwt_key)"

# 2. Update application to accept both old and new keys
# 3. Switch to signing with new key
# 4. Remove old key after grace period
```

### n8N Integration Credentials
**Rotation Cycle**: 45 days
**Examples**: n8N API keys, webhook secrets, connector credentials

**Tenant Isolation**:
```python
# Tenant-specific credential storage
vault_path = f"secret/smeflow/tenants/{tenant_id}/n8n"
credentials = {
    "api_key": encrypted_api_key,
    "webhook_secret": webhook_secret,
    "created_at": datetime.utcnow().isoformat(),
    "expires_at": (datetime.utcnow() + timedelta(days=45)).isoformat()
}
```

---

## 🏗️ Implementation Architecture

### Secrets Service Layer

```python
# smeflow/core/secrets.py
from abc import ABC, abstractmethod
from typing import Dict, Optional
import hvac  # HashiCorp Vault client

class SecretsManager(ABC):
    """Abstract secrets manager interface."""
    
    @abstractmethod
    async def get_secret(self, path: str, tenant_id: Optional[str] = None) -> str:
        """Retrieve secret value."""
        pass
    
    @abstractmethod
    async def set_secret(self, path: str, value: str, tenant_id: Optional[str] = None) -> bool:
        """Store secret value."""
        pass
    
    @abstractmethod
    async def rotate_secret(self, path: str, tenant_id: Optional[str] = None) -> str:
        """Rotate secret and return new value."""
        pass

class VaultSecretsManager(SecretsManager):
    """Production Vault-based secrets manager."""
    
    def __init__(self, vault_url: str, role_name: str):
        self.client = hvac.Client(url=vault_url)
        self.role_name = role_name
    
    async def get_secret(self, path: str, tenant_id: Optional[str] = None) -> str:
        """Retrieve secret from Vault with tenant isolation."""
        if tenant_id:
            vault_path = f"secret/smeflow/tenants/{tenant_id}/{path}"
        else:
            vault_path = f"secret/smeflow/{path}"
        
        response = self.client.secrets.kv.v2.read_secret_version(path=vault_path)
        return response['data']['data']['value']

class EnvironmentSecretsManager(SecretsManager):
    """Development environment secrets manager."""
    
    async def get_secret(self, path: str, tenant_id: Optional[str] = None) -> str:
        """Retrieve secret from environment variables."""
        env_key = path.upper().replace('/', '_')
        if tenant_id:
            env_key = f"TENANT_{tenant_id.upper()}_{env_key}"
        
        return os.getenv(env_key)
```

### Multi-Tenant Secret Isolation

```python
# smeflow/integrations/secrets_integration.py
class TenantSecretsService:
    """Tenant-aware secrets management."""
    
    def __init__(self, secrets_manager: SecretsManager):
        self.secrets_manager = secrets_manager
    
    async def get_n8n_credentials(self, tenant_id: str) -> Dict[str, str]:
        """Get n8N credentials for specific tenant."""
        return {
            "api_key": await self.secrets_manager.get_secret("n8n/api_key", tenant_id),
            "webhook_secret": await self.secrets_manager.get_secret("n8n/webhook_secret", tenant_id)
        }
    
    async def get_payment_credentials(self, tenant_id: str, provider: str) -> Dict[str, str]:
        """Get payment provider credentials for tenant."""
        if provider == "mpesa":
            return {
                "consumer_key": await self.secrets_manager.get_secret("payments/mpesa/consumer_key", tenant_id),
                "consumer_secret": await self.secrets_manager.get_secret("payments/mpesa/consumer_secret", tenant_id)
            }
        elif provider == "paystack":
            return {
                "secret_key": await self.secrets_manager.get_secret("payments/paystack/secret_key", tenant_id)
            }
```

---

## 🔄 Rotation Procedures

### Automated Rotation Workflow

```bash
#!/bin/bash
# scripts/rotate-secrets.sh

ENVIRONMENT=${1:-staging}
SECRET_TYPE=${2:-all}

echo "Starting secret rotation for $ENVIRONMENT environment..."

case $SECRET_TYPE in
  "database")
    rotate_database_secrets
    ;;
  "llm")
    rotate_llm_api_keys
    ;;
  "payments")
    rotate_payment_credentials
    ;;
  "all")
    rotate_database_secrets
    rotate_llm_api_keys
    rotate_payment_credentials
    rotate_auth_secrets
    ;;
esac

echo "Secret rotation completed. Updating dependent services..."
kubectl rollout restart deployment/smeflow-api
kubectl rollout restart deployment/smeflow-n8n
```

### Manual Rotation Process

1. **Pre-Rotation Checklist**:
   - [ ] Backup current secrets
   - [ ] Verify dependent services
   - [ ] Schedule maintenance window
   - [ ] Notify operations team

2. **Rotation Steps**:
   ```bash
   # 1. Generate new secret
   NEW_SECRET=$(generate_secure_password 32)
   
   # 2. Store in vault with versioning
   vault kv put secret/smeflow/service/key \
     value="$NEW_SECRET" \
     previous_rotation="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
   
   # 3. Update application configuration
   kubectl create secret generic smeflow-secrets \
     --from-literal=service-key="$NEW_SECRET" \
     --dry-run=client -o yaml | kubectl apply -f -
   
   # 4. Rolling restart services
   kubectl rollout restart deployment/smeflow-api
   
   # 5. Verify functionality
   kubectl get pods -l app=smeflow-api
   curl -f https://api.smeflow.com/health
   ```

3. **Post-Rotation Verification**:
   - [ ] All services healthy
   - [ ] Authentication working
   - [ ] Integration tests passing
   - [ ] Monitoring alerts clear

---

## 🚨 Incident Response

### Secret Compromise Response

**Immediate Actions (0-15 minutes)**:
1. **Revoke Compromised Secret**:
   ```bash
   # Immediately disable the compromised key
   vault kv delete secret/smeflow/compromised/path
   
   # Block access in external services
   curl -X DELETE "https://api.openai.com/v1/api_keys/$COMPROMISED_KEY"
   ```

2. **Generate Emergency Replacement**:
   ```bash
   # Create new secret immediately
   EMERGENCY_SECRET=$(generate_secure_password 32)
   vault kv put secret/smeflow/service/key value="$EMERGENCY_SECRET"
   ```

3. **Update Critical Services**:
   ```bash
   # Emergency deployment with new secrets
   kubectl patch deployment smeflow-api -p \
     '{"spec":{"template":{"metadata":{"annotations":{"emergency-rotation":"'$(date)'"}}}}}'
   ```

**Investigation Phase (15-60 minutes)**:
- Audit logs analysis
- Scope of compromise assessment
- Affected tenant identification
- External service notification

**Recovery Phase (1-4 hours)**:
- Full secret rotation cycle
- Security posture review
- Incident documentation
- Process improvement recommendations

### Monitoring & Alerting

```yaml
# monitoring/secret-alerts.yaml
groups:
- name: secrets-management
  rules:
  - alert: SecretRotationOverdue
    expr: (time() - secret_last_rotation_timestamp) > (30 * 24 * 3600)
    for: 1h
    labels:
      severity: warning
    annotations:
      summary: "Secret rotation overdue for {{ $labels.secret_path }}"
      
  - alert: UnauthorizedSecretAccess
    expr: increase(vault_secret_access_denied_total[5m]) > 0
    for: 0m
    labels:
      severity: critical
    annotations:
      summary: "Unauthorized secret access attempt detected"
      
  - alert: SecretAccessAnomalous
    expr: rate(vault_secret_access_total[1h]) > (rate(vault_secret_access_total[24h]) * 3)
    for: 15m
    labels:
      severity: warning
    annotations:
      summary: "Anomalous secret access pattern detected"
```

---

## 📋 Compliance & Audit

### African Market Compliance

**CBN (Central Bank of Nigeria) Requirements**:
- Financial credentials stored within Nigerian jurisdiction
- Encryption at rest and in transit
- Access logging for regulatory reporting
- Data residency compliance for Nigerian tenants

**POPIA (South Africa) Requirements**:
- Personal information encryption
- Access control and audit trails
- Data subject rights compliance
- Cross-border transfer restrictions

**Implementation**:
```python
# Regional compliance enforcement
class ComplianceSecretsManager:
    def __init__(self, region: str):
        self.region = region
        self.vault_endpoint = self.get_regional_vault(region)
    
    def get_regional_vault(self, region: str) -> str:
        """Get region-specific Vault endpoint for compliance."""
        regional_vaults = {
            "NG": "https://vault-nigeria.smeflow.com",  # CBN compliance
            "ZA": "https://vault-southafrica.smeflow.com",  # POPIA compliance
            "KE": "https://vault-kenya.smeflow.com",
            "default": "https://vault-eu.smeflow.com"  # GDPR compliance
        }
        return regional_vaults.get(region, regional_vaults["default"])
```

### Audit Trail Requirements

**Logging Standards**:
```json
{
  "timestamp": "2025-10-03T23:18:01Z",
  "event_type": "secret_access",
  "tenant_id": "tenant_123",
  "user_id": "user_456",
  "secret_path": "payments/mpesa/consumer_key",
  "action": "read",
  "source_ip": "10.0.1.100",
  "user_agent": "smeflow-api/1.0",
  "success": true,
  "compliance_region": "NG",
  "audit_id": "audit_789"
}
```

**Retention Policies**:
- **Development**: 30 days
- **Staging**: 90 days
- **Production**: 7 years (compliance requirement)
- **Financial Secrets**: 10 years (regulatory requirement)

---

## 🛠️ Operational Procedures

### Daily Operations

**Health Checks**:
```bash
# Daily secret health verification
./scripts/check-secret-health.sh

# Verify Vault connectivity
vault status

# Check secret expiration warnings
vault kv list -format=json secret/smeflow/ | jq '.[] | select(.expires_at < now + 7*24*3600)'
```

**Monitoring Dashboard**:
- Secret rotation status
- Access pattern anomalies
- Compliance posture
- Regional distribution
- Cost tracking

### Weekly Maintenance

**Security Review**:
- [ ] Review access logs for anomalies
- [ ] Verify rotation schedules
- [ ] Update compliance documentation
- [ ] Test incident response procedures
- [ ] Validate backup and recovery

**Performance Optimization**:
- [ ] Cache hit rates for frequently accessed secrets
- [ ] Vault performance metrics
- [ ] Regional latency measurements
- [ ] Cost optimization opportunities

---

## 📚 Integration Examples

### n8N Connector Credentials

```python
# Example: Secure n8N credential management
async def setup_n8n_tenant_credentials(tenant_id: str, credentials: Dict[str, str]):
    """Securely store n8N credentials for tenant."""
    secrets_service = get_secrets_service()
    
    # Encrypt and store each credential
    for key, value in credentials.items():
        encrypted_value = encrypt_tenant_secret(value, tenant_id)
        await secrets_service.set_secret(
            path=f"n8n/{key}",
            value=encrypted_value,
            tenant_id=tenant_id
        )
    
    # Log for audit trail
    audit_log.info(
        "n8n_credentials_stored",
        tenant_id=tenant_id,
        credential_count=len(credentials),
        timestamp=datetime.utcnow()
    )

async def get_n8n_client_for_tenant(tenant_id: str) -> SMEFlowN8nClient:
    """Get configured n8N client with tenant-specific credentials."""
    secrets_service = get_secrets_service()
    
    api_key = await secrets_service.get_secret("n8n/api_key", tenant_id)
    base_url = await secrets_service.get_secret("n8n/base_url", tenant_id)
    
    config = N8nConfig(
        base_url=base_url,
        api_key=decrypt_tenant_secret(api_key, tenant_id)
    )
    
    return SMEFlowN8nClient(config=config)
```

### African Payment Provider Integration

```python
# Example: M-Pesa credential management with CBN compliance
class MPesaSecretsManager:
    def __init__(self, tenant_id: str):
        self.tenant_id = tenant_id
        self.secrets_service = get_secrets_service()
        self.compliance_region = self.get_tenant_region(tenant_id)
    
    async def get_mpesa_credentials(self) -> Dict[str, str]:
        """Get M-Pesa credentials with CBN compliance."""
        if self.compliance_region == "NG":
            # Ensure credentials are stored in Nigerian jurisdiction
            vault_region = "nigeria"
        else:
            vault_region = "default"
        
        consumer_key = await self.secrets_service.get_secret(
            "payments/mpesa/consumer_key", 
            self.tenant_id,
            region=vault_region
        )
        
        consumer_secret = await self.secrets_service.get_secret(
            "payments/mpesa/consumer_secret", 
            self.tenant_id,
            region=vault_region
        )
        
        # Log access for compliance audit
        await self.log_financial_credential_access("mpesa", "read")
        
        return {
            "consumer_key": consumer_key,
            "consumer_secret": consumer_secret
        }
```

---

## 🎯 Success Metrics

### Security KPIs
- **Zero** secrets in source code or logs
- **100%** of secrets encrypted at rest
- **<15 minutes** incident response time
- **30-day** maximum rotation cycle for critical secrets

### Compliance KPIs
- **100%** regional data residency compliance
- **7-year** audit trail retention
- **<24 hours** compliance reporting generation
- **Zero** cross-tenant secret access violations

### Operational KPIs
- **99.9%** secret service availability
- **<100ms** secret retrieval latency
- **Zero** manual secret management tasks
- **100%** automated rotation coverage

---

## 📖 References

### Documentation
- [HashiCorp Vault Best Practices](https://learn.hashicorp.com/vault)
- [Kubernetes Secrets Management](https://kubernetes.io/docs/concepts/configuration/secret/)
- [CBN Cybersecurity Guidelines](https://www.cbn.gov.ng/Out/2018/CCD/Cybersecurity%20Framework%20for%20Banks%20and%20Other%20Financial%20Institutions%20in%20Nigeria.pdf)
- [POPIA Compliance Guide](https://popia.co.za/)

### Tools & Libraries
- **HashiCorp Vault**: Production secret storage
- **Docker Secrets**: Staging environment
- **Kubernetes CSI**: Secret injection
- **python-dotenv**: Development environment
- **cryptography**: Python encryption library

---

*Last Updated: 2025-10-03*  
*Version: 1.0*  
*Owner: Security & Platform Operations Team*  
*Review Cycle: Quarterly*
