// OLI Content Script - Enhanced DOM Injection
// Wrapped in IIFE to prevent re-declaration errors on multiple injections
(function() {
    // Check if already loaded
    if (window.__OLI_CONTENT_LOADED__) {
        console.log("🛡️ OLI Content Script already loaded, skipping...");
        return;
    }
    window.__OLI_CONTENT_LOADED__ = true;
    
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
        if (!element) {
            console.warn("[OLI] showTooltip called with no element");
            return;
        }
        
        createTooltip();
        
        const colors = STATUS_COLORS[status] || STATUS_COLORS.CRITIQUE;
        const rect = element.getBoundingClientRect();
        
        // Validate rect - if element is not visible or has no size, don't show tooltip
        if (!rect || rect.width === 0 || rect.height === 0) {
            console.warn("[OLI] Element has invalid bounding rect:", rect);
            return;
        }
        
        console.log("[OLI] showTooltip - element:", element.tagName, "rect:", rect);
        
        tooltipElement.innerHTML = `
            <div style="display: flex; align-items: flex-start; gap: 10px;">
                <span style="font-size: 18px; line-height: 1;">${colors.icon}</span>
                <div>
                    <div style="font-weight: 600; margin-bottom: 4px; color: ${status === 'CRITIQUE' ? '#FCA5A5' : status === 'AVERTISSEMENT' ? '#FCD34D' : '#6EE7B7'};">
                        ${status === 'CRITIQUE' ? 'Critical Alert' : status === 'AVERTISSEMENT' ? 'Warning' : 'Compliant'}
                    </div>
                    <div style="color: #CBD5E1;">${content}</div>
                </div>
            </div>
            <div class="oli-tooltip-arrow" style="
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
        
        // Position tooltip - use fixed positioning relative to viewport
        // getBoundingClientRect() already gives viewport-relative coordinates
        
        // First render to get tooltip dimensions
        tooltipElement.style.visibility = 'hidden';
        tooltipElement.style.opacity = '0';
        tooltipElement.style.display = 'block';
        const tooltipHeight = tooltipElement.offsetHeight;
        const tooltipWidth = tooltipElement.offsetWidth || 320;
        
        // Calculate position - try to place above element first
        let left = rect.left + (rect.width / 2) - (tooltipWidth / 2);
        let top = rect.top - tooltipHeight - 12;
        let arrowOnTop = false;
        
        // If tooltip would go above viewport, place below element
        if (top < 10) {
            top = rect.bottom + 12;
            arrowOnTop = true;
        }
        
        // Keep tooltip within horizontal bounds
        if (left < 10) left = 10;
        if (left + tooltipWidth > window.innerWidth - 10) {
            left = window.innerWidth - tooltipWidth - 10;
        }
        
        // Calculate arrow position to point to the element center
        const arrowLeft = Math.max(15, Math.min(rect.left + rect.width/2 - left - 6, tooltipWidth - 25));
        
        // Update arrow position
        const arrow = tooltipElement.querySelector('.oli-tooltip-arrow');
        if (arrow) {
            if (arrowOnTop) {
                arrow.style.cssText = `
                    position: absolute;
                    top: -6px;
                    left: ${arrowLeft}px;
                    width: 12px;
                    height: 12px;
                    background: #1E293B;
                    transform: rotate(45deg);
                    border-radius: 2px;
                `;
            } else {
                arrow.style.cssText = `
                    position: absolute;
                    bottom: -6px;
                    left: ${arrowLeft}px;
                    width: 12px;
                    height: 12px;
                    background: #0F172A;
                    transform: rotate(45deg);
                    border-radius: 2px;
                `;
            }
        }
        
        tooltipElement.style.left = `${left}px`;
        tooltipElement.style.top = `${top}px`;
        tooltipElement.style.visibility = 'visible';
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
            } else {
                // Restore existing elements
                el.classList.remove('oli-highlight', 'oli-focus-highlight');
                // Restore original styles if saved
                if (el.dataset.oliOriginalStyle !== undefined) {
                    el.setAttribute('style', el.dataset.oliOriginalStyle);
                } else {
                    el.removeAttribute('style');
                }
                delete el.dataset.oliStatus;
                delete el.dataset.oliMessage;
                delete el.dataset.oliOriginalStyle;
                delete el.dataset.oliBadgeCreated;
                delete el.dataset.oliMouseEnter;
                delete el.dataset.oliMouseLeave;
            }
        });
        
        // Remove all badges (including fixed position badges)
        document.querySelectorAll('.oli-badge').forEach(b => {
            // Clean up scroll listeners if attached
            if (b.dataset.cleanup === 'scroll-listener') {
                // Note: we can't easily remove specific scroll listeners, but they'll be cleaned up when badge is removed
                // In production, consider storing listener references for proper cleanup
            }
            b.remove();
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
            span.dataset.oliMessage = message || `Element flagged by OLI`;
            
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
            <span>OLI: ${overallStatus === 'CRITIQUE' ? 'Alerts detected' : overallStatus === 'AVERTISSEMENT' ? 'Points of attention' : 'Compliant'}</span>
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

    // Extract form data from the page
    function extractFormData() {
        const formData = [];
        const inputs = document.querySelectorAll('input, select, textarea');
        
        inputs.forEach(input => {
            // Skip utility inputs
            if (input.type === 'hidden' || input.type === 'submit' || input.type === 'button' || 
                input.type === 'image' || input.type === 'file') return;
            
            // Skip empty inputs
            if (!input.value || input.value.trim() === '') return;
            
            // Find label
            let label = '';
            if (input.id) {
                const labelEl = document.querySelector(`label[for="${input.id}"]`);
                if (labelEl) label = labelEl.textContent.trim().replace(/\*$/, '').trim();
            }
            if (!label && input.closest('label')) {
                label = input.closest('label').textContent.trim().replace(/\*$/, '').trim();
            }
            if (!label) {
                const formGroup = input.closest('.form-group, .field, .col');
                if (formGroup) {
                    const labelEl = formGroup.querySelector('label');
                    if (labelEl) label = labelEl.textContent.trim().replace(/\*$/, '').trim();
                }
            }
            
            // Use name or id as fallback label
            if (!label) {
                label = input.name || input.id || input.placeholder || 'Unknown Field';
            }
            
            formData.push({
                label: label,
                value: input.value,
                name: input.name || input.id
            });
        });
        
        return formData;
    }

    // Extract key value from text (e.g., "15 000 $" from "Solde moyen (6 mois) : 15 000 $")
    function extractKeyValue(text) {
        // Try to extract monetary values
        const moneyMatch = text.match(/[\d\s]+\s*\$/);
        if (moneyMatch) {
            return moneyMatch[0].trim();
        }
        // Try to extract dates
        const dateMatch = text.match(/\d{4}-\d{2}-\d{2}/);
        if (dateMatch) {
            return dateMatch[0];
        }
        // Return last part after colon
        if (text.includes(':')) {
            return text.split(':').pop().trim();
        }
        return text;
    }

    // Find the best matching element for a search text
    function findBestMatchElement(searchText, keyValue) {
        console.log("[OLI Content] findBestMatchElement - searchText:", searchText, "keyValue:", keyValue);
        
        // Try to extract Label from "Field [Label]: Value" format
        let targetLabel = null;
        const labelMatch = searchText.match(/Field \[(.*?)\]:/);
        if (labelMatch && labelMatch[1]) {
            targetLabel = labelMatch[1].trim();
            console.log("[OLI Content] Target label extracted:", targetLabel);
        }

        // Priority 0: Look for input values (Direct match in form fields)
        const inputs = document.querySelectorAll('input, select, textarea');
        let bestInput = null;
        let bestInputScore = 0;
        
        for (const input of inputs) {
            // Skip utility inputs
            if (input.type === 'hidden' || input.type === 'submit' || input.type === 'button' || input.type === 'image') continue;
            
            let matchScore = 0;
            
            // Check value match - normalize values for comparison
            const normalizedValue = input.value.replace(/\s+/g, ' ').trim();
            const normalizedKeyValue = keyValue.replace(/\s+/g, ' ').trim();
            
            if (normalizedValue && (
                normalizedValue.includes(normalizedKeyValue) || 
                normalizedKeyValue.includes(normalizedValue) ||
                normalizedValue === normalizedKeyValue
            )) {
                matchScore += 10; // Strong value match
                console.log("[OLI Content] Value match for input:", input.name || input.id, "value:", input.value);
            }
            
            // Check label match if available
            if (targetLabel) {
                // Check name/id - case insensitive partial match
                const nameLower = (input.name || '').toLowerCase();
                const idLower = (input.id || '').toLowerCase();
                const labelLower = targetLabel.toLowerCase();
                
                if (nameLower.includes(labelLower) || labelLower.includes(nameLower) ||
                    idLower.includes(labelLower) || labelLower.includes(idLower)) {
                    matchScore += 3;
                }
                
                // Check associated label
                let labelText = '';
                if (input.id) {
                    const labelEl = document.querySelector(`label[for="${input.id}"]`);
                    if (labelEl) labelText = labelEl.innerText.trim();
                }
                if (!labelText && input.closest('label')) {
                    labelText = input.closest('label').innerText.trim();
                }
                
                // Also check parent .form-group or .field for label
                if (!labelText) {
                    const formGroup = input.closest('.form-group, .field, .col');
                    if (formGroup) {
                        const label = formGroup.querySelector('label');
                        if (label) labelText = label.innerText.trim();
                    }
                }
                
                if (labelText) {
                    const labelTextLower = labelText.toLowerCase();
                    if (labelTextLower.includes(labelLower) || labelLower.includes(labelTextLower)) {
                        matchScore += 5; // Strong match on label
                        console.log("[OLI Content] Label match:", labelText, "for input:", input.name || input.id);
                    }
                }
            }

            if (matchScore > bestInputScore) {
                bestInputScore = matchScore;
                bestInput = input;
            }
        }
        
        if (bestInputScore >= 3) { // At least a decent match
            console.log("[OLI Content] Found best input match with score:", bestInputScore);
            return { element: bestInput, type: 'input' };
        }

        // Priority 1: Look for value elements in fields (common in static forms)
        const fieldContainers = document.querySelectorAll('.field, .form-group, tr, [class*="row"], [class*="field"]');
        for (const container of fieldContainers) {
            const valueEl = container.querySelector('.value, .form-control, td:last-child, [class*="value"]');
            if (valueEl && valueEl.textContent.includes(keyValue)) {
                console.log("[OLI Content] Found in field value element");
                return { element: valueEl, type: 'value' };
            }
        }
        
        // Priority 2: Look for highlighted classes (danger, warning)
        const highlightedEls = document.querySelectorAll('.highlight-danger, .highlight-warning, .highlight-info, .highlight-success, [class*="highlight"]');
        for (const el of highlightedEls) {
            if (el.textContent.includes(keyValue)) {
                console.log("[OLI Content] Found in highlighted element");
                return { element: el, type: 'highlighted' };
            }
        }
        
        // Priority 3: Look in table cells
        const tableCells = document.querySelectorAll('td, th');
        for (const cell of tableCells) {
            if (cell.textContent.includes(keyValue)) {
                console.log("[OLI Content] Found in table cell");
                return { element: cell, type: 'table' };
            }
        }
        
        // Priority 4: Look for amount/money displays
        const amountEls = document.querySelectorAll('.amount, [class*="amount"], [class*="price"], [class*="balance"]');
        for (const el of amountEls) {
            if (el.textContent.includes(keyValue)) {
                console.log("[OLI Content] Found in amount element");
                return { element: el, type: 'amount' };
            }
        }
        
        console.log("[OLI Content] No matching element found");
        return null;
    }

    // Find text, highlight it with pulse animation, and scroll to it
    function findAndScrollToText(searchText, status, message, scrollAndPulse = true) {
        console.log("[OLI Content] findAndScrollToText:", searchText, "scrollAndPulse:", scrollAndPulse);
        const colors = STATUS_COLORS[status] || STATUS_COLORS.CRITIQUE;
        
        // First, remove any previous focus highlights
        document.querySelectorAll('.oli-focus-highlight').forEach(el => {
            el.classList.remove('oli-focus-highlight');
            el.style.animation = '';
            el.style.outline = '';
            el.style.boxShadow = '';
        });
        
        // Try to find in existing highlights first (only if not scrolling, meaning this is a re-check)
        if (scrollAndPulse) {
            const existingHighlights = document.querySelectorAll('.oli-highlight');
            console.log("[OLI Content] Existing highlights:", existingHighlights.length);
            
            const existingHighlight = Array.from(existingHighlights).find(el => {
                const elValue = el.value || el.textContent || '';
                return elValue.includes(searchText) || elValue.includes(extractKeyValue(searchText));
            });
            
            if (existingHighlight) {
                console.log("[OLI Content] Found in existing highlight");
                scrollToAndPulse(existingHighlight, colors);
                return true;
            }
        }
        
        // Extract key value from the search text
        const keyValue = extractKeyValue(searchText);
        console.log("[OLI Content] Key value extracted:", keyValue);
        
        // Try to find the best matching element first (forms, fields, tables)
        const bestMatch = findBestMatchElement(searchText, keyValue);
        if (bestMatch) {
            console.log("[OLI Content] Found best match:", bestMatch.type);
            highlightExistingElement(bestMatch.element, status, message, colors, scrollAndPulse);
            return true;
        }
        
        // Create search variants
        const searchVariants = [
            searchText,
            keyValue,
            searchText.trim().replace(/\s+/g, ' '),
            keyValue.replace(/\s+/g, ''),  // Remove all spaces
            keyValue.replace(/\s/g, '\u00A0'),  // Non-breaking spaces
            searchText.replace(/\s*:\s*/g, ' : '),  // Normalize colons
        ];
        
        // Remove duplicates
        const uniqueVariants = [...new Set(searchVariants.filter(v => v && v.length > 0))];
        console.log("[OLI Content] Search variants:", uniqueVariants);
        
        // Search in the page text
        const walker = document.createTreeWalker(
            document.body,
            NodeFilter.SHOW_TEXT,
            null,
            false
        );
        
        let node;
        while (node = walker.nextNode()) {
            const nodeText = node.nodeValue;
            if (!nodeText || nodeText.trim().length === 0) continue;
            
            // Check if any variant matches
            const matchingVariant = uniqueVariants.find(variant => nodeText.includes(variant));
            if (matchingVariant) {
                console.log("[OLI Content] Found text with variant:", matchingVariant);
                
                // Create a highlight span for this text
                const span = document.createElement('span');
                span.className = 'oli-highlight oli-focus-highlight';
                span.dataset.oliOriginal = node.nodeValue;
                span.dataset.oliStatus = status;
                span.dataset.oliMessage = message || 'Element flagged by OLI';
                
                span.style.cssText = `
                    display: inline;
                    position: relative;
                    border: 3px solid ${colors.border};
                    background: ${colors.bg};
                    border-radius: 4px;
                    padding: 2px 6px;
                    margin: 0 2px;
                    transition: all 0.2s ease;
                `;
                
                // Create the highlighted content using the matching variant
                const parts = node.nodeValue.split(matchingVariant);
                span.innerHTML = parts.join(`<mark style="
                    background: ${colors.bg};
                    color: ${colors.text};
                    font-weight: 700;
                    padding: 2px 4px;
                    border-radius: 2px;
                ">${matchingVariant}</mark>`);
                
                // Add icon badge
                const badge = document.createElement('span');
                badge.className = 'oli-badge';
                badge.style.cssText = `
                    position: absolute;
                    top: -12px;
                    right: -12px;
                    background: ${colors.border};
                    color: white;
                    font-size: 12px;
                    width: 24px;
                    height: 24px;
                    border-radius: 50%;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    font-weight: bold;
                    box-shadow: 0 2px 8px ${colors.border}60;
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
                
                node.parentNode.replaceChild(span, node);
                highlightedElements.push(span);
                
                scrollToAndPulse(span, colors);
                return true;
            }
        }
        
        console.log("[OLI Content] Text not found in page");
        return false;
    }

    // Highlight an existing DOM element (without wrapping in new span)
    function highlightExistingElement(element, status, message, colors, scrollAndPulse = true) {
        console.log("[OLI Content] highlightExistingElement:", element.tagName, element.id || element.name, "scrollAndPulse:", scrollAndPulse);
        
        // Add highlight class and styles
        element.classList.add('oli-highlight');
        element.dataset.oliStatus = status;
        element.dataset.oliMessage = message || 'Element flagged by OLI';
        
        // Store original styles
        const originalStyle = element.getAttribute('style') || '';
        element.dataset.oliOriginalStyle = originalStyle;
        
        // Apply highlight styles
        element.style.cssText = originalStyle + `
            outline: 3px solid ${colors.border} !important;
            outline-offset: 2px !important;
            background: ${colors.bg} !important;
            border-radius: 4px !important;
            transition: all 0.2s ease;
        `;
        
        // Check if element is a void tag (cannot have children)
        const isVoid = /^(IMG|INPUT|BR|HR|AREA|BASE|BASEFONT|COL|LINK|META|PARAM|SELECT|TEXTAREA)$/i.test(element.tagName);
        
        // Check if badge needs to be created
        let badgeExists = false;
        if (isVoid) {
            // Check if we already created a badge for this element
            const existingBadge = element.parentElement?.querySelector(`.oli-badge[data-for="${element.id || element.name}"]`);
            badgeExists = !!existingBadge;
        } else {
            badgeExists = !!element.querySelector('.oli-badge');
        }
        
        if (!badgeExists) {
            const badge = document.createElement('span');
            badge.className = 'oli-badge';
            badge.style.cssText = `
                position: fixed;
                background: ${colors.border};
                color: white;
                font-size: 12px;
                width: 24px;
                height: 24px;
                border-radius: 50%;
                display: flex;
                align-items: center;
                justify-content: center;
                font-weight: bold;
                box-shadow: 0 2px 8px ${colors.border}80;
                z-index: 999997;
                pointer-events: none;
                transition: all 0.2s ease;
            `;
            badge.textContent = status === 'CRITIQUE' ? '!' : status === 'AVERTISSEMENT' ? '?' : '✓';
            
            if (isVoid) {
                // For void elements (inputs, selects), use fixed positioning based on getBoundingClientRect
                badge.dataset.for = element.id || element.name || '';
                
                // Function to update badge position
                const updateBadgePosition = () => {
                    const rect = element.getBoundingClientRect();
                    if (rect && rect.width > 0 && rect.height > 0) {
                        badge.style.top = `${rect.top - 12}px`;
                        badge.style.left = `${rect.right - 12}px`;
                        badge.style.display = 'flex';
                    } else {
                        badge.style.display = 'none'; // Hide if element not visible
                    }
                };
                
                // Initial position - wait a tick for layout
                requestAnimationFrame(() => {
                    const rect = element.getBoundingClientRect();
                    console.log("[OLI] Initial badge position for", element.tagName, element.id || element.name, "rect:", rect);
                    updateBadgePosition();
                });
                
                // Update position on scroll and resize
                const scrollHandler = () => updateBadgePosition();
                window.addEventListener('scroll', scrollHandler, true);
                window.addEventListener('resize', scrollHandler);
                
                // Store cleanup function
                badge.dataset.cleanup = 'scroll-listener';
                element.dataset.badgeScrollHandler = scrollHandler.toString();
                
                document.body.appendChild(badge);
                element.dataset.oliBadgeCreated = 'true';
            } else {
                // Normal elements can use relative positioning
                const originalPosition = window.getComputedStyle(element).position;
                if (originalPosition === 'static') {
                    element.style.position = 'relative';
                }
                badge.style.position = 'absolute';
                badge.style.top = '-12px';
                badge.style.right = '-12px';
                element.appendChild(badge);
            }
        }
        
        // Add hover events
        const mouseEnterHandler = function() {
            showTooltip(this, this.dataset.oliMessage, this.dataset.oliStatus);
        };
        const mouseLeaveHandler = function() {
            hideTooltip();
        };
        
        element.addEventListener('mouseenter', mouseEnterHandler);
        element.addEventListener('mouseleave', mouseLeaveHandler);
        
        // Store handlers for cleanup
        element.dataset.oliMouseEnter = 'attached';
        element.dataset.oliMouseLeave = 'attached';
        
        highlightedElements.push(element);
        
        if (scrollAndPulse) {
            scrollToAndPulse(element, colors);
        }
    }

    // Scroll to element and add pulse animation
    function scrollToAndPulse(element, colors) {
        // Add focus animation styles if not present
        if (!document.getElementById('oli-focus-styles')) {
            const style = document.createElement('style');
            style.id = 'oli-focus-styles';
            style.textContent = `
                @keyframes oli-focus-pulse {
                    0% {
                        box-shadow: 0 0 0 0 rgba(239, 68, 68, 0.7);
                        transform: scale(1);
                    }
                    50% {
                        box-shadow: 0 0 0 15px rgba(239, 68, 68, 0);
                        transform: scale(1.05);
                    }
                    100% {
                        box-shadow: 0 0 0 0 rgba(239, 68, 68, 0);
                        transform: scale(1);
                    }
                }
                .oli-focus-highlight {
                    animation: oli-focus-pulse 0.6s ease-out 3 !important;
                    z-index: 10000 !important;
                }
            `;
            document.head.appendChild(style);
        }
        
        // Add focus class
        element.classList.add('oli-focus-highlight');
        
        // Scroll to the element with offset for better visibility
        const rect = element.getBoundingClientRect();
        const scrollTop = window.pageYOffset || document.documentElement.scrollTop;
        const targetY = rect.top + scrollTop - (window.innerHeight / 3);
        
        window.scrollTo({
            top: Math.max(0, targetY),
            behavior: 'smooth'
        });
        
        // Show tooltip briefly
        setTimeout(() => {
            showTooltip(element, element.dataset.oliMessage, element.dataset.oliStatus);
            
            // Hide tooltip after 3 seconds
            setTimeout(() => {
                hideTooltip();
            }, 3000);
        }, 500);
        
        // Remove focus class after animation
        setTimeout(() => {
            element.classList.remove('oli-focus-highlight');
        }, 2000);
    }

    // Listen for messages from the side panel
    chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
        console.log("📨 OLI received message:", request.action, request.data);
        
        if (request.action === "SCAN_PAGE") {
            // Get base text
            let text = document.body.innerText;
            
            // Extract form field values and append them
            const formData = extractFormData();
            console.log("[OLI] SCAN_PAGE - form data extracted:", formData);
            
            if (formData.length > 0) {
                text += "\n\n=== FORM DATA ===\n";
                formData.forEach(field => {
                    text += `Field [${field.label}]: ${field.value}\n`;
                });
            }
            
            console.log("[OLI] SCAN_PAGE - text length:", text.length, "form fields:", formData.length);
            console.log("[OLI] SCAN_PAGE - final text excerpt:", text.substring(text.length - 500));
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
                console.log("[OLI] HIGHLIGHT_RISKS - processing", highlights.length, "highlights");
                highlights.forEach(h => {
                    // Use findAndScrollToText which is smarter and can handle inputs
                    // Pass false for scrollAndPulse since we'll scroll to them individually via SCROLL_TO_TEXT
                    const found = findAndScrollToText(h.text, h.status, `Risk element detected`, false);
                    console.log("[OLI] Highlight attempt for:", h.text, "found:", found);
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
        else if (request.action === "SCROLL_TO_TEXT") {
            // Find, highlight, and scroll to specific text
            console.log("[OLI Content] SCROLL_TO_TEXT received:", request.data);
            const { text, status, message } = request.data;
            
            if (!text) {
                console.log("[OLI Content] No text provided");
                sendResponse({ success: false, error: "No text provided" });
                return true;
            }
            
            // Find the text in the page
            const found = findAndScrollToText(text, status, message);
            console.log("[OLI Content] Text found:", found);
            sendResponse({ success: found });
        }
        
        return true; // Keep message channel open for async response
    });

    // Initial setup
    createTooltip();
    console.log("✅ OLI Content Script Ready");
})();
