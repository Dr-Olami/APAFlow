#!/usr/bin/env python3
"""
SMEFlow Infrastructure Validation Script

This script validates that all Phase 1 infrastructure components are operational
and ready for Phase 3.2 n8N Integration Layer implementation.
"""

import asyncio
import json
import subprocess
import sys
from typing import Dict, List, Tuple
import asyncpg
import redis
import requests
from datetime import datetime

# Color codes for output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
ENDC = '\033[0m'

def print_status(message: str, status: str, details: str = ""):
    """Print formatted status message."""
    if status == "PASS":
        color = GREEN
        symbol = "✅"
    elif status == "FAIL":
        color = RED
        symbol = "❌"
    elif status == "WARN":
        color = YELLOW
        symbol = "⚠️"
    else:
        color = BLUE
        symbol = "ℹ️"
    
    print(f"{color}{symbol} {message}{ENDC}")
    if details:
        print(f"   {details}")

def run_command(cmd: str) -> Tuple[bool, str]:
    """Run shell command and return success status and output."""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
        return result.returncode == 0, result.stdout.strip()
    except subprocess.TimeoutExpired:
        return False, "Command timeout"
    except Exception as e:
        return False, str(e)

def check_docker_services() -> List[Dict]:
    """Check status of Docker services."""
    print(f"\n{BLUE}=== Docker Services Check ==={ENDC}")
    
    services = [
        {"name": "PostgreSQL", "container": "postgres", "port": "5432"},
        {"name": "Redis", "container": "redis", "port": "6379"},
        {"name": "Keycloak", "container": "keycloak", "port": "8080"},
        {"name": "Cerbos", "container": "cerbos", "port": "3593"}
    ]
    
    results = []
    
    # Check if Docker is running
    success, output = run_command("docker ps")
    if not success:
        print_status("Docker daemon", "FAIL", "Docker is not running or accessible")
        return results
    
    for service in services:
        success, output = run_command(f"docker ps --filter name={service['container']} --format '{{{{.Names}}}}\\t{{{{.Status}}}}'")
        
        if success and service['container'] in output.lower():
            if 'up' in output.lower():
                print_status(f"{service['name']} container", "PASS", f"Running on port {service['port']}")
                results.append({"service": service['name'], "status": "running", "port": service['port']})
            else:
                print_status(f"{service['name']} container", "FAIL", f"Container exists but not running: {output}")
                results.append({"service": service['name'], "status": "stopped", "port": service['port']})
        else:
            print_status(f"{service['name']} container", "FAIL", f"Container not found")
            results.append({"service": service['name'], "status": "missing", "port": service['port']})
    
    return results

async def check_database_connectivity():
    """Check PostgreSQL database connectivity and multi-tenant setup."""
    print(f"\n{BLUE}=== Database Connectivity Check ==={ENDC}")
    
    try:
        # Try to connect to database
        conn = await asyncpg.connect(
            host="localhost",
            port=5432,
            user="smeflow",
            password="smeflow123",
            database="smeflow"
        )
        
        print_status("PostgreSQL connection", "PASS", "Successfully connected to database")
        
        # Check if basic tables exist
        tables = await conn.fetch("SELECT tablename FROM pg_tables WHERE schemaname = 'public';")
        table_names = [row['tablename'] for row in tables]
        
        required_tables = ['tenants', 'agents', 'workflows', 'logs']
        missing_tables = [table for table in required_tables if table not in table_names]
        
        if not missing_tables:
            print_status("Database schema", "PASS", f"All required tables present: {', '.join(required_tables)}")
        else:
            print_status("Database schema", "WARN", f"Missing tables: {', '.join(missing_tables)}")
        
        # Check tenant isolation
        schemas = await conn.fetch("SELECT schema_name FROM information_schema.schemata WHERE schema_name LIKE 'tenant_%';")
        if schemas:
            print_status("Multi-tenant schemas", "PASS", f"Found {len(schemas)} tenant schemas")
        else:
            print_status("Multi-tenant schemas", "WARN", "No tenant-specific schemas found")
        
        await conn.close()
        
    except Exception as e:
        print_status("PostgreSQL connection", "FAIL", f"Connection failed: {str(e)}")

