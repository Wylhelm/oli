/**
 * DOMScanner - Advanced DOM scanning with MutationObserver
 * Based on opus45.md specifications for F1 module
 */

export interface ExtractedField {
  name: string;
  type: string;
  value: string;
  label: string;
  required: boolean;
  element?: HTMLElement;
}

export interface ExtractedForm {
  id: string;
  action: string;
  method: string;
  fields: ExtractedField[];
}

export interface ExtractedTable {
  id: string;
  headers: string[];
  rows: string[][];
}

export interface ScanResult {
  forms: ExtractedForm[];
  inputs: ExtractedField[];
  tables: ExtractedTable[];
  textBlocks: string[];
  rawText: string;
  metadata: {
    url: string;
    title: string;
    timestamp: number;
  };
}

class DOMScanner {
  private observerConfig: MutationObserverInit;
  private mutationObserver: MutationObserver | null;
  private debounceTimeout: ReturnType<typeof setTimeout> | null;

  constructor() {
    this.observerConfig = {
      childList: true,
      subtree: true,
      attributes: true,
      attributeFilter: ['value', 'src', 'data-value']
    };
    this.mutationObserver = null;
    this.debounceTimeout = null;
  }

  /**
   * Initialize the scanner with mutation observation
   */
  init(): void {
    this.setupMutationObserver();
    this.setupFormListeners();
  }

  /**
   * Perform a full scan of the current page
   */
  scanCurrentPage(): ScanResult {
    return {
      forms: this.extractForms(),
      inputs: this.extractInputFields(),
      tables: this.extractDataTables(),
      textBlocks: this.extractRelevantText(),
      rawText: document.body.innerText,
      metadata: {
        url: window.location.href,
        title: document.title,
        timestamp: Date.now()
      }
    };
  }

  /**
   * Extract all forms from the page
   */
  private extractForms(): ExtractedForm[] {
    const forms = document.querySelectorAll('form');
    return Array.from(forms).map(form => ({
      id: form.id || this.generateUniqueId(),
      action: form.action,
      method: form.method,
      fields: this.extractFormFields(form)
    }));
  }

  /**
   * Extract fields from a specific form
   */
  private extractFormFields(form: HTMLFormElement): ExtractedField[] {
    const fields = form.querySelectorAll('input, select, textarea');
    return Array.from(fields).map(field => {
      const inputField = field as HTMLInputElement;
      return {
        name: inputField.name || inputField.id,
        type: inputField.type || field.tagName.toLowerCase(),
        value: inputField.value,
        label: this.findLabelForField(inputField),
        required: inputField.required
      };
    });
  }

  /**
   * Extract all input fields (including those outside forms)
   */
  private extractInputFields(): ExtractedField[] {
    const allFields = document.querySelectorAll('input, select, textarea');
    return Array.from(allFields)
      .filter(field => !field.closest('form')) // Exclude fields inside forms
      .map(field => {
        const inputField = field as HTMLInputElement;
        return {
          name: inputField.name || inputField.id,
          type: inputField.type || field.tagName.toLowerCase(),
          value: inputField.value,
          label: this.findLabelForField(inputField),
          required: inputField.required
        };
      });
  }

  /**
   * Find the associated label for a field
   */
  private findLabelForField(field: HTMLInputElement): string {
    // By 'for' attribute
    if (field.id) {
      const label = document.querySelector(`label[for="${field.id}"]`);
      if (label) return label.textContent?.trim() || '';
    }
    // By parent label
    const parentLabel = field.closest('label');
    if (parentLabel) return parentLabel.textContent?.trim() || '';
    // By aria-label
    return field.getAttribute('aria-label') || '';
  }

  /**
   * Extract data tables
   */
  private extractDataTables(): ExtractedTable[] {
    const tables = document.querySelectorAll('table');
    return Array.from(tables).map(table => ({
      id: table.id || this.generateUniqueId(),
      headers: this.extractTableHeaders(table),
      rows: this.extractTableRows(table)
    }));
  }

  private extractTableHeaders(table: HTMLTableElement): string[] {
    const headers = table.querySelectorAll('th');
    return Array.from(headers).map(th => th.textContent?.trim() || '');
  }

