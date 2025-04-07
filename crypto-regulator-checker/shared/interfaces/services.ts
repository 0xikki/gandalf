/// <reference types="node" />
import { ComplianceIssue, RegulatoryUpdate } from '../types/api.types';

export interface IDocumentProcessor {
    processDocument(file: Buffer, filename: string): Promise<{
        text: string;
        metadata: Record<string, any>;
    }>;
    validateDocument(file: Buffer, filename: string): Promise<boolean>;
    extractMetadata(file: Buffer): Promise<Record<string, any>>;
}

export interface IEmbeddingService {
    generateEmbeddings(text: string): Promise<number[]>;
    batchGenerateEmbeddings(texts: string[]): Promise<number[][]>;
    getDimensions(): number;
}

export interface IVectorStore {
    addDocument(
        id: string,
        vector: number[],
        metadata: Record<string, any>
    ): Promise<void>;
    searchSimilar(
        vector: number[],
        k: number,
        filter?: Record<string, any>
    ): Promise<Array<{
        id: string;
        score: number;
        metadata: Record<string, any>;
    }>>;
    deleteDocument(id: string): Promise<void>;
    clear(): Promise<void>;
}

export interface ILLMService {
    generateResponse(
        prompt: string,
        context: string[],
        options?: {
            temperature?: number;
            maxTokens?: number;
        }
    ): Promise<string>;
    generateAnalysis(
        document: string,
        regulations: string[]
    ): Promise<ComplianceIssue[]>;
}

export interface IRAGService {
    processQuery(
        query: string,
        options?: {
            maxResults?: number;
            minScore?: number;
        }
    ): Promise<{
        answer: string;
        sources: string[];
        confidence: number;
    }>;
    addDocument(
        content: string,
        metadata: Record<string, any>
    ): Promise<string>;
}

export interface INotificationService {
    sendNotification(
        userId: string,
        message: string,
        type: 'compliance' | 'regulatory' | 'risk'
    ): Promise<void>;
    updateSettings(
        userId: string,
        settings: {
            email: boolean;
            inApp: boolean;
            frequency: string;
        }
    ): Promise<void>;
}

export interface ICacheService {
    get<T>(key: string): Promise<T | null>;
    set<T>(key: string, value: T, ttl?: number): Promise<void>;
    delete(key: string): Promise<void>;
    clear(): Promise<void>;
} 