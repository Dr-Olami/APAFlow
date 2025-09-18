# SMEFlow White-Label UI System

## Overview

The SMEFlow White-Label UI System enables complete customization of the platform interface for each tenant, providing a branded experience that aligns with their business identity. This system supports multi-tenant branding, African market localization, and seamless integration with the core SMEFlow platform.

## Architecture Overview

### Multi-Tenant Branding Stack
```
Frontend Layer:
├── React-based Flowise UI (customizable)
├── Dynamic Theme Provider (tenant-aware)
├── Asset Management System (CDN-hosted)
├── Responsive Design Framework
└── Progressive Web App (PWA) capabilities

Backend Services:
├── Branding Configuration API
├── Asset Upload & Processing Service
├── Theme Generation Engine
├── Custom Domain Management
└── Template Rendering Service

Data Layer:
├── Tenant Branding Database
├── Asset Storage (S3-compatible)
├── Theme Cache (Redis)
├── CDN Distribution
└── Backup & Versioning
```

## Branding Components

### 1. Visual Identity System

#### 1.1 Logo Management
```typescript
interface LogoConfiguration {
  primary: {
    url: string;           // Main logo URL
    width: number;         // Preferred width in pixels
    height: number;        // Preferred height in pixels
    alt_text: string;      // Accessibility text
  };
  secondary?: {
    url: string;           // Alternative logo (light/dark)
    width: number;
    height: number;
    alt_text: string;
  };
  favicon: {
    url: string;           // Favicon URL (32x32, 16x16)
    type: 'ico' | 'png';   // File format
  };
  loading_logo?: {
    url: string;           // Loading screen logo
    animation?: 'spin' | 'pulse' | 'none';
  };
}
```

#### 1.2 Color Palette System
```typescript
interface ColorPalette {
  primary: {
    main: string;          // Primary brand color (#hex)
    light: string;         // Lighter variant
    dark: string;          // Darker variant
    contrast: string;      // Contrasting text color
  };
  secondary: {
    main: string;          // Secondary/accent color
    light: string;
    dark: string;
    contrast: string;
  };
  background: {
    default: string;       // Main background
    paper: string;         // Card/modal backgrounds
    elevated: string;      // Elevated surfaces
  };
  text: {
    primary: string;       // Main text color
    secondary: string;     // Secondary text
    disabled: string;      // Disabled text
    hint: string;          // Placeholder text
  };
  status: {
    success: string;       // Success states
    warning: string;       // Warning states
    error: string;         // Error states
    info: string;          // Info states
  };
}
```

#### 1.3 Typography System
```typescript
interface TypographyConfiguration {
  fontFamily: {
    primary: string;       // Main font family
    secondary?: string;    // Alternative font
    monospace: string;     // Code/monospace font
  };
  fontSizes: {
    xs: string;            // Extra small (12px)
    sm: string;            // Small (14px)
    base: string;          // Base (16px)
    lg: string;            // Large (18px)
    xl: string;            // Extra large (20px)
    '2xl': string;         // 2X large (24px)
    '3xl': string;         // 3X large (30px)
    '4xl': string;         // 4X large (36px)
  };
  fontWeights: {
    light: number;         // 300
    normal: number;        // 400
    medium: number;        // 500
    semibold: number;      // 600
    bold: number;          // 700
  };
  lineHeights: {
    tight: number;         // 1.25
    normal: number;        // 1.5
    relaxed: number;       // 1.75
  };
}
```

### 2. Layout Customization

#### 2.1 Dashboard Layout Options
```typescript
interface DashboardLayout {
  header: {
    height: number;        // Header height in pixels
    position: 'fixed' | 'static';
    showLogo: boolean;
    showSearch: boolean;
    showNotifications: boolean;
    showUserMenu: boolean;
    customActions?: CustomAction[];
  };
  sidebar: {
    width: number;         // Sidebar width
    collapsible: boolean;
    defaultCollapsed: boolean;
    position: 'left' | 'right';
    showIcons: boolean;
    customMenuItems?: MenuItem[];
  };
  content: {
    maxWidth?: number;     // Content max width
    padding: number;       // Content padding
    backgroundColor?: string;
  };
  footer: {
    show: boolean;
    height?: number;
    content?: string;
    links?: FooterLink[];
  };
}
```