  private extractTableRows(table: HTMLTableElement): string[][] {
    const rows = table.querySelectorAll('tbody tr, tr');
    return Array.from(rows)
      .filter(row => row.querySelector('td')) // Only rows with data cells
      .map(row => {
        const cells = row.querySelectorAll('td');
        return Array.from(cells).map(cell => cell.textContent?.trim() || '');
      });
  }

  /**
   * Extract relevant text blocks (sections with data)
   */
  private extractRelevantText(): string[] {
    const textBlocks: string[] = [];
    
    // Extract from common data containers
    const containers = document.querySelectorAll(
      '.section, .field, .data-row, [data-field], .form-group, dl, .info-block'
    );
    
    containers.forEach(container => {
      const text = container.textContent?.trim();
      if (text && text.length > 5 && text.length < 1000) {
        textBlocks.push(text);
      }
    });

    // Also extract from definition lists
    const dlElements = document.querySelectorAll('dl');
    dlElements.forEach(dl => {
      const dts = dl.querySelectorAll('dt');
      const dds = dl.querySelectorAll('dd');
      dts.forEach((dt, i) => {
        if (dds[i]) {
          textBlocks.push(`${dt.textContent?.trim()}: ${dds[i].textContent?.trim()}`);
        }
      });
    });

    return textBlocks;
  }

  /**
   * Setup MutationObserver to watch for DOM changes
   */
  private setupMutationObserver(): void {
    this.mutationObserver = new MutationObserver((mutations) => {
      mutations.forEach(mutation => {
        if (this.isRelevantMutation(mutation)) {
          this.handleDOMChange(mutation);
        }
      });
    });
    
    if (document.body) {
      this.mutationObserver.observe(document.body, this.observerConfig);
    }
  }

  private isRelevantMutation(mutation: MutationRecord): boolean {
    const relevantTags = ['INPUT', 'SELECT', 'TEXTAREA', 'FORM', 'TABLE'];
    if (mutation.type === 'childList') {
      return Array.from(mutation.addedNodes).some(
        node => node.nodeType === 1 && relevantTags.includes((node as Element).tagName)
      );
    }
    return mutation.type === 'attributes';
  }

  private handleDOMChange(mutation: MutationRecord): void {
    const event = new CustomEvent('oli-dom-change', {
      detail: { mutation, timestamp: Date.now() }
    });
    document.dispatchEvent(event);
  }

  /**
   * Setup listeners for form field changes
   */
  private setupFormListeners(): void {
    document.addEventListener('input', this.debounce((e: Event) => {
      const target = e.target as HTMLElement;
      if (this.isFormElement(target)) {
        this.onFieldChange(target as HTMLInputElement);
      }
    }, 500));

    document.addEventListener('change', (e: Event) => {
      const target = e.target as HTMLElement;
      if (this.isFormElement(target)) {
        this.onFieldChange(target as HTMLInputElement);
      }
    });
  }

  private isFormElement(element: HTMLElement): boolean {
    return ['INPUT', 'SELECT', 'TEXTAREA'].includes(element.tagName);
  }

  private onFieldChange(field: HTMLInputElement): void {
    const event = new CustomEvent('oli-field-change', {
      detail: {
        field: {
          name: field.name || field.id,
          value: field.value,
          type: field.type
        },
        timestamp: Date.now()
      }
    });
    document.dispatchEvent(event);
  }

  private generateUniqueId(): string {
    return `oli-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
  }

  private debounce(
    func: (e: Event) => void,
    wait: number
  ): (e: Event) => void {
    return (e: Event) => {
      if (this.debounceTimeout) {
        clearTimeout(this.debounceTimeout);
      }
      this.debounceTimeout = setTimeout(() => func(e), wait);
    };
  }

  /**
   * Cleanup resources
   */
  destroy(): void {
    if (this.mutationObserver) {
      this.mutationObserver.disconnect();
    }
    if (this.debounceTimeout) {
      clearTimeout(this.debounceTimeout);
    }
  }
}

export default DOMScanner;

