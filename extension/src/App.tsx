import { useState, useEffect } from 'react'
import { 
  AlertTriangle, 
  CheckCircle, 
  FileText, 
  Shield, 
  ExternalLink, 
  Loader2,
  AlertCircle,
  ChevronRight,
  Scale,
  FileCheck,
  User,
  Wallet,
  Clock,
  ShieldCheck,
  ShieldAlert,
  ShieldX,
  Sparkles,
  Zap,
  BookOpen,
  Brain,
  FileType,
  RotateCcw,
  Settings,
  Sun,
  Moon,
  Eye,
  Type,
  X
} from 'lucide-react'
import { cn } from './lib/utils'
import { pdfHandler, type DetectedPDF } from './lib/pdf-handler'
import logoImg from './assets/logo.png'

// Display Modes
type DisplayMode = 'standard' | 'dark' | 'high-contrast' | 'senior';

// Types matching the LLM backend response
interface ComplianceCheck {
  id: string;
  name: string;
  status: 'CONFORME' | 'AVERTISSEMENT' | 'CRITIQUE';
  message: string;
  reference: string;
  url: string;
  recommendation: string;
  highlight_text: string | null;
  confidence?: number;
}

interface LegalSource {
  title: string;
  url: string;
  doc_type?: string;
  section?: string;
  summary?: string;
  relevance?: number;
}

interface AnalysisResult {
  overall_status: 'CONFORME' | 'AVERTISSEMENT' | 'CRITIQUE';
  risk_score: number;
  completeness_score: number;
  checks: ComplianceCheck[];
  anonymized_text: string;
  summary: string;
  sources?: LegalSource[];
  analysis_mode?: 'llm' | 'rule-based';
}

type AnalysisMode = 'llm' | 'fast';

// Status configuration
const statusConfig = {
  CONFORME: {
    color: 'emerald',
    bg: 'bg-emerald-50 dark:bg-emerald-950/30',
    border: 'border-emerald-200 dark:border-emerald-800',
    text: 'text-emerald-600 dark:text-emerald-400',
    icon: CheckCircle,
    label: 'Compliant'
  },
  AVERTISSEMENT: {
    color: 'amber',
    bg: 'bg-amber-50 dark:bg-amber-950/30',
    border: 'border-amber-200 dark:border-amber-800',
    text: 'text-amber-600 dark:text-amber-400',
    icon: AlertCircle,
    label: 'Warning'
  },
  CRITIQUE: {
    color: 'red',
    bg: 'bg-red-50 dark:bg-red-950/30',
    border: 'border-red-200 dark:border-red-800',
    text: 'text-red-600 dark:text-red-400',
    icon: AlertTriangle,
    label: 'Critical'
  }
};

// Check icon mapping
const checkIcons: Record<string, typeof Scale> = {
  'LICO_001': Wallet,
  'DOC_001': Clock,
  'ID_001': User,
  'POF_001': FileCheck
};

// Circular Progress Component
function CircularProgress({ 
  value, 
  max = 100, 
  size = 120, 
  strokeWidth = 8,
  color = 'primary',
  label,
  sublabel
}: { 
  value: number; 
  max?: number; 
  size?: number; 
  strokeWidth?: number;
  color?: string;
  label?: string;
  sublabel?: string;
}) {
  const radius = (size - strokeWidth) / 2;
  const circumference = radius * 2 * Math.PI;
  const progress = Math.min(value, max);
  const offset = circumference - (progress / max) * circumference;

  const colorMap: Record<string, string> = {
    primary: '#005696',
    emerald: '#10B981',
    amber: '#F59E0B',
    red: '#EF4444'
  };

  return (
    <div className="relative inline-flex items-center justify-center">
      <svg width={size} height={size} className="transform -rotate-90">
        {/* Background circle */}
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke="currentColor"
          className="text-slate-200 dark:text-slate-700"
          strokeWidth={strokeWidth}
        />
        {/* Progress circle */}
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke={colorMap[color] || colorMap.primary}
          strokeWidth={strokeWidth}
          strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          className="transition-all duration-1000 ease-out"
        />
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        {label && <span className="text-2xl font-bold text-slate-900 dark:text-slate-100">{label}</span>}
        {sublabel && <span className="text-xs text-slate-500 dark:text-slate-400">{sublabel}</span>}
      </div>
    </div>
  );
}

