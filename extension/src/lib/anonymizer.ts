/**
 * DataAnonymizer - Client-side PII anonymization before sending to backend
 * Based on opus45.md specifications - compliant with privacy regulations
 */

interface PatternMap {
  [key: string]: RegExp;
}

interface TokenInfo {
  original: string;
  type: string;
  token: string;
}

class DataAnonymizer {
  private patterns: PatternMap;
  private tokenMap: Map<string, TokenInfo>;
  private reverseMap: Map<string, string>;
  private tokenCounter: number;

  constructor() {
    this.patterns = {
      // Canadian Social Insurance Number
      sin: /\b\d{3}[-\s]?\d{3}[-\s]?\d{3}\b/g,
      // Passport number (common formats)
      passport: /\b[A-Z]{2}\d{6}\b/g,
      // Email addresses
      email: /\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b/g,
      // Canadian phone numbers
      phone: /\b(\+1[-\s]?)?\(?\d{3}\)?[-\s]?\d{3}[-\s]?\d{4}\b/g,
      // Canadian postal codes
      postalCode: /\b[A-Z]\d[A-Z][-\s]?\d[A-Z]\d\b/gi,
      // Credit card numbers
      creditCard: /\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b/g,
      // Dates (various formats)
      date: /\b\d{4}[-/]\d{2}[-/]\d{2}\b|\b\d{2}[-/]\d{2}[-/]\d{4}\b/g,
      // UCI (Unique Client Identifier) - Immigration format
      uci: /\bUCI[-\s]?\d{8,10}\b/gi,
      // Bank account numbers (generic pattern)
      bankAccount: /\b\d{5,12}\b/g,
      // IP addresses
      ip: /\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b/g
    };

    this.tokenMap = new Map();
    this.reverseMap = new Map();
    this.tokenCounter = 0;
  }

  /**
   * Main anonymization method - handles strings and objects
   */
  anonymize(data: string | object): string | object {
    if (typeof data === 'string') {
      return this.anonymizeString(data);
    } else if (typeof data === 'object' && data !== null) {
      return this.anonymizeObject(data as Record<string, unknown>);
    }
    return data;
  }

  /**
   * Anonymize a string by replacing PII with tokens
   */
  anonymizeString(text: string): string {
    let anonymized = text;

    // Apply pattern-based anonymization
    for (const [type, pattern] of Object.entries(this.patterns)) {
      // Skip generic bank account pattern to avoid false positives
      if (type === 'bankAccount') continue;
      
      anonymized = anonymized.replace(pattern, (match) => {
        return this.createToken(match, type);
      });
    }

    // Anonymize common proper nouns (French/English names)
    anonymized = this.anonymizeProperNouns(anonymized);

    return anonymized;
  }

  /**
   * Anonymize an object recursively
   */
  anonymizeObject(obj: Record<string, unknown>): Record<string, unknown> {
    const sensitiveFields = [
      'name', 'nom', 'prenom', 'firstname', 'lastname',
      'email', 'courriel', 'phone', 'telephone', 'tel',
      'address', 'adresse', 'sin', 'nas', 'ssn',
      'passport', 'passeport', 'dob', 'dateofbirth',
      'datenaissance', 'creditcard', 'carte', 'account',
      'compte', 'uci', 'clientid'
    ];

    const anonymized: Record<string, unknown> = {};

    for (const [key, value] of Object.entries(obj)) {
      const lowerKey = key.toLowerCase();
      const isSensitive = sensitiveFields.some(f => lowerKey.includes(f));

      if (isSensitive && typeof value === 'string') {
        anonymized[key] = this.createToken(value, `field_${key}`);
      } else if (typeof value === 'object' && value !== null) {
        anonymized[key] = this.anonymizeObject(value as Record<string, unknown>);
      } else if (typeof value === 'string') {
        anonymized[key] = this.anonymizeString(value);
      } else {
        anonymized[key] = value;
      }
    }

    return anonymized;
  }

  /**
   * Create a unique token for a piece of PII
   */
  private createToken(original: string, type: string): string {
    // Check if already tokenized
    const existing = this.reverseMap.get(original);
    if (existing) return existing;

    const typeLabel = type.toUpperCase().replace(/[^A-Z]/g, '_');
    const token = `<${typeLabel}_${++this.tokenCounter}>`;

    this.tokenMap.set(token, { original, type, token });
    this.reverseMap.set(original, token);

    return token;
  }

  /**
   * Anonymize proper nouns using heuristics
   */
  private anonymizeProperNouns(text: string): string {
    // Common name prefixes that indicate a name follows
    const nameIndicators = [
      'Nom complet :',
      'Nom :',
      'Name:',
      'Demandeur :',
      'Applicant:',
      'M\\.',
      'Mme\\.',
      'Mr\\.',
      'Mrs\\.',
      'Ms\\.'
    ];

    let anonymized = text;

    // Replace names after indicators
    nameIndicators.forEach(indicator => {
      const indicatorPattern = new RegExp(
        `(${indicator}\\s*)([A-Z][a-zéèêëàâäùûüôöîïç]+(?:\\s+[A-Z][a-zéèêëàâäùûüôöîïç]+)*)`,
        'g'
      );
      anonymized = anonymized.replace(indicatorPattern, (_match, prefix, name) => {
        return prefix + this.createToken(name, 'PERSON');
      });
    });

    return anonymized;
  }

  /**
   * De-anonymize text by replacing tokens with original values
   * (Used for display purposes only, never sent to backend)
   */
  deanonymize(text: string): string {
    let result = text;
    this.tokenMap.forEach((info, token) => {
      result = result.replace(new RegExp(token.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'), 'g'), info.original);
    });
    return result;
  }

  /**
   * Get anonymization summary for audit trail
   */
  getAnonymizationSummary(): { totalTokens: number; byType: Record<string, number> } {
    const byType: Record<string, number> = {};
    
    this.tokenMap.forEach((info) => {
      byType[info.type] = (byType[info.type] || 0) + 1;
    });

    return {
      totalTokens: this.tokenMap.size,
      byType
    };
  }

  /**
   * Reset the anonymizer state
   */
  reset(): void {
    this.tokenMap.clear();
    this.reverseMap.clear();
    this.tokenCounter = 0;
  }
}

// Singleton instance
const anonymizer = new DataAnonymizer();
export default anonymizer;
export { DataAnonymizer };