#### 2.2 Navigation Customization
```typescript
interface NavigationConfig {
  mainMenu: MenuItem[];
  quickActions: QuickAction[];
  userMenu: UserMenuItem[];
  breadcrumbs: {
    show: boolean;
    separator: string;
    maxItems: number;
  };
}

interface MenuItem {
  id: string;
  label: string;
  icon?: string;
  url?: string;
  children?: MenuItem[];
  permissions?: string[];
  badge?: {
    text: string;
    color: string;
  };
}
```

### 3. Component Theming

#### 3.1 Button Styles
```css
/* Dynamic button theming */
.btn-primary {
  background-color: var(--color-primary-main);
  border-color: var(--color-primary-main);
  color: var(--color-primary-contrast);
}

.btn-primary:hover {
  background-color: var(--color-primary-dark);
  border-color: var(--color-primary-dark);
}

.btn-secondary {
  background-color: var(--color-secondary-main);
  border-color: var(--color-secondary-main);
  color: var(--color-secondary-contrast);
}
```

#### 3.2 Form Components
```typescript
interface FormTheme {
  inputStyles: {
    borderRadius: number;
    borderWidth: number;
    borderColor: string;
    focusColor: string;
    backgroundColor: string;
    textColor: string;
    placeholderColor: string;
  };
  labelStyles: {
    fontSize: string;
    fontWeight: number;
    color: string;
    marginBottom: number;
  };
  errorStyles: {
    color: string;
    fontSize: string;
    marginTop: number;
  };
}
```

## Flowise Integration

### 1. Workflow Builder Customization

#### 1.1 Node Styling
```typescript
interface NodeTheme {
  defaultNode: {
    backgroundColor: string;
    borderColor: string;
    textColor: string;
    borderRadius: number;
    shadowColor: string;
  };
  selectedNode: {
    borderColor: string;
    shadowColor: string;
    borderWidth: number;
  };
  nodeCategories: {
    [category: string]: {
      backgroundColor: string;
      iconColor: string;
      borderColor: string;
    };
  };
}
```

#### 1.2 Canvas Customization
```typescript
interface CanvasTheme {
  backgroundColor: string;
  gridColor: string;
  gridSize: number;
  connectionLineColor: string;
  connectionLineWidth: number;
  selectionBoxColor: string;
  zoomControls: {
    backgroundColor: string;
    iconColor: string;
    borderColor: string;
  };
}
```

### 2. Custom Node Categories

#### 2.1 SMEFlow Agent Nodes
```typescript
const smeflowNodeCategories = {
  'SMEFlow Agents': {
    backgroundColor: '#e3f2fd',
    iconColor: '#1976d2',
    borderColor: '#90caf9',
    nodes: [
      'Automator Agent',
      'Mentor Agent',
      'Supervisor Agent'
    ]
  },
  'African Integrations': {
    backgroundColor: '#fff3e0',
    iconColor: '#f57c00',
    borderColor: '#ffcc02',
    nodes: [
      'M-Pesa Payment',
      'Paystack Gateway',
      'WhatsApp Business',
      'Jumia API'
    ]
  },
  'Compliance Tools': {
    backgroundColor: '#f3e5f5',
    iconColor: '#7b1fa2',
    borderColor: '#ce93d8',
    nodes: [
      'GDPR Compliance',
      'POPIA Validator',
      'CBN Reporter',
      'Audit Logger'
    ]
  }
};
```

## Localization System

### 1. Multi-Language Support

