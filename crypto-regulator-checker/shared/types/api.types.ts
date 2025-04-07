export interface UploadResponse {
    status: 'success' | 'error';
    message: string;
    documentId?: string;
    error?: string;
}

export interface AnalysisResponse {
    status: 'success' | 'error';
    message: string;
    results?: {
        complianceIssues: ComplianceIssue[];
        riskScore: number;
        recommendations: string[];
        regulatoryUpdates: RegulatoryUpdate[];
    };
    error?: string;
}

export interface ComplianceIssue {
    severity: 'high' | 'medium' | 'low';
    description: string;
    regulation: string;
    suggestion: string;
    context?: string;
}

export interface RegulatoryUpdate {
    date: string;
    region: string;
    description: string;
    impact: string;
    source: string;
}

export interface NotificationSettings {
    email: boolean;
    inApp: boolean;
    frequency: 'immediate' | 'daily' | 'weekly';
    types: ('compliance' | 'regulatory' | 'risk')[];
}

export interface UserPreferences {
    notifications: NotificationSettings;
    defaultRegions: string[];
    riskThreshold: number;
    language: string;
} 