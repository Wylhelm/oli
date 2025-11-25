// OLI Content Script - Enhanced DOM Injection
console.log("🛡️ OLI Content Script Loaded");

// Track highlighted elements for cleanup
let highlightedElements = [];
let tooltipElement = null;

// Status colors
const STATUS_COLORS = {
    CRITIQUE: {
        border: '#EF4444',
        bg: 'rgba(239, 68, 68, 0.1)',
        text: '#DC2626',
        icon: '🔴'
    },
    AVERTISSEMENT: {
        border: '#F59E0B',
        bg: 'rgba(245, 158, 11, 0.1)',
        text: '#D97706',
        icon: '🟡'
    },
    CONFORME: {
        border: '#10B981',
        bg: 'rgba(16, 185, 129, 0.1)',
        text: '#059669',
        icon: '🟢'
    }
};

// Create tooltip element
function createTooltip() {
    if (tooltipElement) return;
    
    tooltipElement = document.createElement('div');
    tooltipElement.id = 'oli-tooltip';
    tooltipElement.style.cssText = `
        position: fixed;
        z-index: 999999;
        padding: 12px 16px;
        background: linear-gradient(135deg, #1E293B 0%, #0F172A 100%);
        color: white;
        border-radius: 12px;
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
        font-size: 13px;
        line-height: 1.5;
        max-width: 320px;
        box-shadow: 0 20px 40px rgba(0, 0, 0, 0.3), 0 0 0 1px rgba(255, 255, 255, 0.1);
        pointer-events: none;
        opacity: 0;
        transform: translateY(8px);
        transition: opacity 0.2s ease, transform 0.2s ease;
        backdrop-filter: blur(8px);
    `;
    document.body.appendChild(tooltipElement);
}

// Show tooltip
function showTooltip(element, content, status) {
    createTooltip();
    
    const colors = STATUS_COLORS[status] || STATUS_COLORS.CRITIQUE;
    const rect = element.getBoundingClientRect();
    
    tooltipElement.innerHTML = `
        <div style="display: flex; align-items: flex-start; gap: 10px;">
            <span style="font-size: 18px; line-height: 1;">${colors.icon}</span>
            <div>
                <div style="font-weight: 600; margin-bottom: 4px; color: ${status === 'CRITIQUE' ? '#FCA5A5' : status === 'AVERTISSEMENT' ? '#FCD34D' : '#6EE7B7'};">
                    ${status === 'CRITIQUE' ? 'Alerte Critique' : status === 'AVERTISSEMENT' ? 'Avertissement' : 'Conforme'}
                </div>
                <div style="color: #CBD5E1;">${content}</div>
            </div>
        </div>
        <div style="
            position: absolute;
            bottom: -6px;
            left: 20px;
            width: 12px;
            height: 12px;
            background: #0F172A;
            transform: rotate(45deg);
            border-radius: 2px;
        "></div>
    `;
    
    // Position tooltip above the element
    const tooltipRect = tooltipElement.getBoundingClientRect();
    let left = rect.left + (rect.width / 2) - 30;
    let top = rect.top - tooltipRect.height - 12 + window.scrollY;
    
    // Ensure tooltip stays within viewport
    if (left < 10) left = 10;
    if (left + 320 > window.innerWidth) left = window.innerWidth - 330;
    if (top < 10) {
        top = rect.bottom + 12 + window.scrollY;
        // Flip arrow
        tooltipElement.querySelector('div:last-child').style.cssText = `
            position: absolute;
            top: -6px;
            left: 20px;
            width: 12px;
            height: 12px;
            background: #1E293B;
            transform: rotate(45deg);
            border-radius: 2px;
        `;
    }
    
    tooltipElement.style.left = `${left}px`;
    tooltipElement.style.top = `${top}px`;
    tooltipElement.style.opacity = '1';
    tooltipElement.style.transform = 'translateY(0)';
}

// Hide tooltip
function hideTooltip() {
    if (tooltipElement) {
        tooltipElement.style.opacity = '0';
        tooltipElement.style.transform = 'translateY(8px)';
    }
}

// Clean up previous highlights
function cleanupHighlights() {
    highlightedElements.forEach(el => {
        if (el.parentNode && el.dataset.oliOriginal) {
            const textNode = document.createTextNode(el.dataset.oliOriginal);
            el.parentNode.replaceChild(textNode, el);
        }
    });
    highlightedElements = [];
}