#### 1.1 Language Configuration
```typescript
interface LocalizationConfig {
  defaultLanguage: string;
  supportedLanguages: Language[];
  fallbackLanguage: string;
  rtlLanguages: string[];
  dateFormats: {
    [languageCode: string]: string;
  };
  numberFormats: {
    [languageCode: string]: Intl.NumberFormatOptions;
  };
  currencyFormats: {
    [currencyCode: string]: Intl.NumberFormatOptions;
  };
}

interface Language {
  code: string;           // ISO 639-1 code (e.g., 'en', 'sw')
  name: string;           // Language name in English
  nativeName: string;     // Language name in native script
  flag: string;           // Flag emoji or icon
  rtl: boolean;           // Right-to-left text direction
  region: string[];       // Applicable regions/countries
}
```

#### 1.2 African Language Support
```typescript
const africanLanguages: Language[] = [
  {
    code: 'en',
    name: 'English',
    nativeName: 'English',
    flag: '🇬🇧',
    rtl: false,
    region: ['NG', 'KE', 'ZA', 'GH', 'UG', 'TZ', 'RW', 'ET']
  },
  {
    code: 'sw',
    name: 'Swahili',
    nativeName: 'Kiswahili',
    flag: '🇰🇪',
    rtl: false,
    region: ['KE', 'TZ', 'UG', 'RW', 'CD']
  },
  {
    code: 'ha',
    name: 'Hausa',
    nativeName: 'Harshen Hausa',
    flag: '🇳🇬',
    rtl: false,
    region: ['NG', 'NE', 'GH', 'CM']
  },
  {
    code: 'yo',
    name: 'Yoruba',
    nativeName: 'Èdè Yorùbá',
    flag: '🇳🇬',
    rtl: false,
    region: ['NG', 'BJ', 'TG']
  },
  {
    code: 'ig',
    name: 'Igbo',
    nativeName: 'Asụsụ Igbo',
    flag: '🇳🇬',
    rtl: false,
    region: ['NG']
  },
  {
    code: 'am',
    name: 'Amharic',
    nativeName: 'አማርኛ',
    flag: '🇪🇹',
    rtl: false,
    region: ['ET']
  },
  {
    code: 'ar',
    name: 'Arabic',
    nativeName: 'العربية',
    flag: '🇪🇬',
    rtl: true,
    region: ['EG', 'MA', 'TN', 'DZ', 'LY', 'SD']
  },
  {
    code: 'fr',
    name: 'French',
    nativeName: 'Français',
    flag: '🇫🇷',
    rtl: false,
    region: ['SN', 'CI', 'BF', 'ML', 'NE', 'TD', 'CM', 'GA', 'CG', 'CD', 'CF', 'DJ', 'MG']
  },
  {
    code: 'pt',
    name: 'Portuguese',
    nativeName: 'Português',
    flag: '🇵🇹',
    rtl: false,
    region: ['AO', 'MZ', 'GW', 'ST', 'CV']
  },
  {
    code: 'af',
    name: 'Afrikaans',
    nativeName: 'Afrikaans',
    flag: '🇿🇦',
    rtl: false,
    region: ['ZA', 'NA']
  }
];
```

### 2. Cultural Adaptations

#### 2.1 Regional Formatting
```typescript
interface RegionalFormat {
  currency: {
    code: string;           // ISO 4217 code (NGN, KES, ZAR)
    symbol: string;         // Currency symbol (₦, KSh, R)
    position: 'before' | 'after';
    decimals: number;
    thousandsSeparator: string;
    decimalSeparator: string;
  };
  dateTime: {
    dateFormat: string;     // DD/MM/YYYY or MM/DD/YYYY
    timeFormat: '12h' | '24h';
    firstDayOfWeek: 0 | 1;  // 0 = Sunday, 1 = Monday
    timezone: string;       // Africa/Lagos, Africa/Nairobi
  };
  address: {
    format: string[];       // Order of address components
    postalCodeLabel: string;
    stateLabel: string;
    required: string[];     // Required fields
  };
  phone: {
    countryCode: string;    // +234, +254, +27
    format: string;         // (XXX) XXX-XXXX
    nationalPrefix: string; // 0
  };
}
```

