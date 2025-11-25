import { useState } from 'react'
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
  ShieldX
} from 'lucide-react'
import { cn } from './lib/utils'

// Types matching the new backend response
interface ComplianceCheck {
  id: string;
  name: string;
  status: 'CONFORME' | 'AVERTISSEMENT' | 'CRITIQUE';
  message: string;
  reference: string;
  url: string;
  recommendation: string;
  highlight_text: string | null;
}

interface AnalysisResult {
  overall_status: 'CONFORME' | 'AVERTISSEMENT' | 'CRITIQUE';
  risk_score: number;
  completeness_score: number;
  checks: ComplianceCheck[];
  anonymized_text: string;
  summary: string;
}

// Status configuration
const statusConfig = {
  CONFORME: {
    color: 'emerald',
    bg: 'bg-emerald-50',
    border: 'border-emerald-200',
    text: 'text-emerald-600',
    icon: CheckCircle,
    label: 'Conforme'
  },
  AVERTISSEMENT: {
    color: 'amber',
    bg: 'bg-amber-50',
    border: 'border-amber-200',
    text: 'text-amber-600',
    icon: AlertCircle,
    label: 'Avertissement'
  },
  CRITIQUE: {
    color: 'red',
    bg: 'bg-red-50',
    border: 'border-red-200',
    text: 'text-red-600',
    icon: AlertTriangle,
    label: 'Critique'
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
          stroke="#E5E7EB"
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
        {label && <span className="text-2xl font-bold text-slate-900">{label}</span>}
        {sublabel && <span className="text-xs text-slate-500">{sublabel}</span>}
      </div>
    </div>
  );
}