// Alert Card Component
function AlertCard({ check, index, onScrollTo, isPdfMode }: { check: ComplianceCheck; index: number; onScrollTo?: (text: string, status: string, message: string) => void; isPdfMode?: boolean }) {
  const config = statusConfig[check.status];
  const Icon = checkIcons[check.id] || Scale;
  const hasHighlight = !!check.highlight_text;
  // PDF mode: highlighting not supported, only allow clicking for HTML pages
  const isClickable = hasHighlight && !isPdfMode;
  
  const handleClick = () => {
    if (isClickable && onScrollTo && check.highlight_text) {
      console.log("[OLI AlertCard] Click - scrolling to:", check.highlight_text);
      onScrollTo(check.highlight_text, check.status, check.message);
    }
  };
  
  return (
    <div 
      className={cn(
        "p-4 rounded-xl border shadow-sm transition-all",
        "animate-in fade-in slide-in-from-bottom-4",
        "bg-white dark:bg-slate-900",
        check.status === 'CRITIQUE' && "border-l-4 border-l-red-500 border-red-100 dark:border-red-900",
        check.status === 'AVERTISSEMENT' && "border-l-4 border-l-amber-500 border-amber-100 dark:border-amber-900",
        check.status === 'CONFORME' && "border-l-4 border-l-emerald-500 border-emerald-100 dark:border-emerald-900",
        isClickable && "cursor-pointer hover:shadow-md hover:scale-[1.01]"
      )}
      style={{ animationDelay: `${index * 100}ms` }}
      onClick={handleClick}
      title={isClickable ? "Click to view in page" : undefined}
    >
      <div className="flex items-start gap-3">
        <div className={cn(
          "p-2 rounded-lg shrink-0",
          config.bg
        )}>
          <Icon className={cn("w-4 h-4", config.text)} />
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1">
            <h4 className="font-medium text-slate-900 dark:text-slate-100 text-sm">{check.name}</h4>
            <span className={cn(
              "px-2 py-0.5 rounded-full text-xs font-medium",
              config.bg, config.text
            )}>
              {config.label}
            </span>
            {isClickable && (
              <span className="text-xs text-slate-400 dark:text-slate-500 flex items-center gap-1">
                <ExternalLink className="w-3 h-3" />
                View
              </span>
            )}
          </div>
          <p className="text-sm text-slate-600 dark:text-slate-300 mb-2">{check.message}</p>
          {check.status !== 'CONFORME' && check.recommendation && (
            <p className="text-xs text-slate-500 dark:text-slate-400 italic flex items-center gap-1">
              <ChevronRight className="w-3 h-3" />
              {check.recommendation}
            </p>
          )}
        </div>
      </div>
      
      <div className="mt-3 pt-3 border-t border-slate-100 dark:border-slate-800 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span className="text-xs text-slate-400 dark:text-slate-500 bg-slate-50 dark:bg-slate-800 px-2 py-1 rounded font-mono">
            {check.reference}
          </span>
          {check.confidence !== undefined && (
            <span className="text-xs text-slate-400 dark:text-slate-500 flex items-center gap-1">
              <Sparkles className="w-3 h-3" />
              {Math.round(check.confidence * 100)}%
            </span>
          )}
        </div>
        <a
          href={check.url}
          target="_blank"
          rel="noopener noreferrer"
          className="text-xs font-medium text-primary dark:text-blue-400 hover:text-blue-700 dark:hover:text-blue-300 flex items-center gap-1 transition-colors"
        >
          Source
          <ExternalLink className="w-3 h-3" />
        </a>
      </div>
    </div>
  );
}

// Status Badge Component
function StatusBadge({ status }: { status: 'CONFORME' | 'AVERTISSEMENT' | 'CRITIQUE' }) {
  const config = statusConfig[status];
  const Icon = config.icon;
  
  return (
    <div className={cn(
      "inline-flex items-center gap-2 px-4 py-2 rounded-full font-semibold text-sm",
      config.bg, config.text, config.border, "border"
    )}>
      <Icon className="w-4 h-4" />
      {config.label}
    </div>
  );
}