## Implementation Architecture

### 1. Theme Engine

#### 1.1 Dynamic Theme Generation
```typescript
class ThemeEngine {
  private cache: Map<string, CompiledTheme> = new Map();
  
  async generateTheme(tenantId: string, config: BrandingConfig): Promise<CompiledTheme> {
    // Check cache first
    const cacheKey = `${tenantId}-${config.version}`;
    if (this.cache.has(cacheKey)) {
      return this.cache.get(cacheKey)!;
    }
    
    // Generate CSS variables
    const cssVariables = this.generateCSSVariables(config);
    
    // Compile theme assets
    const compiledTheme = {
      cssVariables,
      customCSS: config.customCSS,
      assets: await this.processAssets(config.assets),
      fonts: await this.loadFonts(config.typography),
      components: this.generateComponentStyles(config)
    };
    
    // Cache the compiled theme
    this.cache.set(cacheKey, compiledTheme);
    
    return compiledTheme;
  }
  
  private generateCSSVariables(config: BrandingConfig): string {
    return `
      :root {
        --color-primary-main: ${config.colors.primary.main};
        --color-primary-light: ${config.colors.primary.light};
        --color-primary-dark: ${config.colors.primary.dark};
        --color-secondary-main: ${config.colors.secondary.main};
        --font-family-primary: ${config.typography.fontFamily.primary};
        --font-size-base: ${config.typography.fontSizes.base};
        --border-radius-base: ${config.layout.borderRadius}px;
        --spacing-unit: ${config.layout.spacingUnit}px;
      }
    `;
  }
}
```

#### 1.2 Asset Processing Pipeline
```typescript
class AssetProcessor {
  async processLogo(file: File, tenant: string): Promise<ProcessedAsset> {
    // Validate file type and size
    this.validateAsset(file, {
      maxSize: 2 * 1024 * 1024, // 2MB
      allowedTypes: ['image/png', 'image/jpeg', 'image/svg+xml']
    });
    
    // Generate multiple sizes
    const sizes = [32, 64, 128, 256, 512];
    const variants = await Promise.all(
      sizes.map(size => this.resizeImage(file, size))
    );
    
    // Upload to CDN
    const urls = await this.uploadToCDN(variants, tenant);
    
    // Generate optimized formats (WebP, AVIF)
    const optimizedFormats = await this.generateOptimizedFormats(file);
    
    return {
      original: urls.original,
      variants: urls.variants,
      optimized: optimizedFormats,
      metadata: {
        originalSize: file.size,
        dimensions: await this.getImageDimensions(file),
        format: file.type
      }
    };
  }
}
```

### 2. Custom Domain Management

#### 2.1 Domain Configuration
```typescript
interface CustomDomainConfig {
  domain: string;           // custom.domain.com
  subdomain?: string;       // app.custom.domain.com
  sslCertificate: {
    provider: 'letsencrypt' | 'custom';
    autoRenew: boolean;
    certificateChain?: string;
    privateKey?: string;
  };
  dnsRecords: DNSRecord[];
  verification: {
    method: 'dns' | 'file';
    token: string;
    verified: boolean;
    verifiedAt?: Date;
  };
}

class CustomDomainService {
  async setupCustomDomain(tenantId: string, config: CustomDomainConfig): Promise<void> {
    // Validate domain ownership
    await this.verifyDomainOwnership(config);
    
    // Configure SSL certificate
    await this.setupSSLCertificate(config);
    
    // Update CDN configuration
    await this.updateCDNConfig(tenantId, config.domain);
    
    // Configure reverse proxy
    await this.configureReverseProxy(tenantId, config);
    
    // Update tenant configuration
    await this.updateTenantDomain(tenantId, config.domain);
  }
}
```

### 3. Performance Optimization