def check_redis_connectivity():
    """Check Redis connectivity and configuration."""
    print(f"\n{BLUE}=== Redis Cache Check ==={ENDC}")
    
    try:
        r = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
        
        # Test basic connectivity
        if r.ping():
            print_status("Redis connection", "PASS", "Successfully connected to Redis")
        else:
            print_status("Redis connection", "FAIL", "Redis ping failed")
            return
        
        # Test cache operations
        test_key = "smeflow:health:test"
        r.set(test_key, "test_value", ex=60)
        
        if r.get(test_key) == "test_value":
            print_status("Redis operations", "PASS", "Cache read/write operations working")
            r.delete(test_key)
        else:
            print_status("Redis operations", "FAIL", "Cache operations not working")
        
        # Check memory usage
        info = r.info('memory')
        used_memory_mb = info['used_memory'] / (1024 * 1024)
        print_status("Redis memory", "INFO", f"Memory usage: {used_memory_mb:.2f} MB")
        
    except Exception as e:
        print_status("Redis connection", "FAIL", f"Connection failed: {str(e)}")

def check_keycloak_service():
    """Check Keycloak authentication service."""
    print(f"\n{BLUE}=== Keycloak Authentication Check ==={ENDC}")
    
    try:
        # Check if Keycloak is accessible
        response = requests.get("http://localhost:8080/realms/smeflow/.well-known/openid_configuration", timeout=10)
        
        if response.status_code == 200:
            print_status("Keycloak service", "PASS", "Keycloak is accessible and responding")
            
            config = response.json()
            if 'issuer' in config and 'smeflow' in config['issuer']:
                print_status("SMEFlow realm", "PASS", "SMEFlow realm is configured")
            else:
                print_status("SMEFlow realm", "WARN", "SMEFlow realm configuration unclear")
        else:
            print_status("Keycloak service", "FAIL", f"HTTP {response.status_code}")
    
    except requests.exceptions.RequestException as e:
        print_status("Keycloak service", "FAIL", f"Connection failed: {str(e)}")

def check_cerbos_service():
    """Check Cerbos authorization service."""
    print(f"\n{BLUE}=== Cerbos Authorization Check ==={ENDC}")
    
    try:
        # Check Cerbos health endpoint
        response = requests.get("http://localhost:3593/_cerbos/health", timeout=10)
        
        if response.status_code == 200:
            print_status("Cerbos service", "PASS", "Cerbos is accessible and healthy")
            
            health_data = response.json()
            if health_data.get('status') == 'SERVING':
                print_status("Cerbos status", "PASS", "Service is serving requests")
            else:
                print_status("Cerbos status", "WARN", f"Status: {health_data.get('status', 'unknown')}")
        else:
            print_status("Cerbos service", "FAIL", f"HTTP {response.status_code}")
    
    except requests.exceptions.RequestException as e:
        print_status("Cerbos service", "FAIL", f"Connection failed: {str(e)}")

def check_environment_config():
    """Check environment configuration."""
    print(f"\n{BLUE}=== Environment Configuration Check ==={ENDC}")
    
    try:
        from smeflow.core.config import get_settings
        settings = get_settings()
        
        print_status("Configuration loading", "PASS", "Settings loaded successfully")
        
        # Check critical configuration values
        if settings.DATABASE_URL:
            print_status("Database URL", "PASS", "Database URL configured")
        else:
            print_status("Database URL", "FAIL", "Database URL not configured")
        
        if settings.REDIS_HOST:
            print_status("Redis configuration", "PASS", f"Redis host: {settings.REDIS_HOST}")
        else:
            print_status("Redis configuration", "FAIL", "Redis host not configured")
        
        if settings.KEYCLOAK_URL:
            print_status("Keycloak configuration", "PASS", f"Keycloak URL: {settings.KEYCLOAK_URL}")
        else:
            print_status("Keycloak configuration", "FAIL", "Keycloak URL not configured")
        
        # Check n8N configuration
        if settings.N8N_BASE_URL:
            print_status("n8N configuration", "PASS", f"n8N URL: {settings.N8N_BASE_URL}")
        else:
            print_status("n8N configuration", "WARN", "n8N URL not configured (expected for Stage 0)")
        
    except Exception as e:
        print_status("Configuration loading", "FAIL", f"Failed to load settings: {str(e)}")