// Alert Card Component
function AlertCard({ check, index }: { check: ComplianceCheck; index: number }) {
  const config = statusConfig[check.status];
  const Icon = checkIcons[check.id] || Scale;
  
  return (
    <div 
      className={cn(
        "p-4 rounded-xl border shadow-sm transition-all hover:shadow-md",
        "animate-in fade-in slide-in-from-bottom-4",
        "bg-white",
        check.status === 'CRITIQUE' && "border-l-4 border-l-red-500 border-red-100",
        check.status === 'AVERTISSEMENT' && "border-l-4 border-l-amber-500 border-amber-100",
        check.status === 'CONFORME' && "border-l-4 border-l-emerald-500 border-emerald-100"
      )}
      style={{ animationDelay: `${index * 100}ms` }}
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
            <h4 className="font-medium text-slate-900 text-sm">{check.name}</h4>
            <span className={cn(
              "px-2 py-0.5 rounded-full text-xs font-medium",
              config.bg, config.text
            )}>
              {config.label}
            </span>
          </div>
          <p className="text-sm text-slate-600 mb-2">{check.message}</p>
          {check.status !== 'CONFORME' && (
            <p className="text-xs text-slate-500 italic flex items-center gap-1">
              <ChevronRight className="w-3 h-3" />
              {check.recommendation}
            </p>
          )}
        </div>
      </div>
      
      <div className="mt-3 pt-3 border-t border-slate-100 flex items-center justify-between">
        <span className="text-xs text-slate-400 bg-slate-50 px-2 py-1 rounded font-mono">
          {check.reference}
        </span>
        <a
          href={check.url}
          target="_blank"
          rel="noopener noreferrer"
          className="text-xs font-medium text-primary hover:text-blue-700 flex items-center gap-1 transition-colors"
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

function App() {
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<AnalysisResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  const scanPage = async () => {
    setLoading(true);
    setResult(null);
    setError(null);

    try {
      // 1. Get active tab
      const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
      if (!tab.id) {
        throw new Error("Aucun onglet actif trouvé");
      }

      // 2. Extract page text
      const injectionResults = await chrome.scripting.executeScript({
        target: { tabId: tab.id },
        func: () => document.body.innerText,
      });

      const pageText = injectionResults[0].result;

      // 3. Send to Backend
      const response = await fetch('http://localhost:8001/analyze', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          text: pageText,
          url: tab.url 
        }),
      });

      if (!response.ok) {
        throw new Error(`Erreur serveur: ${response.status}`);
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
      setError(err instanceof Error ? err.message : "Erreur inconnue");
    } finally {
      setLoading(false);
    }
  };

  // Determine risk color for circular progress
  const getRiskColor = (score: number): string => {
    if (score >= 60) return 'red';
    if (score >= 30) return 'amber';
    return 'emerald';
  };

  return (
    <div className="w-full min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 text-slate-900 font-sans">
      {/* Header with Glass Effect */}
      <header className="bg-white/80 backdrop-blur-md border-b border-slate-200/50 p-4 flex items-center justify-between sticky top-0 z-10">
        <div className="flex items-center gap-3">
          <div className="relative">
            <div className="absolute inset-0 bg-primary/20 blur-lg rounded-xl"></div>
            <div className="relative bg-gradient-to-br from-primary to-blue-700 text-white p-2 rounded-xl shadow-lg">
              <Shield className="w-5 h-5" />
            </div>
          </div>
          <div>
            <h1 className="font-bold text-lg tracking-tight bg-gradient-to-r from-primary to-blue-600 bg-clip-text text-transparent">
              OLI
            </h1>
            <p className="text-[10px] text-slate-400 -mt-0.5">Overlay Legal Intelligence</p>
          </div>
        </div>
        <div className="flex items-center gap-1.5 px-3 py-1.5 bg-emerald-50 text-emerald-700 rounded-full text-xs font-medium border border-emerald-100 shadow-sm">
          <div className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
          Actif
        </div>
      </header>

      <main className="p-4 space-y-5 pb-24">
        {/* Initial State */}
        {!result && !loading && !error && (
          <div className="bg-white rounded-2xl p-8 shadow-sm border border-slate-100 flex flex-col items-center text-center">
            <div className="relative mb-4">
              <div className="absolute inset-0 bg-primary/5 blur-2xl rounded-full"></div>
              <div className="relative bg-slate-50 p-6 rounded-2xl border border-slate-100">
                <FileText className="w-12 h-12 text-slate-300" />
              </div>
            </div>
            <h2 className="text-lg font-semibold text-slate-700 mb-1">Prêt à analyser</h2>
            <p className="text-sm text-slate-400 max-w-[200px]">
              Cliquez sur le bouton ci-dessous pour scanner la page active
            </p>
          </div>
        )}

        {/* Error State */}
        {error && (
          <div className="bg-red-50 rounded-2xl p-6 border border-red-100 flex items-start gap-3">
            <div className="bg-red-100 p-2 rounded-lg">
              <AlertTriangle className="w-5 h-5 text-red-600" />
            </div>
            <div>
              <h3 className="font-semibold text-red-700 mb-1">Erreur d'analyse</h3>
              <p className="text-sm text-red-600">{error}</p>
            </div>
          </div>
        )}

        {/* Results */}
        {result && (
          <>
            {/* Score Cards */}
            <div className="grid grid-cols-2 gap-3">
              {/* Risk Score */}
              <div className="bg-white rounded-2xl p-4 shadow-sm border border-slate-100 flex flex-col items-center animate-in fade-in slide-in-from-left duration-500">
                <CircularProgress 
                  value={result.risk_score} 
                  color={getRiskColor(result.risk_score)}
                  label={`${result.risk_score}`}
                  sublabel="Risque"
                  size={90}
                  strokeWidth={6}
                />
                <p className="text-xs text-slate-400 mt-2">Score de risque</p>
              </div>

              {/* Completeness Score */}
              <div className="bg-white rounded-2xl p-4 shadow-sm border border-slate-100 flex flex-col items-center animate-in fade-in slide-in-from-right duration-500">
                <CircularProgress 
                  value={result.completeness_score}
                  color="primary"
                  label={`${result.completeness_score}%`}
                  sublabel="Complet"
                  size={90}
                  strokeWidth={6}
                />
                <p className="text-xs text-slate-400 mt-2">Complétude</p>
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
                Contrôles de conformité ({result.checks.length})
              </h3>
              
              {result.checks.map((check, index) => (
                <AlertCard key={check.id} check={check} index={index} />
              ))}
            </div>

            {/* Privacy Notice */}
            <div className="p-3 rounded-xl bg-slate-50 border border-slate-100 text-xs text-slate-500 flex items-center gap-2">
              <Shield className="w-3.5 h-3.5 text-primary" />
              <span>Données anonymisées avant traitement IA (Presidio)</span>
            </div>
          </>
        )}
      </main>

      {/* Floating Action Button */}
      <div className="fixed bottom-0 left-0 right-0 p-4 bg-gradient-to-t from-slate-100 via-slate-100 to-transparent">
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
              : "bg-gradient-to-r from-primary to-blue-600 text-white hover:shadow-xl hover:shadow-primary/25"
          )}
        >
          {loading ? (
            <>
              <Loader2 className="w-5 h-5 animate-spin" />
              Analyse en cours...
            </>
          ) : (
            <>
              <Shield className="w-5 h-5" />
              Scanner la page
            </>
          )}
        </button>
      </div>
    </div>
  )
}

export default App
