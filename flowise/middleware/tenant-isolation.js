/**
 * SMEFlow Multi-tenant Isolation Middleware for Flowise
 * 
 * Provides database-level tenant isolation and workspace separation
 * for African market SME automation workflows.
 */

const { v4: uuidv4, validate: uuidValidate } = require('uuid');

class TenantIsolationMiddleware {
    constructor(config = {}) {
        this.config = {
            tenantHeader: 'X-Tenant-ID',
            requireTenantId: true,
            defaultSchema: 'public',
            ...config
        };
    }

    /**
     * Express middleware for tenant isolation
     */
    middleware() {
        return (req, res, next) => {
            try {
                // Extract tenant ID from header
                const tenantId = req.headers[this.config.tenantHeader.toLowerCase()];
                
                if (!tenantId && this.config.requireTenantId) {
                    return res.status(400).json({
                        error: 'Tenant ID required',
                        message: `Header ${this.config.tenantHeader} is required for multi-tenant access`
                    });
                }

                if (tenantId && !uuidValidate(tenantId)) {
                    return res.status(400).json({
                        error: 'Invalid tenant ID format',
                        message: 'Tenant ID must be a valid UUID'
                    });
                }

                // Add tenant context to request
                req.tenant = {
                    id: tenantId,
                    schema: tenantId ? `tenant_${tenantId.replace(/-/g, '_')}` : this.config.defaultSchema,
                    isolated: !!tenantId
                };

                // Add tenant-aware database connection
                req.getTenantDb = () => {
                    return this.createTenantConnection(req.tenant);
                };

                next();
            } catch (error) {
                console.error('Tenant isolation middleware error:', error);
                res.status(500).json({
                    error: 'Tenant isolation failed',
                    message: error.message
                });
            }
        };
    }

    /**
     * Create tenant-specific database connection
     */
    createTenantConnection(tenant) {
        // This would integrate with Flowise's database connection pool
        // For now, return tenant context for query modification
        return {
            tenant: tenant,
            query: (sql, params) => {
                // Modify queries to include tenant isolation
                const tenantAwareQuery = this.addTenantFilter(sql, tenant.id);
                return this.executeQuery(tenantAwareQuery, params);
            }
        };
    }

    /**
     * Add tenant filter to SQL queries
     */
    addTenantFilter(sql, tenantId) {
        if (!tenantId) return sql;
        
        // Simple tenant filter injection
        // In production, use proper query builders with parameterized queries
        const lowerSql = sql.toLowerCase();
        
        if (lowerSql.includes('where')) {
            return sql.replace(/where/i, `WHERE tenant_id = '${tenantId}' AND`);
        } else if (lowerSql.includes('select')) {
            const fromIndex = lowerSql.indexOf('from');
            if (fromIndex > -1) {
                return sql.slice(0, fromIndex) + 
                       sql.slice(fromIndex) + 
                       ` WHERE tenant_id = '${tenantId}'`;
            }
        }
        
        return sql;
    }

    /**
     * Execute tenant-aware query (placeholder)
     */
    async executeQuery(sql, params) {
        // This would integrate with Flowise's actual database layer
        console.log('Executing tenant-aware query:', sql, params);
        return { success: true, query: sql, params };
    }

    /**
     * Validate tenant access permissions
     */
    async validateTenantAccess(tenantId, resource, action = 'read') {
        try {
            // Integration with SMEFlow API for tenant validation
            const response = await fetch(`http://smeflow:8000/api/v1/tenants/${tenantId}/validate`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-Tenant-ID': tenantId
                },
                body: JSON.stringify({ resource, action })
            });

            if (!response.ok) {
                throw new Error(`Tenant validation failed: ${response.statusText}`);
            }

            const result = await response.json();
            return result.valid === true;
        } catch (error) {
            console.error('Tenant access validation error:', error);
            return false;
        }
    }

    /**
     * Get tenant-specific configuration
     */
    async getTenantConfig(tenantId) {
        try {
            const response = await fetch(`http://smeflow:8000/api/v1/tenants/${tenantId}`, {
                headers: { 'X-Tenant-ID': tenantId }
            });

            if (!response.ok) {
                throw new Error(`Failed to fetch tenant config: ${response.statusText}`);
            }

            const tenant = await response.json();
            
            return {
                id: tenant.id,
                name: tenant.name,
                region: tenant.region || 'africa-west',
                currency: tenant.currency || 'NGN',
                timezone: tenant.timezone || 'Africa/Lagos',
                languages: tenant.languages || ['en', 'ha'],
                subscription_tier: tenant.subscription_tier || 'free',
                limits: tenant.limits || {
                    workflows_per_month: 100,
                    agents_per_tenant: 10,
                    api_calls_per_day: 1000
                }
            };
        } catch (error) {
            console.error('Error fetching tenant config:', error);
            return null;
        }
    }

    /**
     * African market-specific tenant setup
     */
    setupAfricanMarketTenant(tenantConfig) {
        const africanDefaults = {
            currencies: ['NGN', 'KES', 'ZAR', 'GHS', 'UGX', 'TZS', 'RWF', 'ETB'],
            languages: ['en', 'ha', 'yo', 'ig', 'sw', 'am', 'fr', 'ar'],
            timezones: [
                'Africa/Lagos',    // Nigeria
                'Africa/Nairobi',  // Kenya
                'Africa/Johannesburg', // South Africa
                'Africa/Accra',    // Ghana
                'Africa/Kampala',  // Uganda
                'Africa/Dar_es_Salaam', // Tanzania
                'Africa/Kigali',   // Rwanda
                'Africa/Addis_Ababa' // Ethiopia
            ],
            phoneFormats: {
                'NGN': '+234',
                'KES': '+254', 
                'ZAR': '+27',
                'GHS': '+233',
                'UGX': '+256',
                'TZS': '+255',
                'RWF': '+250',
                'ETB': '+251'
            },
            businessHours: {
                start: '08:00',
                end: '18:00',
                workdays: ['monday', 'tuesday', 'wednesday', 'thursday', 'friday']
            }
        };

        return {
            ...tenantConfig,
            africanMarket: africanDefaults,
            localization: {
                currency: tenantConfig.currency || 'NGN',
                language: tenantConfig.language || 'en',
                timezone: tenantConfig.timezone || 'Africa/Lagos',
                phoneFormat: africanDefaults.phoneFormats[tenantConfig.currency] || '+234'
            }
        };
    }
}

module.exports = TenantIsolationMiddleware;