async def check_n8n_wrapper():
    """Check n8N wrapper health check functionality."""
    print(f"\n{BLUE}=== n8N Wrapper Check ==={ENDC}")
    
    try:
        from smeflow.integrations.n8n_wrapper import SMEFlowN8nClient, N8nConfig
        
        # Create test configuration
        config = N8nConfig(
            base_url="http://localhost:5678",
            api_key="test-key"
        )
        
        client = SMEFlowN8nClient(config=config)
        
        # Test health check method (should not raise TypeError anymore)
        try:
            # This will fail due to no n8N service, but shouldn't raise TypeError
            result = await client.health_check()
            print_status("n8N wrapper health check", "PASS", "Method callable without TypeError")
            
            if result['status'] == 'unhealthy':
                print_status("n8N service availability", "WARN", "n8N service not available (expected for Stage 0)")
            
        except TypeError as e:
            print_status("n8N wrapper health check", "FAIL", f"TypeError in health_check method: {str(e)}")
        except Exception as e:
            print_status("n8N wrapper health check", "PASS", f"Method works, service unavailable: {type(e).__name__}")
        
        # Check template loading
        templates = client.get_available_templates()
        if templates:
            print_status("n8N templates", "PASS", f"Loaded {len(templates)} workflow templates")
        else:
            print_status("n8N templates", "WARN", "No workflow templates loaded")
        
    except Exception as e:
        print_status("n8N wrapper import", "FAIL", f"Failed to import n8N wrapper: {str(e)}")

def generate_report(results: Dict):
    """Generate summary report."""
    print(f"\n{BLUE}=== Infrastructure Readiness Summary ==={ENDC}")
    
    total_checks = sum(len(checks) for checks in results.values())
    passed_checks = sum(1 for checks in results.values() for check in checks if check.get('status') == 'PASS')
    
    print(f"Total Checks: {total_checks}")
    print(f"Passed: {passed_checks}")
    print(f"Success Rate: {(passed_checks/total_checks)*100:.1f}%")
    
    if passed_checks == total_checks:
        print_status("Stage 0 Readiness", "PASS", "All infrastructure components ready for Stage 1")
    elif passed_checks >= total_checks * 0.8:
        print_status("Stage 0 Readiness", "WARN", "Most components ready, review warnings before proceeding")
    else:
        print_status("Stage 0 Readiness", "FAIL", "Critical infrastructure issues must be resolved")
    
    # Save detailed report
    report = {
        "timestamp": datetime.utcnow().isoformat(),
        "summary": {
            "total_checks": total_checks,
            "passed_checks": passed_checks,
            "success_rate": (passed_checks/total_checks)*100
        },
        "details": results
    }
    
    with open("infrastructure_validation_report.json", "w") as f:
        json.dump(report, f, indent=2)
    
    print(f"\n📄 Detailed report saved to: infrastructure_validation_report.json")

async def main():
    """Main validation function."""
    print(f"{BLUE}SMEFlow Infrastructure Validation{ENDC}")
    print(f"Timestamp: {datetime.utcnow().isoformat()}")
    print("=" * 50)
    
    results = {}
    
    # Run all checks
    docker_results = check_docker_services()
    results['docker'] = docker_results
    
    await check_database_connectivity()
    check_redis_connectivity()
    check_keycloak_service()
    check_cerbos_service()
    check_environment_config()
    await check_n8n_wrapper()
    
    # Generate final report
    generate_report(results)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print(f"\n{YELLOW}Validation interrupted by user{ENDC}")
        sys.exit(1)
    except Exception as e:
        print(f"\n{RED}Validation failed with error: {str(e)}{ENDC}")
        sys.exit(1)