// Source Card Component - Shows RAG summary with link to law
function SourceCard({ source, index }: { source: LegalSource; index: number }) {
  return (
    <div 
      className="bg-white dark:bg-slate-900 rounded-lg border border-slate-200 dark:border-slate-800 overflow-hidden transition-all hover:shadow-md animate-in fade-in slide-in-from-bottom-2"
      style={{ animationDelay: `${index * 80}ms` }}
    >
      {/* Header with title and relevance */}
      <div className="p-3 bg-gradient-to-r from-blue-50 to-slate-50 dark:from-slate-800 dark:to-slate-900 border-b border-slate-100 dark:border-slate-800">
        <div className="flex items-start gap-2">
          <div className="p-1.5 bg-blue-100 dark:bg-blue-900/30 rounded shrink-0">
            <Scale className="w-3.5 h-3.5 text-blue-700 dark:text-blue-400" />
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-sm font-semibold text-slate-800 dark:text-slate-100 leading-tight">
              {source.title}
            </p>
            <div className="flex items-center gap-2 mt-1 flex-wrap">
              {source.section && (
                <span className="text-xs text-blue-700 dark:text-blue-300 bg-blue-100 dark:bg-blue-900/30 px-2 py-0.5 rounded font-medium">
                  Section {source.section}
                </span>
              )}
              {source.doc_type && (
                <span className="text-xs text-slate-600 dark:text-slate-400 bg-slate-100 dark:bg-slate-800 px-2 py-0.5 rounded">
                  {source.doc_type}
                </span>
              )}
              {source.relevance && source.relevance > 0 && (
                <span className="text-xs text-emerald-700 dark:text-emerald-400 bg-emerald-100 dark:bg-emerald-900/30 px-2 py-0.5 rounded font-medium">
                  {Math.round(source.relevance * 100)}% relevant
                </span>
              )}
            </div>
          </div>
        </div>
      </div>
      
      {/* Summary from RAG - always visible */}
      {source.summary && (
        <div className="p-3 bg-white dark:bg-slate-900">
          <div className="text-xs text-slate-600 dark:text-slate-300 leading-relaxed border-l-3 border-blue-400 dark:border-blue-600 pl-3 py-1 bg-blue-50/50 dark:bg-blue-900/20 rounded-r">
            <p className="italic line-clamp-4">"{source.summary}"</p>
          </div>
        </div>
      )}
      
      {/* Link to full law */}
      <div className="px-3 pb-3 pt-1">
        <a
          href={source.url}
          target="_blank"
          rel="noopener noreferrer"
          className="inline-flex items-center gap-1.5 text-xs font-semibold text-blue-600 dark:text-blue-400 hover:text-blue-800 dark:hover:text-blue-300 transition-colors bg-blue-50 dark:bg-slate-800 hover:bg-blue-100 dark:hover:bg-slate-700 px-3 py-1.5 rounded-full"
        >
          <ExternalLink className="w-3.5 h-3.5" />
          View law on Justice.gc.ca
        </a>
      </div>
    </div>
  );
}

// Sources List Component
function SourcesList({ sources }: { sources: LegalSource[] }) {
  if (!sources || sources.length === 0) return null;
  
  return (
    <div className="bg-gradient-to-br from-slate-50 to-blue-50/30 dark:from-slate-900 dark:to-slate-800 rounded-xl p-4 border border-slate-200 dark:border-slate-800">
      <h4 className="text-xs font-semibold text-slate-600 dark:text-slate-400 uppercase tracking-wider mb-3 flex items-center gap-2">
        <BookOpen className="w-3.5 h-3.5 text-blue-600 dark:text-blue-400" />
        Legal Sources ({sources.length})
      </h4>
      <p className="text-xs text-slate-500 dark:text-slate-500 mb-3">
        Click on a source to view the relevant excerpt
      </p>
      <div className="space-y-2">
        {sources.slice(0, 5).map((source, i) => (
          <SourceCard key={i} source={source} index={i} />
        ))}
      </div>
    </div>
  );
}

// Analysis Mode Toggle Component
function ModeToggle({ 
  mode, 
  onChange 
}: { 
  mode: AnalysisMode; 
  onChange: (mode: AnalysisMode) => void 
}) {
  return (
    <div className="flex items-center gap-1 p-1 bg-slate-100 dark:bg-slate-800 rounded-lg">
      <button
        onClick={() => onChange('fast')}
        className={cn(
          "flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-medium transition-all",
          mode === 'fast' 
            ? "bg-white dark:bg-slate-700 text-slate-900 dark:text-slate-100 shadow-sm" 
            : "text-slate-500 dark:text-slate-400 hover:text-slate-700 dark:hover:text-slate-300"
        )}
      >
        <Zap className="w-3 h-3" />
        Fast
      </button>
      <button
        onClick={() => onChange('llm')}
        className={cn(
          "flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-medium transition-all",
          mode === 'llm' 
            ? "bg-white dark:bg-slate-700 text-slate-900 dark:text-slate-100 shadow-sm" 
            : "text-slate-500 dark:text-slate-400 hover:text-slate-700 dark:hover:text-slate-300"
        )}
      >
        <Brain className="w-3 h-3" />
        AI
      </button>
    </div>
  );
}

