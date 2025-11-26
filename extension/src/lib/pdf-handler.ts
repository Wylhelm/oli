/**
 * PDF Handler - Extract text from PDF documents using PDF.js
 * Supports embedded PDFs, PDF URLs, and file uploads
 */

import * as pdfjsLib from 'pdfjs-dist';

// Types
export interface PDFExtractionResult {
  success: boolean;
  totalPages: number;
  content: PageContent[];
  formFields: FormField[];
  fullText: string;
  error?: string;
}

export interface PageContent {
  page: number;
  text: string;
}

export interface FormField {
  page: number;
  name: string;
  type: string;
  value: string | null;
}

export interface DetectedPDF {
  url: string;
  type: 'embed' | 'iframe' | 'object' | 'link';
  element: Element;
}

class PDFHandler {
  private workerInitialized = false;

  constructor() {
    this.initWorker();
  }

  /**
   * Initialize PDF.js worker
   */
  private initWorker(): void {
    if (this.workerInitialized) return;
    
    try {
      // Use CDN worker for Chrome extension compatibility
      pdfjsLib.GlobalWorkerOptions.workerSrc = 
        'https://cdnjs.cloudflare.com/ajax/libs/pdf.js/4.0.379/pdf.worker.min.mjs';
      this.workerInitialized = true;
    } catch (error) {
      console.error('[OLI PDF] Worker initialization failed:', error);
    }
  }

  /**
   * Extract text from a PDF URL
   */
  async extractFromUrl(pdfUrl: string): Promise<PDFExtractionResult> {
    try {
      this.initWorker();
      
      const loadingTask = pdfjsLib.getDocument({
        url: pdfUrl,
        // Required for CORS
        withCredentials: false,
      });
      
      const pdf = await loadingTask.promise;
      return await this.extractFromDocument(pdf);
    } catch (error) {
      console.error('[OLI PDF] URL extraction failed:', error);
      return {
        success: false,
        totalPages: 0,
        content: [],
        formFields: [],
        fullText: '',
        error: error instanceof Error ? error.message : 'Unknown error'
      };
    }
  }

  /**
   * Extract text from a PDF ArrayBuffer (file upload)
   */
  async extractFromBuffer(buffer: ArrayBuffer): Promise<PDFExtractionResult> {
    try {
      this.initWorker();
      
      const loadingTask = pdfjsLib.getDocument({ data: buffer });
      const pdf = await loadingTask.promise;
      return await this.extractFromDocument(pdf);
    } catch (error) {
      console.error('[OLI PDF] Buffer extraction failed:', error);
      return {
        success: false,
        totalPages: 0,
        content: [],
        formFields: [],
        fullText: '',
        error: error instanceof Error ? error.message : 'Unknown error'
      };
    }
  }

  /**
   * Extract content from a loaded PDF document
   */
  private async extractFromDocument(pdf: pdfjsLib.PDFDocumentProxy): Promise<PDFExtractionResult> {
    const content: PageContent[] = [];
    const formFields: FormField[] = [];
    const textParts: string[] = [];

    for (let pageNum = 1; pageNum <= pdf.numPages; pageNum++) {
      try {
        const page = await pdf.getPage(pageNum);

        // Extract text content
        const textContent = await page.getTextContent();
        const pageText = textContent.items
          .map((item) => {
            if ('str' in item) {
              return item.str;
            }
            return '';
          })
          .join(' ')
          .replace(/\s+/g, ' ')
          .trim();

        content.push({ page: pageNum, text: pageText });
        textParts.push(pageText);

        // Extract form fields (annotations)
        try {
          const annotations = await page.getAnnotations();
          for (const annotation of annotations) {
            if (annotation.subtype === 'Widget') {
              formFields.push({
                page: pageNum,
                name: annotation.fieldName || `field_${pageNum}_${formFields.length}`,
                type: annotation.fieldType || 'unknown',
                value: annotation.fieldValue || null
              });
            }
          }
        } catch {
          // Annotations may fail on some PDFs
        }
      } catch (pageError) {
        console.warn(`[OLI PDF] Page ${pageNum} extraction failed:`, pageError);
        content.push({ page: pageNum, text: '[Extraction failed]' });
      }
    }

    return {
      success: true,
      totalPages: pdf.numPages,
      content,
      formFields,
      fullText: textParts.join('\n\n')
    };
  }

  /**
   * Detect PDFs embedded in the current page
   */
  detectEmbeddedPDFs(): DetectedPDF[] {
    const detected: DetectedPDF[] = [];

    // Check embed elements
    document.querySelectorAll('embed[type="application/pdf"]').forEach(el => {
      const src = (el as HTMLEmbedElement).src;
      if (src) {
        detected.push({ url: src, type: 'embed', element: el });
      }
    });

    // Check iframes with PDF
    document.querySelectorAll('iframe').forEach(el => {
      const src = el.src;
      if (src && (src.endsWith('.pdf') || src.includes('.pdf?'))) {
        detected.push({ url: src, type: 'iframe', element: el });
      }
    });

    // Check object elements
    document.querySelectorAll('object[data*=".pdf"], object[type="application/pdf"]').forEach(el => {
      const data = (el as HTMLObjectElement).data;
      if (data) {
        detected.push({ url: data, type: 'object', element: el });
      }
    });

    // Check links to PDFs
    document.querySelectorAll('a[href*=".pdf"]').forEach(el => {
      const href = (el as HTMLAnchorElement).href;
      if (href && href.endsWith('.pdf')) {
        detected.push({ url: href, type: 'link', element: el });
      }
    });

    return detected;
  }

  /**
   * Check if the current page is a PDF viewer
   */
  isPDFViewer(): boolean {
    // Chrome's built-in PDF viewer
    if (document.querySelector('embed[type="application/pdf"]')) {
      return true;
    }
    
    // URL ends with .pdf
    if (window.location.href.toLowerCase().endsWith('.pdf')) {
      return true;
    }
    
    // Common PDF viewer patterns
    if (document.querySelector('#viewer.pdfViewer, .pdf-viewer, #pdf-js-viewer')) {
      return true;
    }

    return false;
  }

  /**
   * Get the PDF URL if viewing a PDF directly
   */
  getCurrentPDFUrl(): string | null {
    // Direct PDF URL
    if (window.location.href.toLowerCase().endsWith('.pdf')) {
      return window.location.href;
    }

    // Embedded PDF
    const embed = document.querySelector('embed[type="application/pdf"]') as HTMLEmbedElement;
    if (embed?.src) {
      return embed.src;
    }

    return null;
  }
}

export const pdfHandler = new PDFHandler();
export default pdfHandler;