#### 3.1 Asset Optimization
```typescript
interface AssetOptimization {
  images: {
    formats: ['webp', 'avif', 'jpeg'];
    quality: number;
    progressive: boolean;
    responsive: boolean;
  };
  css: {
    minification: boolean;
    purgeUnused: boolean;
    criticalCSS: boolean;
  };
  fonts: {
    preload: boolean;
    fontDisplay: 'swap' | 'fallback' | 'optional';
    subset: boolean;
  };
  caching: {
    staticAssets: number;    // Cache duration in seconds
    dynamicContent: number;
    cdnTTL: number;
  };
}
```

#### 3.2 Progressive Loading
```typescript
class ProgressiveLoader {
  async loadTenantTheme(tenantId: string): Promise<void> {
    // Load critical CSS first
    await this.loadCriticalCSS(tenantId);
    
    // Load fonts asynchronously
    this.loadFonts(tenantId);
    
    // Load remaining assets
    this.loadSecondaryAssets(tenantId);
    
    // Apply theme when ready
    this.applyTheme(tenantId);
  }
  
  private async loadCriticalCSS(tenantId: string): Promise<void> {
    const criticalCSS = await this.getCriticalCSS(tenantId);
    const style = document.createElement('style');
    style.textContent = criticalCSS;
    document.head.appendChild(style);
  }
}
```

## Security Considerations

### 1. Asset Security
```typescript
interface AssetSecurity {
  upload: {
    maxFileSize: number;
    allowedTypes: string[];
    virusScanning: boolean;
    contentValidation: boolean;
  };
  storage: {
    encryption: boolean;
    accessControl: 'private' | 'public';
    signedUrls: boolean;
    expirationTime: number;
  };
  delivery: {
    hotlinkProtection: boolean;
    referrerPolicy: string;
    corsPolicy: string[];
  };
}
```

### 2. Content Security Policy
```typescript
const cspPolicy = {
  'default-src': ["'self'"],
  'style-src': ["'self'", "'unsafe-inline'", 'fonts.googleapis.com'],
  'font-src': ["'self'", 'fonts.gstatic.com'],
  'img-src': ["'self'", 'data:', '*.smeflow.com', 'cdn.smeflow.com'],
  'script-src': ["'self'", "'unsafe-eval'"],
  'connect-src': ["'self'", 'api.smeflow.com'],
  'frame-ancestors': ["'none'"],
  'base-uri': ["'self'"],
  'form-action': ["'self'"]
};
```

## Testing & Quality Assurance

### 1. Visual Regression Testing
```typescript
interface VisualTest {
  component: string;
  variants: string[];
  viewports: Viewport[];
  themes: string[];
  browsers: Browser[];
}

class VisualRegressionTester {
  async testThemeVariants(tenantId: string): Promise<TestResults> {
    const themes = await this.getTenantThemes(tenantId);
    const results: TestResults = {};
    
    for (const theme of themes) {
      results[theme.id] = await this.runVisualTests(theme);
    }
    
    return results;
  }
}
```

### 2. Accessibility Testing
```typescript
interface AccessibilityChecks {
  colorContrast: boolean;
  keyboardNavigation: boolean;
  screenReaderCompatibility: boolean;
  focusManagement: boolean;
  semanticHTML: boolean;
}
```

## Monitoring & Analytics

### 1. Theme Performance Metrics
```typescript
interface ThemeMetrics {
  loadTime: number;
  assetSizes: {
    css: number;
    images: number;
    fonts: number;
  };
  cacheHitRate: number;
  userSatisfaction: number;
  conversionImpact: number;
}
```

### 2. Usage Analytics
```typescript
interface ThemeAnalytics {
  popularColors: ColorUsage[];
  fontPreferences: FontUsage[];
  layoutChoices: LayoutUsage[];
  customizationRate: number;
  completionRate: number;
}
```

This white-label UI system provides SME tenants with complete branding control while maintaining performance, security, and accessibility standards across the SMEFlow platform.