// Display Settings Modal
function DisplaySettingsModal({ 
  isOpen, 
  onClose, 
  currentMode, 
  onModeChange 
}: { 
  isOpen: boolean; 
  onClose: () => void; 
  currentMode: DisplayMode; 
  onModeChange: (mode: DisplayMode) => void;
}) {
  if (!isOpen) return null;

  const modes: { id: DisplayMode; name: string; desc: string; icon: any; previewClass: string }[] = [
    { id: 'standard', name: 'Standard', desc: 'Default light mode', icon: Sun, previewClass: 'bg-white border-slate-200 text-slate-900' },
    { id: 'dark', name: 'Dark Mode', desc: 'Reduces eye strain', icon: Moon, previewClass: 'bg-slate-900 border-slate-700 text-white' },
    { id: 'high-contrast', name: 'High Contrast', desc: 'Maximum contrast and readability', icon: Eye, previewClass: 'bg-white border-black border-2 text-black font-bold' },
    { id: 'senior', name: 'Senior Mode', desc: 'Larger text and simplified interface', icon: Type, previewClass: 'bg-slate-50 border-slate-300 text-slate-900 text-lg' }
  ];

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm animate-in fade-in p-4">
      <div className="bg-white dark:bg-slate-900 rounded-2xl w-full max-w-2xl p-6 shadow-2xl animate-in slide-in-from-bottom-8 relative max-h-[90vh] overflow-y-auto border border-slate-200 dark:border-slate-800">
        <button onClick={onClose} className="absolute top-4 right-4 p-2 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-full transition-colors">
          <X className="w-5 h-5 text-slate-500" />
        </button>
        
        <h2 className="text-xl font-bold text-slate-900 dark:text-white mb-6">Display Settings</h2>
        
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          {modes.map((mode) => (
            <button
              key={mode.id}
              onClick={() => onModeChange(mode.id)}
              className={cn(
                "p-4 rounded-xl border-2 text-left transition-all hover:scale-[1.02] flex flex-col gap-3",
                currentMode === mode.id 
                  ? "border-primary ring-2 ring-primary/20 bg-primary/5 dark:bg-primary/20" 
                  : "border-slate-200 dark:border-slate-700 hover:border-slate-300 dark:hover:border-slate-600 bg-white dark:bg-slate-800"
              )}
            >
              <div className="flex items-start gap-3">
                <div className={cn("p-2 rounded-lg shrink-0", currentMode === mode.id ? "bg-primary text-white" : "bg-slate-100 dark:bg-slate-700 text-slate-500 dark:text-slate-400")}>
                  <mode.icon className="w-5 h-5" />
                </div>
                <div>
                  <h3 className="font-semibold text-slate-900 dark:text-white">{mode.name}</h3>
                  <p className="text-xs text-slate-500 dark:text-slate-400">{mode.desc}</p>
                </div>
              </div>
              
              {/* Preview */}
              <div className={cn("h-12 rounded-lg flex items-center px-3 w-full", mode.previewClass)}>
                 Text preview
                 {mode.id === 'high-contrast' && <div className="ml-auto w-3 h-3 bg-yellow-400 rounded-full ring-1 ring-black"/>}
              </div>
            </button>
          ))}
        </div>
        
        <div className="mt-6 pt-6 border-t border-slate-100 dark:border-slate-800">
          <h3 className="font-semibold text-slate-900 dark:text-white mb-3">Interface Preview</h3>
          <div className="p-4 rounded-xl border border-slate-200 dark:border-slate-800 bg-slate-50/50 dark:bg-slate-950/50">
            <div className="flex items-center gap-3 mb-3">
              <div className="w-10 h-10 rounded-lg bg-primary/10 flex items-center justify-center">
                <Shield className="w-5 h-5 text-primary" />
              </div>
              <div>
                <div className="h-4 w-24 bg-slate-200 dark:bg-slate-700 rounded mb-1.5"></div>
                <div className="h-3 w-16 bg-slate-100 dark:bg-slate-800 rounded"></div>
              </div>
            </div>
            <div className="h-20 bg-white dark:bg-slate-800 rounded-lg border border-slate-200 dark:border-slate-700 p-3">
              <div className="h-3 w-3/4 bg-slate-100 dark:bg-slate-700 rounded mb-2"></div>
              <div className="h-3 w-1/2 bg-slate-100 dark:bg-slate-700 rounded"></div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

function App() {
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<AnalysisResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [analysisMode, setAnalysisMode] = useState<AnalysisMode>('llm');
  const [loadingMessage, setLoadingMessage] = useState('');
  const [detectedPDFs, setDetectedPDFs] = useState<DetectedPDF[]>([]);
  const [currentPdfUrl, setCurrentPdfUrl] = useState<string | null>(null);
  
  // Display Settings State
  const [isSettingsOpen, setIsSettingsOpen] = useState(false);
  const [displayMode, setDisplayMode] = useState<DisplayMode>(() => {
    const saved = localStorage.getItem('oli-display-mode');
    return (saved as DisplayMode) || 'standard';
  });

  // Apply display mode to root element
  useEffect(() => {
    const root = document.documentElement;
    root.classList.remove('dark', 'high-contrast', 'senior');
    if (displayMode === 'dark') root.classList.add('dark');
    if (displayMode === 'high-contrast') root.classList.add('high-contrast');
    if (displayMode === 'senior') root.classList.add('senior');
    
    localStorage.setItem('oli-display-mode', displayMode);
  }, [displayMode]);

  // Detect PDFs when component mounts
  useEffect(() => {
    detectPDFs();
  }, []);

  // Detect PDFs on the current page
  const detectPDFs = async () => {
    try {
      const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
      if (!tab.id) return;

      const results = await chrome.scripting.executeScript({
        target: { tabId: tab.id },
        func: () => {
          const detected: Array<{url: string; type: string}> = [];
          
          // Check embed elements
          document.querySelectorAll('embed[type="application/pdf"]').forEach(el => {
            const src = (el as HTMLEmbedElement).src;
            if (src) detected.push({ url: src, type: 'embed' });
          });
          
          // Check iframes with PDF
          document.querySelectorAll('iframe').forEach(el => {
            const src = el.src;
            if (src && (src.endsWith('.pdf') || src.includes('.pdf?'))) {
              detected.push({ url: src, type: 'iframe' });
            }
          });
          
          // Check links to PDFs
          document.querySelectorAll('a[href$=".pdf"]').forEach(el => {
            const href = (el as HTMLAnchorElement).href;
            if (href) detected.push({ url: href, type: 'link' });
          });
          
          // Check if current page is PDF
          if (window.location.href.toLowerCase().endsWith('.pdf')) {
            detected.push({ url: window.location.href, type: 'direct' });
          }
          
          return detected;
        }
      });

      if (results[0]?.result) {
        setDetectedPDFs(results[0].result as DetectedPDF[]);
      }
    } catch (err) {
      console.error('PDF detection failed:', err);
    }
  };

  // Analyze a detected PDF
  const analyzePDF = async (pdf: DetectedPDF) => {
    setLoading(true);
    setResult(null);
    setError(null);
    setLoadingMessage('Extracting PDF...');
    // Store PDF URL for navigation
    setCurrentPdfUrl(pdf.url);

    try {
      // Extract PDF with page content
      const pdfResult = await pdfHandler.extractFromUrl(pdf.url);
      if (!pdfResult.success) {
        throw new Error(pdfResult.error || 'Unable to extract text from PDF');
      }
      
      // Analyze with LLM
      setLoadingMessage('Retrieving legal context...');
      setTimeout(() => setLoadingMessage('AI analysis in progress...'), 1500);

      const endpoint = analysisMode === 'llm' 
        ? 'http://localhost:8001/analyze/llm' 
        : 'http://localhost:8001/analyze';
      
      const response = await fetch(endpoint, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text: pdfResult.fullText }),
      });

      if (!response.ok) {
        throw new Error(`Server error: ${response.status}`);
      }

      const data: AnalysisResult = await response.json();
      setResult(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
      setCurrentPdfUrl(null);
    } finally {
      setLoading(false);
      setLoadingMessage('');
    }
  };

  const scanPage = async () => {
    setLoading(true);
    setResult(null);
    setError(null);
    
    // Show progressive loading messages for LLM mode
    if (analysisMode === 'llm') {
      setLoadingMessage('Extracting content...');
      setTimeout(() => setLoadingMessage('Retrieving legal context...'), 1500);
      setTimeout(() => setLoadingMessage('AI analysis in progress...'), 3000);
    }

    // Also detect PDFs
    detectPDFs();

    try {
      // 1. Get active tab
      const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
      if (!tab.id) {
        throw new Error("No active tab found");
      }

      // Check if current page is a PDF (including Adobe Acrobat wrapper)
      const isAdobePdf = tab.url?.startsWith('chrome-extension://') && tab.url?.includes('/http');
      const isPdfPage = tab.url?.toLowerCase().endsWith('.pdf') || 
                        tab.url?.includes('/pdf/') ||
                        tab.url?.includes('blob:') ||
                        isAdobePdf;
      
      // Extract original URL if Adobe has wrapped it
      let originalPdfUrl = tab.url;
      if (isAdobePdf && tab.url) {
        // Format: chrome-extension://[id]/http://... -> extract http://...
        const httpMatch = tab.url.match(/(https?:\/\/.+)$/);
        if (httpMatch) {
          originalPdfUrl = httpMatch[1];
          console.log("[OLI] Extracted original PDF URL from Adobe:", originalPdfUrl);
        }
      }
      
      let pageText: string;
      
      if (isPdfPage && originalPdfUrl) {
        // Extract PDF with page tracking
        setLoadingMessage('Extracting PDF...');
        // Set the ORIGINAL PDF URL for navigation (not the Adobe wrapper URL)
        setCurrentPdfUrl(originalPdfUrl);
        console.log("[OLI] PDF detected, setting currentPdfUrl:", originalPdfUrl);
        
        try {
          // Use original URL for PDF extraction (not Adobe wrapper)
          const pdfResult = await pdfHandler.extractFromUrl(originalPdfUrl);
          if (pdfResult.success) {
            // pdfPageContent disabled - PDF.js blocked by CSP
            pageText = pdfResult.fullText;
            console.log("[OLI] PDF extraction success, pages:", pdfResult.content.length);
          } else {
            throw new Error(pdfResult.error || 'PDF extraction failed');
          }
        } catch (pdfError) {
          // PDF extraction failed (likely CSP blocking PDF.js)
          console.log("[OLI] PDF extraction failed:", pdfError);
          
          // If we're on Adobe's extension page, we can't extract text via script
          if (isAdobePdf) {
            console.log("[OLI] On Adobe page, cannot extract text. Using placeholder.");
            // We can still navigate using the original URL, but analysis will be limited
            pageText = `[PDF opened in Adobe Acrobat: ${originalPdfUrl}]\n\nAnalysis of this PDF requires manual extraction. Navigation functions remain available.`;
          } else {
            // Try to extract text from page
            try {
              const injectionResults = await chrome.scripting.executeScript({
                target: { tabId: tab.id },
                func: () => document.body.innerText,
              });
              pageText = injectionResults[0].result || '';
            } catch {
              pageText = '';
            }
          }
        }
      } else {
        // Regular page - clear PDF state
        setCurrentPdfUrl(null);
        
        // Extract page text
        const injectionResults = await chrome.scripting.executeScript({
          target: { tabId: tab.id },
          func: () => document.body.innerText,
        });
        pageText = injectionResults[0].result || '';
      }

      // 3. Send to Backend (LLM or Fast mode)
      const endpoint = analysisMode === 'llm' 
        ? 'http://localhost:8001/analyze/llm' 
        : 'http://localhost:8001/analyze';
      
      const response = await fetch(endpoint, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          text: pageText,
          url: tab.url 
        }),
      });

      if (!response.ok) {
        throw new Error(`Server error: ${response.status}`);
      }

      const data: AnalysisResult = await response.json();
      setResult(data);

      // 4. Highlight risks in page
      const highlightTexts = data.checks
        .filter(c => c.highlight_text && c.status !== 'CONFORME')
        .map(c => ({
          text: c.highlight_text!,
          status: c.status
        }));

      if (highlightTexts.length > 0) {
        await chrome.scripting.executeScript({
          target: { tabId: tab.id },
          files: ['content.js']
        });

        // Send highlight data after script loads
        setTimeout(() => {
          chrome.tabs.sendMessage(tab.id!, {
            action: "HIGHLIGHT_RISKS",
            data: {
              highlights: highlightTexts,
              overallStatus: data.overall_status
            }
          });
        }, 300);
      }

    } catch (err) {
      console.error("Error scanning page:", err);
      setError(err instanceof Error ? err.message : "Unknown error");
    } finally {
      setLoading(false);
      setLoadingMessage('');
    }
  };

  // Determine risk color for circular progress
  const getRiskColor = (score: number): string => {
    if (score >= 60) return 'red';
    if (score >= 30) return 'amber';
    return 'emerald';
  };

  // Reset to initial state for new analysis
  const resetAnalysis = async () => {
    setResult(null);
    setError(null);
    setDetectedPDFs([]);
    // Clear PDF analysis state
    setCurrentPdfUrl(null);
    
    // Clear highlights in the page
    try {
      const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
      if (tab?.id) {
        chrome.tabs.sendMessage(tab.id, { action: "CLEAR_HIGHLIGHTS" }).catch(() => {});
      }
    } catch {
      // Ignore errors
    }
    
    // Re-detect PDFs
    detectPDFs();
  };


  // Scroll to and highlight text in the page
  const scrollToHighlight = async (text: string, status: string, message: string) => {
    console.log("[OLI] scrollToHighlight called:", { text, status, isPdf: !!currentPdfUrl });
    
    // PDF highlighting not supported - skip for PDF pages
    if (currentPdfUrl) {
      console.log("[OLI] PDF mode - highlighting not supported");
      return;
    }
    
    try {
      const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
      console.log("[OLI] Active tab:", tab?.id, tab?.url);
      
      if (!tab?.id) {
        console.error("[OLI] No active tab found");
        return;
      }

      // Try to send message directly first (script may already be loaded)
      try {
        const response = await chrome.tabs.sendMessage(tab.id, {
          action: "SCROLL_TO_TEXT",
          data: { text, status, message }
        });
        console.log("[OLI] Response:", response);
        return;
      } catch {
        // Script not loaded, inject it
        console.log("[OLI] Script not loaded, injecting...");
      }

      // Inject content script
      await chrome.scripting.executeScript({
        target: { tabId: tab.id },
        files: ['content.js']
      });
      
      // Wait a bit then send message
      await new Promise(resolve => setTimeout(resolve, 300));
      
      // Send scroll message
      console.log("[OLI] Sending SCROLL_TO_TEXT message after injection");
      const response = await chrome.tabs.sendMessage(tab.id, {
        action: "SCROLL_TO_TEXT",
        data: { text, status, message }
      });
      console.log("[OLI] Response:", response);
      
    } catch (err) {
      console.error("[OLI] Failed to scroll to highlight:", err);
    }
  };

  return (
    <div className="w-full min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 text-slate-900 font-sans">
      {/* Display Settings Modal */}
      <DisplaySettingsModal 
        isOpen={isSettingsOpen}
        onClose={() => setIsSettingsOpen(false)}
        currentMode={displayMode}
        onModeChange={setDisplayMode}
      />

      {/* Header with Glass Effect */}
      <header className="bg-white/80 backdrop-blur-md border-b border-slate-200/50 p-4 sticky top-0 z-10">
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center gap-3">
            <div className="relative">
              <div className="absolute inset-0 bg-primary/20 blur-lg rounded-xl"></div>
              <img 
                src={logoImg} 
                alt="OLI Logo" 
                className="relative w-10 h-10 rounded-xl shadow-lg object-contain"
              />
            </div>
            <div>
              <h1 className="font-bold text-lg tracking-tight bg-gradient-to-r from-primary to-blue-600 bg-clip-text text-transparent">
                OLI
              </h1>
              <p className="text-[10px] text-slate-400 -mt-0.5">Overlay Legal Intelligence</p>
            </div>
          </div>
          
          <div className="flex items-center gap-2">
            <div className="flex items-center gap-1.5 px-3 py-1.5 bg-emerald-50 text-emerald-700 rounded-full text-xs font-medium border border-emerald-100 shadow-sm">
              <div className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
              Active
            </div>
            <button 
              onClick={() => setIsSettingsOpen(true)}
              className="p-2 hover:bg-slate-100 rounded-full transition-colors text-slate-500"
              title="Display Settings"
            >
              <Settings className="w-5 h-5" />
            </button>
          </div>
        </div>
        <ModeToggle mode={analysisMode} onChange={setAnalysisMode} />
      </header>

      <main className="p-4 space-y-5 pb-24">
        {/* Initial State */}
        {!result && !loading && !error && (
          <div className="space-y-4">
            <div className="bg-white rounded-2xl p-8 shadow-sm border border-slate-100 flex flex-col items-center text-center">
              <div className="relative mb-4">
                <div className="absolute inset-0 bg-primary/5 blur-2xl rounded-full"></div>
                <div className="relative bg-slate-50 p-6 rounded-2xl border border-slate-100">
                  <FileText className="w-12 h-12 text-slate-300" />
                </div>
              </div>
              <h2 className="text-lg font-semibold text-slate-700 mb-1">Ready to analyze</h2>
              <p className="text-sm text-slate-400 max-w-[200px]">
                Click the button below to scan the active page
              </p>
            </div>
            
            {/* Detected PDFs */}
            {detectedPDFs.length > 0 && (
              <div className="bg-white rounded-2xl p-4 shadow-sm border border-slate-100">
                <h3 className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-3 flex items-center gap-2">
                  <FileType className="w-3 h-3" />
                  Detected PDFs ({detectedPDFs.length})
                </h3>
                <div className="space-y-2">
                  {detectedPDFs.map((pdf, i) => (
                    <button
                      key={i}
                      onClick={() => analyzePDF(pdf)}
                      className="w-full flex items-center gap-3 p-3 rounded-xl bg-slate-50 hover:bg-violet-50 border border-slate-100 hover:border-violet-200 transition-all text-left group"
                    >
                      <div className="p-2 rounded-lg bg-violet-100 text-violet-600">
                        <FileType className="w-4 h-4" />
                      </div>
                      <div className="flex-1 min-w-0">
                        <p className="text-sm text-slate-700 truncate group-hover:text-violet-700">
                          {pdf.url.split('/').pop() || 'PDF Document'}
                        </p>
                        <p className="text-xs text-slate-400">{pdf.type}</p>
                      </div>
                      <Brain className="w-4 h-4 text-slate-300 group-hover:text-violet-500" />
                    </button>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

        {/* Error State */}
        {error && (
          <div className="bg-red-50 rounded-2xl p-6 border border-red-100 flex items-start gap-3">
            <div className="bg-red-100 p-2 rounded-lg">
              <AlertTriangle className="w-5 h-5 text-red-600" />
            </div>
            <div>
              <h3 className="font-semibold text-red-700 mb-1">Analysis Error</h3>
              <p className="text-sm text-red-600">{error}</p>
            </div>
          </div>
        )}

        {/* Results */}
        {result && (
          <>
            {/* New Analysis Button */}
            <button
              onClick={resetAnalysis}
              className="w-full flex items-center justify-center gap-2 py-2 px-4 rounded-xl bg-slate-100 hover:bg-slate-200 text-slate-600 text-sm font-medium transition-all mb-3"
            >
              <RotateCcw className="w-4 h-4" />
              New Analysis
            </button>
            
            {/* Score Cards */}
            <div className="grid grid-cols-2 gap-3">
              {/* Risk Score */}
              <div className="bg-white rounded-2xl p-4 shadow-sm border border-slate-100 flex flex-col items-center animate-in fade-in slide-in-from-left duration-500">
                <CircularProgress 
                  value={result.risk_score} 
                  color={getRiskColor(result.risk_score)}
                  label={`${result.risk_score}`}
                  sublabel="Risk"
                  size={90}
                  strokeWidth={6}
                />
                <p className="text-xs text-slate-400 mt-2">Risk Score</p>
              </div>

              {/* Completeness Score */}
              <div className="bg-white rounded-2xl p-4 shadow-sm border border-slate-100 flex flex-col items-center animate-in fade-in slide-in-from-right duration-500">
                <CircularProgress 
                  value={result.completeness_score}
                  color="primary"
                  label={`${result.completeness_score}%`}
                  sublabel="Complete"
                  size={90}
                  strokeWidth={6}
                />
                <p className="text-xs text-slate-400 mt-2">Completeness</p>
              </div>
            </div>

            {/* Overall Status */}
            <div className={cn(
              "rounded-2xl p-5 shadow-sm border flex items-center gap-4 animate-in fade-in slide-in-from-bottom duration-500",
              result.overall_status === 'CRITIQUE' && "bg-gradient-to-r from-red-50 to-white border-red-100",
              result.overall_status === 'AVERTISSEMENT' && "bg-gradient-to-r from-amber-50 to-white border-amber-100",
              result.overall_status === 'CONFORME' && "bg-gradient-to-r from-emerald-50 to-white border-emerald-100"
            )}>
              <div className={cn(
                "p-3 rounded-xl",
                result.overall_status === 'CRITIQUE' && "bg-red-100",
                result.overall_status === 'AVERTISSEMENT' && "bg-amber-100",
                result.overall_status === 'CONFORME' && "bg-emerald-100"
              )}>
                {result.overall_status === 'CRITIQUE' && <ShieldX className="w-6 h-6 text-red-600" />}
                {result.overall_status === 'AVERTISSEMENT' && <ShieldAlert className="w-6 h-6 text-amber-600" />}
                {result.overall_status === 'CONFORME' && <ShieldCheck className="w-6 h-6 text-emerald-600" />}
              </div>
              <div className="flex-1">
                <StatusBadge status={result.overall_status} />
                <p className="text-sm text-slate-600 mt-2">{result.summary}</p>
              </div>
            </div>

            {/* Compliance Checks */}
            <div className="space-y-3">
              <h3 className="text-xs font-semibold text-slate-500 uppercase tracking-wider px-1 flex items-center gap-2">
                <Scale className="w-3 h-3" />
                Compliance Checks ({result.checks.length})
              </h3>
              
              {result.checks.map((check, index) => (
                <AlertCard key={check.id} check={check} index={index} onScrollTo={scrollToHighlight} isPdfMode={!!currentPdfUrl} />
              ))}
            </div>

            {/* Sources from RAG */}
            {result.sources && result.sources.length > 0 && (
              <SourcesList sources={result.sources} />
            )}

            {/* Analysis Mode & Privacy Notice */}
            <div className="space-y-2">
              {result.analysis_mode && (
                <div className={cn(
                  "p-3 rounded-xl border text-xs flex items-center gap-2",
                  result.analysis_mode === 'llm' 
                    ? "bg-violet-50 border-violet-100 text-violet-600"
                    : "bg-slate-50 border-slate-100 text-slate-500"
                )}>
                  {result.analysis_mode === 'llm' ? (
                    <>
                      <Brain className="w-3.5 h-3.5" />
                      <span>AI analysis with RAG - Legal context retrieved</span>
                    </>
                  ) : (
                    <>
                      <Zap className="w-3.5 h-3.5" />
                      <span>Fast rule-based analysis</span>
                    </>
                  )}
                </div>
              )}
              <div className="p-3 rounded-xl bg-slate-50 border border-slate-100 text-xs text-slate-500 flex items-center gap-2">
                <Shield className="w-3.5 h-3.5 text-primary" />
                <span>Data anonymized before processing</span>
              </div>
            </div>
          </>
        )}
      </main>

      {/* Floating Action Button */}
      <div className="fixed bottom-0 left-0 right-0 p-4 bg-gradient-to-t from-slate-100 via-slate-100 to-transparent">
        {loading && loadingMessage && (
          <div className="mb-3 text-center">
            <p className="text-sm text-slate-500 animate-pulse">{loadingMessage}</p>
          </div>
        )}
        <button
          onClick={scanPage}
          disabled={loading}
          className={cn(
            "w-full font-semibold py-4 px-6 rounded-2xl shadow-lg transition-all",
            "flex items-center justify-center gap-2",
            "disabled:opacity-70 disabled:cursor-not-allowed",
            "active:scale-[0.98]",
            loading 
              ? "bg-slate-200 text-slate-500" 
              : analysisMode === 'llm'
                ? "bg-gradient-to-r from-violet-600 to-purple-600 text-white hover:shadow-xl hover:shadow-violet-500/25"
                : "bg-gradient-to-r from-primary to-blue-600 text-white hover:shadow-xl hover:shadow-primary/25"
          )}
        >
          {loading ? (
            <>
              <Loader2 className="w-5 h-5 animate-spin" />
              {analysisMode === 'llm' ? 'AI Analysis...' : 'Analyzing...'}
            </>
          ) : (
            <>
              {analysisMode === 'llm' ? <Brain className="w-5 h-5" /> : <Shield className="w-5 h-5" />}
              {analysisMode === 'llm' ? 'Analyze with AI' : 'Scan Page'}
            </>
          )}
        </button>
      </div>
      
    </div>
  )
}

export default App
