/**
 * SMEFlow Flowise Startup Configuration
 * 
 * Initializes multi-tenant support and African market optimizations
 * for Flowise integration with SMEFlow platform.
 */

const TenantIsolationMiddleware = require('../middleware/tenant-isolation');
const config = require('./flowise-config.json');

class SMEFlowFlowiseStartup {
    constructor() {
        this.config = config;
        this.tenantMiddleware = new TenantIsolationMiddleware(config.multiTenant);
    }

    /**
     * Initialize SMEFlow-specific Flowise configuration
     */
    async initialize(app) {
        console.log('🚀 Initializing SMEFlow Flowise Integration...');

        // Add tenant isolation middleware
        if (this.config.multiTenant.enabled) {
            app.use(this.tenantMiddleware.middleware());
            console.log('✅ Multi-tenant isolation enabled');
        }

        // Setup African market defaults
        this.setupAfricanMarketDefaults();

        // Configure SMEFlow API integration
        await this.configureSMEFlowAPI();

        // Setup custom error handling
        this.setupErrorHandling(app);

        console.log('✅ SMEFlow Flowise Integration initialized successfully');
    }

    /**
     * Setup African market-specific defaults
     */
    setupAfricanMarketDefaults() {
        global.SMEFLOW_AFRICAN_MARKET = {
            defaultRegion: this.config.africanMarket.defaultRegion,
            supportedCurrencies: this.config.africanMarket.supportedCurrencies,
            supportedLanguages: this.config.africanMarket.supportedLanguages,
            defaultTimezone: this.config.africanMarket.defaultTimezone,
            phoneFormats: this.config.africanMarket.phoneFormats
        };

        console.log('✅ African market defaults configured');
    }

    /**
     * Configure SMEFlow API integration
     */
    async configureSMEFlowAPI() {
        const apiConfig = this.config.smeflowIntegration;
        
        global.SMEFLOW_API = {
            baseUrl: apiConfig.apiUrl,
            version: apiConfig.apiVersion,
            timeout: apiConfig.timeout,
            retries: apiConfig.retries,
            endpoints: apiConfig.endpoints
        };

        // Test API connectivity
        try {
            const response = await fetch(`${apiConfig.apiUrl}/api/v1/health`, {
                timeout: 5000
            });
            
            if (response.ok) {
                console.log('✅ SMEFlow API connectivity verified');
            } else {
                console.warn('⚠️ SMEFlow API health check failed, but continuing...');
            }
        } catch (error) {
            console.warn('⚠️ SMEFlow API not available during startup:', error.message);
        }
    }

    /**
     * Setup custom error handling for SMEFlow integration
     */
    setupErrorHandling(app) {
        app.use((error, req, res, next) => {
            // Log tenant-specific errors
            if (req.tenant) {
                console.error(`[Tenant: ${req.tenant.id}] Error:`, error);
            }

            // Handle SMEFlow-specific errors
            if (error.message.includes('SMEFlow')) {
                return res.status(500).json({
                    error: 'SMEFlow Integration Error',
                    message: error.message,
                    tenant_id: req.tenant?.id,
                    timestamp: new Date().toISOString()
                });
            }

            next(error);
        });

        console.log('✅ Custom error handling configured');
    }

    /**
     * Validate tenant configuration
     */
    async validateTenantConfig(tenantId) {
        try {
            const tenantConfig = await this.tenantMiddleware.getTenantConfig(tenantId);
            
            if (!tenantConfig) {
                throw new Error(`Tenant ${tenantId} not found`);
            }

            // Validate African market configuration
            const africanConfig = this.tenantMiddleware.setupAfricanMarketTenant(tenantConfig);
            
            return {
                valid: true,
                tenant: africanConfig,
                message: 'Tenant configuration valid'
            };
        } catch (error) {
            return {
                valid: false,
                error: error.message,
                message: 'Tenant configuration validation failed'
            };
        }
    }
}

module.exports = SMEFlowFlowiseStartup;
