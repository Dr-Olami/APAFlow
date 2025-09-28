class SMEFlowThemeProvider_Themes {
    constructor() {
        this.label = 'SMEFlow Theme Provider'
        this.name = 'smeflowThemeProvider'
        this.version = 1.0
        this.type = 'SMEFlowThemeProvider'
        this.icon = 'smeflow-theme.svg'
        this.category = 'SMEFlow Themes'
        this.description = 'Provides tenant-specific theming and branding for SMEFlow workflows with African market optimizations'
        this.baseClasses = [this.type]
        this.inputs = [
            {
                label: 'Tenant ID',
                name: 'tenantId',
                type: 'string',
                description: 'Unique identifier for the tenant'
            },
            {
                label: 'Theme Configuration ID',
                name: 'themeConfigId',
                type: 'string',
                optional: true,
                description: 'Specific theme configuration ID (uses active config if not provided)'
            },
            {
                label: 'Language Code',
                name: 'languageCode',
                type: 'options',
                options: [
                    { label: 'English', name: 'en' },
                    { label: 'Swahili', name: 'sw' },
                    { label: 'Hausa', name: 'ha' },
                    { label: 'Yoruba', name: 'yo' },
                    { label: 'Igbo', name: 'ig' },
                    { label: 'Amharic', name: 'am' },
                    { label: 'Arabic', name: 'ar' },
                    { label: 'French', name: 'fr' },
                    { label: 'Portuguese', name: 'pt' },
                    { label: 'Afrikaans', name: 'af' },
                    { label: 'Zulu', name: 'zu' },
                    { label: 'Xhosa', name: 'xh' }
                ],
                default: 'en',
                description: 'Language for UI localization'
            },
            {
                label: 'Region',
                name: 'region',
                type: 'options',
                options: [
                    { label: 'Nigeria', name: 'NG' },
                    { label: 'Kenya', name: 'KE' },
                    { label: 'South Africa', name: 'ZA' },
                    { label: 'Ghana', name: 'GH' },
                    { label: 'Egypt', name: 'EG' },
                    { label: 'Uganda', name: 'UG' },
                    { label: 'Tanzania', name: 'TZ' },
                    { label: 'Rwanda', name: 'RW' },
                    { label: 'Ethiopia', name: 'ET' }
                ],
                default: 'NG',
                description: 'Target region for cultural and regulatory adaptations'
            },
            {
                label: 'Enable Custom CSS',
                name: 'enableCustomCSS',
                type: 'boolean',
                default: true,
                description: 'Apply tenant-specific custom CSS overrides'
            },
            {
                label: 'Cache Duration (seconds)',
                name: 'cacheDuration',
                type: 'number',
                default: 3600,
                description: 'Theme cache duration in seconds'
            }
        ]
        this.outputs = [
            {
                label: 'Theme Configuration',
                name: 'themeConfig',
                baseClasses: ['object']
            },
            {
                label: 'CSS Variables',
                name: 'cssVariables',
                baseClasses: ['string']
            },
            {
                label: 'Localization Config',
                name: 'localizationConfig',
                baseClasses: ['object']
            }
        ]
    }

    async init(nodeData) {
        const tenantId = nodeData.inputs?.tenantId
        const themeConfigId = nodeData.inputs?.themeConfigId
        const languageCode = nodeData.inputs?.languageCode || 'en'
        const region = nodeData.inputs?.region || 'NG'
        const enableCustomCSS = nodeData.inputs?.enableCustomCSS ?? true
        const cacheDuration = nodeData.inputs?.cacheDuration || 3600

        try {
            // Get SMEFlow API base URL from environment
            const apiBaseUrl = process.env.SMEFLOW_API_URL || 'http://localhost:8000'
            
            // Fetch tenant branding configuration
            const brandingResponse = await this.fetchBrandingConfig(
                apiBaseUrl, 
                tenantId, 
                themeConfigId
            )
            
            if (!brandingResponse.success) {
                console.warn(`SMEFlow Theme Provider: ${brandingResponse.error}. Using default theme.`)
                return this.getDefaultTheme(tenantId, languageCode, region)
            }

            // Generate theme from branding configuration
            const themeResponse = await this.generateTheme(
                apiBaseUrl,
                tenantId,
                brandingResponse.data.id,
                cacheDuration,
                enableCustomCSS
            )

            if (!themeResponse.success) {
                console.warn(`SMEFlow Theme Provider: Failed to generate theme. Using default.`)
                return this.getDefaultTheme(tenantId, languageCode, region)
            }

            // Get localization configuration
            const localizationConfig = await this.getLocalizationConfig(
                apiBaseUrl,
                tenantId,
                region,
                languageCode
            )

            // Apply African market optimizations
            const optimizedTheme = this.applyAfricanMarketOptimizations(
                themeResponse.data,
                brandingResponse.data,
                region,
                languageCode
            )

            return {
                themeConfig: {
                    tenantId,
                    brandingId: brandingResponse.data.id,
                    colors: brandingResponse.data.colors,
                    typography: brandingResponse.data.typography,
                    layout: brandingResponse.data.layout,
                    region,
                    languageCode,
                    currencyCode: brandingResponse.data.currency_code,
                    generatedAt: new Date().toISOString(),
                    cacheKey: optimizedTheme.cache_key
                },
                cssVariables: optimizedTheme.css_variables + 
                    (enableCustomCSS && optimizedTheme.custom_css ? '\n' + optimizedTheme.custom_css : '') +
                    '\n' + optimizedTheme.component_styles,
                localizationConfig: localizationConfig.data || this.getDefaultLocalization(region, languageCode)
            }

        } catch (error) {
            console.error('SMEFlow Theme Provider Error:', error)
            return this.getDefaultTheme(tenantId, languageCode, region)
        }
    }

    async fetchBrandingConfig(
        apiBaseUrl, 
        tenantId, 
        themeConfigId
    ) {
        try {
            let url = `${apiBaseUrl}/api/branding/configurations`
            
            if (themeConfigId) {
                url += `/${themeConfigId}`
            } else {
                url += `?active_only=true`
            }

            const response = await fetch(url, {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json',
                    'X-Tenant-ID': tenantId
                }
            })

            if (!response.ok) {
                return { success: false, error: `HTTP ${response.status}: ${response.statusText}` }
            }

            const data = await response.json()
            
            // If fetching all configs, get the first active one
            if (Array.isArray(data) && data.length > 0) {
                return { success: true, data: data[0] }
            } else if (!Array.isArray(data)) {
                return { success: true, data }
            }

            return { success: false, error: 'No active branding configuration found' }

        } catch (error) {
            return { success: false, error: `Network error: ${error.message}` }
        }
    }

    async generateTheme(
        apiBaseUrl,
        tenantId,
        brandingId,
        cacheDuration,
        enableOptimization
    ) {
        try {
            const response = await fetch(`${apiBaseUrl}/api/branding/theme/generate`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-Tenant-ID': tenantId
                },
                body: JSON.stringify({
                    branding_id: brandingId,
                    cache_duration: cacheDuration,
                    enable_optimization: enableOptimization
                })
            })

            if (!response.ok) {
                return { success: false, error: `HTTP ${response.status}: ${response.statusText}` }
            }

            const data = await response.json()
            return { success: true, data }

        } catch (error) {
            return { success: false, error: `Theme generation error: ${error.message}` }
        }
    }

    async getLocalizationConfig(
        apiBaseUrl,
        tenantId,
        region,
        languageCode
    ) {
        try {
            const response = await fetch(`${apiBaseUrl}/api/branding/localization`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                    'X-Tenant-ID': tenantId
                },
                body: new URLSearchParams({
                    region,
                    languages: [languageCode, 'en'].join(','),
                    default_language: languageCode
                })
            })

            if (!response.ok) {
                return { success: false, error: `HTTP ${response.status}: ${response.statusText}` }
            }

            const data = await response.json()
            return { success: true, data }

        } catch (error) {
            return { success: false, error: `Localization error: ${error.message}` }
        }
    }

    applyAfricanMarketOptimizations(
        theme,
        branding,
        region,
        languageCode
    ) {
        // Add African market specific CSS optimizations
        const africanOptimizations = `
/* African Market Optimizations */
:root {
  --african-region: '${region}';
  --african-language: '${languageCode}';
  --mobile-first: true;
  --low-bandwidth-mode: ${region === 'NG' || region === 'KE' ? 'true' : 'false'};
}

/* Mobile-first responsive design for African markets */
@media (max-width: 480px) {
  .smeflow-content {
    padding: calc(var(--spacing-unit) / 2);
  }
  
  .btn-primary, .btn-secondary {
    min-height: 44px; /* Touch-friendly */
    font-size: var(--font-size-base);
  }
}

/* High contrast for bright sunlight conditions */
@media (prefers-contrast: high) or (max-resolution: 150dpi) {
  :root {
    --color-text-primary: #000000;
    --color-background-default: #ffffff;
    --color-primary-main: ${branding.colors.primary.dark || '#1565c0'};
  }
}

/* RTL support for Arabic regions */
${languageCode === 'ar' ? `
[dir="rtl"] {
  text-align: right;
}

[dir="rtl"] .smeflow-sidebar {
  left: auto;
  right: 0;
}

[dir="rtl"] .smeflow-content {
  margin-left: 0;
  margin-right: var(--sidebar-width);
}
` : ''}

/* Regional currency and number formatting */
.currency-${branding.currency_code?.toLowerCase() || 'ngn'} {
  font-family: var(--font-family-primary);
  font-weight: var(--font-weight-medium);
}

/* Cultural color preferences */
${this.getCulturalColorOverrides(region, branding.colors)}
`

        return {
            ...theme,
            css_variables: theme.css_variables + africanOptimizations,
            african_optimizations: true,
            region_specific: true
        }
    }

    getCulturalColorOverrides(region, colors) {
        const culturalOverrides = {
            'NG': `
/* Nigerian green-white theme preference */
.cultural-accent { color: #008751; }
.cultural-secondary { color: #ffffff; }
`,
            'KE': `
/* Kenyan red-black-green theme */
.cultural-accent { color: #bb0000; }
.cultural-secondary { color: #000000; }
`,
            'ZA': `
/* South African rainbow nation theme */
.cultural-accent { color: #007749; }
.cultural-secondary { color: #de3831; }
`,
            'EG': `
/* Egyptian red-white-black theme */
.cultural-accent { color: #ce1126; }
.cultural-secondary { color: #000000; }
`
        }

        return culturalOverrides[region] || culturalOverrides['NG']
    }

    getDefaultTheme(tenantId, languageCode, region) {
        return {
            themeConfig: {
                tenantId,
                brandingId: null,
                colors: {
                    primary: { main: '#1976d2', light: '#42a5f5', dark: '#1565c0', contrast: '#ffffff' },
                    secondary: { main: '#dc004e', light: '#ff5983', dark: '#9a0036', contrast: '#ffffff' },
                    background: { default: '#fafafa', paper: '#ffffff', elevated: '#ffffff' },
                    text: { primary: '#212121', secondary: '#757575', disabled: '#bdbdbd', hint: '#9e9e9e' },
                    status: { success: '#4caf50', warning: '#ff9800', error: '#f44336', info: '#2196f3' }
                },
                typography: {
                    font_family: {
                        primary: 'Inter, -apple-system, BlinkMacSystemFont, sans-serif',
                        secondary: 'Roboto, Arial, sans-serif',
                        monospace: 'Fira Code, Consolas, monospace'
                    },
                    font_sizes: {
                        xs: '0.75rem', sm: '0.875rem', base: '1rem', lg: '1.125rem',
                        xl: '1.25rem', '2xl': '1.5rem', '3xl': '1.875rem', '4xl': '2.25rem'
                    }
                },
                layout: {
                    header: { height: 64, position: 'fixed' },
                    sidebar: { width: 280, collapsible: true },
                    content: { max_width: 1200, padding: 24 },
                    border_radius: 8,
                    spacing_unit: 8
                },
                region,
                languageCode,
                currencyCode: this.getDefaultCurrency(region),
                isDefault: true
            },
            cssVariables: this.getDefaultCSS(region, languageCode),
            localizationConfig: this.getDefaultLocalization(region, languageCode)
        }
    }

    getDefaultCSS(region, languageCode) {
        return `
:root {
  --color-primary-main: #1976d2;
  --color-primary-light: #42a5f5;
  --color-primary-dark: #1565c0;
  --color-secondary-main: #dc004e;
  --color-background-default: #fafafa;
  --color-background-paper: #ffffff;
  --color-text-primary: #212121;
  --font-family-primary: Inter, -apple-system, BlinkMacSystemFont, sans-serif;
  --font-size-base: 1rem;
  --border-radius-base: 8px;
  --spacing-unit: 8px;
  --region: '${region}';
  --language: '${languageCode}';
  --currency: '${this.getDefaultCurrency(region)}';
}

/* Default SMEFlow styling */
body {
  font-family: var(--font-family-primary);
  color: var(--color-text-primary);
  background-color: var(--color-background-default);
}

.btn-primary {
  background-color: var(--color-primary-main);
  color: white;
  border: none;
  padding: 12px 24px;
  border-radius: var(--border-radius-base);
  cursor: pointer;
}
`
    }

    getDefaultLocalization(region, languageCode) {
        const currencies = {
            'NG': 'NGN', 'KE': 'KES', 'ZA': 'ZAR', 'GH': 'GHS', 'EG': 'EGP'
        }

        return {
            default_language: languageCode,
            supported_languages: [languageCode, 'en'],
            regional_formats: {
                currency: {
                    code: currencies[region] || 'NGN',
                    symbol: this.getCurrencySymbol(region),
                    position: 'before'
                },
                date_time: {
                    format: 'DD/MM/YYYY',
                    timezone: this.getTimezone(region)
                }
            },
            cultural_preferences: {
                greeting_style: 'warm',
                business_hours: { start: '08:00', end: '17:00' }
            }
        }
    }

    getDefaultCurrency(region) {
        const currencies = {
            'NG': 'NGN', 'KE': 'KES', 'ZA': 'ZAR', 'GH': 'GHS', 'EG': 'EGP'
        }
        return currencies[region] || 'NGN'
    }

    getCurrencySymbol(region) {
        const symbols = {
            'NG': '₦', 'KE': 'KSh', 'ZA': 'R', 'GH': '₵', 'EG': '£'
        }
        return symbols[region] || '₦'
    }

    getTimezone(region) {
        const timezones = {
            'NG': 'Africa/Lagos',
            'KE': 'Africa/Nairobi', 
            'ZA': 'Africa/Johannesburg',
            'GH': 'Africa/Accra',
            'EG': 'Africa/Cairo'
        }
        return timezones[region] || 'Africa/Lagos'
    }
}

module.exports = { nodeClass: SMEFlowThemeProvider_Themes }