// Highlight text in the page
function highlightText(searchText, status, message) {
    const colors = STATUS_COLORS[status] || STATUS_COLORS.CRITIQUE;
    const walker = document.createTreeWalker(
        document.body, 
        NodeFilter.SHOW_TEXT, 
        null, 
        false
    );
    
    const nodesToProcess = [];
    let node;
    
    while (node = walker.nextNode()) {
        if (node.nodeValue.includes(searchText)) {
            nodesToProcess.push(node);
        }
    }
    
    nodesToProcess.forEach(textNode => {
        const span = document.createElement('span');
        span.className = 'oli-highlight';
        span.dataset.oliOriginal = textNode.nodeValue;
        span.dataset.oliStatus = status;
        span.dataset.oliMessage = message || `Élément signalé par OLI`;
        
        span.style.cssText = `
            display: inline;
            position: relative;
            border: 2px solid ${colors.border};
            background: ${colors.bg};
            border-radius: 4px;
            padding: 2px 4px;
            margin: 0 2px;
            transition: all 0.2s ease;
        `;
        
        // Create the highlighted content
        const parts = textNode.nodeValue.split(searchText);
        span.innerHTML = parts.join(`<mark style="
            background: ${colors.bg};
            color: ${colors.text};
            font-weight: 600;
            padding: 0;
            border-radius: 2px;
        ">${searchText}</mark>`);
        
        // Add icon badge
        const badge = document.createElement('span');
        badge.className = 'oli-badge';
        badge.style.cssText = `
            position: absolute;
            top: -10px;
            right: -10px;
            background: ${colors.border};
            color: white;
            font-size: 10px;
            width: 20px;
            height: 20px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: bold;
            box-shadow: 0 2px 8px ${colors.border}40;
            z-index: 1000;
        `;
        badge.textContent = status === 'CRITIQUE' ? '!' : status === 'AVERTISSEMENT' ? '?' : '✓';
        span.appendChild(badge);
        
        // Add hover events
        span.addEventListener('mouseenter', function() {
            this.style.transform = 'scale(1.02)';
            this.style.boxShadow = `0 4px 12px ${colors.border}40`;
            showTooltip(this, this.dataset.oliMessage, this.dataset.oliStatus);
        });
        
        span.addEventListener('mouseleave', function() {
            this.style.transform = 'scale(1)';
            this.style.boxShadow = 'none';
            hideTooltip();
        });
        
        textNode.parentNode.replaceChild(span, textNode);
        highlightedElements.push(span);
    });
}

// Add floating indicator
function addFloatingIndicator(overallStatus) {
    // Remove existing indicator
    const existing = document.getElementById('oli-indicator');
    if (existing) existing.remove();
    
    const colors = STATUS_COLORS[overallStatus] || STATUS_COLORS.CRITIQUE;
    
    const indicator = document.createElement('div');
    indicator.id = 'oli-indicator';
    indicator.style.cssText = `
        position: fixed;
        bottom: 20px;
        right: 20px;
        z-index: 999998;
        padding: 12px 20px;
        background: linear-gradient(135deg, ${colors.border} 0%, ${colors.text} 100%);
        color: white;
        border-radius: 50px;
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
        font-size: 13px;
        font-weight: 600;
        display: flex;
        align-items: center;
        gap: 8px;
        box-shadow: 0 8px 24px ${colors.border}50;
        cursor: pointer;
        transition: all 0.3s ease;
        animation: oli-slide-in 0.5s ease-out;
    `;
    
    indicator.innerHTML = `
        <span style="font-size: 16px;">🛡️</span>
        <span>OLI: ${overallStatus === 'CRITIQUE' ? 'Alertes détectées' : overallStatus === 'AVERTISSEMENT' ? 'Points d\'attention' : 'Conforme'}</span>
    `;
    
    // Add animation keyframes
    if (!document.getElementById('oli-animations')) {
        const style = document.createElement('style');
        style.id = 'oli-animations';
        style.textContent = `
            @keyframes oli-slide-in {
                from {
                    opacity: 0;
                    transform: translateY(20px);
                }
                to {
                    opacity: 1;
                    transform: translateY(0);
                }
            }
            @keyframes oli-pulse {
                0%, 100% {
                    box-shadow: 0 8px 24px ${colors.border}50;
                }
                50% {
                    box-shadow: 0 8px 32px ${colors.border}80;
                }
            }
        `;
        document.head.appendChild(style);
    }
    
    indicator.addEventListener('mouseenter', function() {
        this.style.transform = 'scale(1.05)';
    });
    
    indicator.addEventListener('mouseleave', function() {
        this.style.transform = 'scale(1)';
    });
    
    document.body.appendChild(indicator);
    
    // Add pulse animation for critical status
    if (overallStatus === 'CRITIQUE') {
        indicator.style.animation = 'oli-slide-in 0.5s ease-out, oli-pulse 2s infinite';
    }
}

// Listen for messages from the side panel
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    console.log("📨 OLI received message:", request.action);
    
    if (request.action === "SCAN_PAGE") {
        const text = document.body.innerText;
        sendResponse({ text: text });
    } 
    else if (request.action === "HIGHLIGHT_RISK") {
        // Legacy support for single highlight
        cleanupHighlights();
        highlightText("5 000 $", request.data.status || 'CRITIQUE', request.data.summary);
        addFloatingIndicator(request.data.status || 'CRITIQUE');
        sendResponse({ status: "Highlighted" });
    }
    else if (request.action === "HIGHLIGHT_RISKS") {
        // New multi-highlight support
        cleanupHighlights();
        
        const { highlights, overallStatus } = request.data;
        
        if (highlights && highlights.length > 0) {
            highlights.forEach(h => {
                highlightText(h.text, h.status, `Élément à risque détecté`);
            });
        }
        
        addFloatingIndicator(overallStatus);
        sendResponse({ status: "Highlighted", count: highlights?.length || 0 });
    }
    else if (request.action === "CLEAR_HIGHLIGHTS") {
        cleanupHighlights();
        const indicator = document.getElementById('oli-indicator');
        if (indicator) indicator.remove();
        sendResponse({ status: "Cleared" });
    }
    
    return true; // Keep message channel open for async response
});

// Initial setup
createTooltip();
console.log("✅ OLI Content Script Ready");
