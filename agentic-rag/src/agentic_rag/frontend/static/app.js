// API Configuration - uses runtime config if available
// Empty string means use relative paths (nginx proxy)
const API_URL = (window.APP_CONFIG && typeof window.APP_CONFIG.API_URL === 'string')
    ? window.APP_CONFIG.API_URL
    : (window.location.hostname === 'localhost' ? 'http://localhost:8000' : '');

// Headers for API requests
// Note: Domino authentication is handled via session cookies automatically
// when making cross-origin requests to other Domino apps
function getAuthHeaders() {
    return { 'Content-Type': 'application/json' };
}

// DOM Elements
const questionInput = document.getElementById('question');
const rerankingMode = document.getElementById('reranking-mode');
const refinementMode = document.getElementById('refinement-mode');
const topK = document.getElementById('top-k');
const showTrace = document.getElementById('show-trace');
const btnAgentic = document.getElementById('btn-agentic');
const btnBaseline = document.getElementById('btn-baseline');
const btnCompare = document.getElementById('btn-compare');
const loadingEl = document.getElementById('loading');
const resultsEl = document.getElementById('results');

// Event Listeners
btnAgentic.addEventListener('click', () => runAgenticQuery());
btnBaseline.addEventListener('click', () => runBaselineQuery());
btnCompare.addEventListener('click', () => runBothQueries());

// Sample question buttons
document.querySelectorAll('.sample-btn').forEach(btn => {
    btn.addEventListener('click', () => {
        questionInput.value = btn.dataset.question;
        questionInput.focus();
    });
});

// Category tabs
document.querySelectorAll('.category-tab').forEach(tab => {
    tab.addEventListener('click', () => {
        // Remove active class from all tabs
        document.querySelectorAll('.category-tab').forEach(t => t.classList.remove('active'));
        // Add active class to clicked tab
        tab.classList.add('active');

        // Hide all category content
        document.querySelectorAll('.category-content').forEach(content => {
            content.classList.add('hidden');
        });

        // Show selected category content
        const category = tab.dataset.category;
        const content = document.getElementById(`category-${category}`);
        if (content) {
            content.classList.remove('hidden');
        }
    });
});

// Query cards
document.querySelectorAll('.query-card').forEach(card => {
    card.addEventListener('click', (e) => {
        e.preventDefault();
        const question = card.dataset.question;
        if (question) {
            questionInput.value = question;
            questionInput.focus();
            // Visual feedback - brief highlight
            card.style.background = 'linear-gradient(145deg, #4a9eff 0%, #3b7ddd 100%)';
            setTimeout(() => {
                card.style.background = '';
            }, 200);
            // Scroll to query input
            questionInput.scrollIntoView({ behavior: 'smooth', block: 'center' });
        }
    });
});

// API Functions
async function runAgenticQuery() {
    const question = questionInput.value.trim();
    if (!question) {
        alert('Please enter a question');
        return;
    }

    showLoading(true);
    clearResults();

    try {
        const headers = getAuthHeaders();
        const response = await fetch(`${API_URL}/api/query`, {
            method: 'POST',
            headers: headers,
            body: JSON.stringify({
                question: question,
                reranking_mode: rerankingMode.value,
                refinement_mode: refinementMode.value,
                top_k: parseInt(topK.value),
                include_trace: showTrace.checked
            })
        });

        if (!response.ok) {
            throw new Error(`API Error: ${response.status}`);
        }

        const data = await response.json();
        displayAgenticResult(data);
    } catch (error) {
        displayError(error.message);
    } finally {
        showLoading(false);
    }
}

async function runBaselineQuery() {
    const question = questionInput.value.trim();
    if (!question) {
        alert('Please enter a question');
        return;
    }

    showLoading(true);
    clearResults();

    try {
        const headers = getAuthHeaders();
        const response = await fetch(`${API_URL}/api/query/baseline`, {
            method: 'POST',
            headers: headers,
            body: JSON.stringify({
                question: question,
                top_k: parseInt(topK.value),
                include_trace: showTrace.checked
            })
        });

        if (!response.ok) {
            throw new Error(`API Error: ${response.status}`);
        }

        const data = await response.json();
        displayBaselineResult(data);
    } catch (error) {
        displayError(error.message);
    } finally {
        showLoading(false);
    }
}

async function runBothQueries() {
    const question = questionInput.value.trim();
    if (!question) {
        alert('Please enter a question');
        return;
    }

    showLoading(true);
    clearResults();

    try {
        const headers = getAuthHeaders();
        const [agenticResponse, baselineResponse] = await Promise.all([
            fetch(`${API_URL}/api/query`, {
                method: 'POST',
                headers: headers,
                body: JSON.stringify({
                    question: question,
                    reranking_mode: rerankingMode.value,
                    refinement_mode: refinementMode.value,
                    top_k: parseInt(topK.value),
                    include_trace: showTrace.checked
                })
            }),
            fetch(`${API_URL}/api/query/baseline`, {
                method: 'POST',
                headers: headers,
                body: JSON.stringify({
                    question: question,
                    top_k: parseInt(topK.value),
                    include_trace: showTrace.checked
                })
            })
        ]);

        const agenticData = await agenticResponse.json();
        const baselineData = await baselineResponse.json();

        displayAgenticResult(agenticData);
        displayBaselineResult(baselineData);
    } catch (error) {
        displayError(error.message);
    } finally {
        showLoading(false);
    }
}

// Display Functions
function displayAgenticResult(data) {
    const answer = data.answer || {};
    const trace = data.trace;

    const html = `
        <div class="result-card">
            <div class="result-header">
                <h3>🤖 Agentic RAG Response</h3>
                <span class="badge badge-agentic">Structured</span>
            </div>
            <div class="result-body">
                <div class="summary">${escapeHtml(answer.summary || 'No summary available')}</div>

                ${answer.key_findings && answer.key_findings.length > 0 ? `
                    <div class="section-title">Key Findings</div>
                    <ul class="findings-list">
                        ${answer.key_findings.map(f => `
                            <li>
                                ${escapeHtml(f.finding)}
                                <span class="finding-source">${escapeHtml(f.source)}</span>
                                <span class="confidence-${f.confidence}">(${f.confidence})</span>
                            </li>
                        `).join('')}
                    </ul>
                ` : ''}

                ${answer.regulatory_context && answer.regulatory_context.length > 0 ? `
                    <div class="section-title">Regulatory Context</div>
                    <ul class="regulatory-list">
                        ${answer.regulatory_context.map(r => `
                            <li>
                                <strong>${escapeHtml(r.regulation)}</strong>: ${escapeHtml(r.relevance)}
                                ${r.compliance_status ? `
                                    <span class="compliance-status status-${r.compliance_status.replace('-', '')}">${r.compliance_status}</span>
                                ` : ''}
                            </li>
                        `).join('')}
                    </ul>
                ` : ''}

                ${answer.causal_chain && answer.causal_chain.length > 0 ? `
                    <div class="section-title">Causal Chain</div>
                    <ol class="causal-list">
                        ${answer.causal_chain.map(step => `<li>${escapeHtml(step)}</li>`).join('')}
                    </ol>
                ` : ''}

                ${answer.caveats && answer.caveats.length > 0 ? `
                    <div class="section-title">Caveats</div>
                    <ul class="caveats-list">
                        ${answer.caveats.map(c => `<li>⚠️ ${escapeHtml(c)}</li>`).join('')}
                    </ul>
                ` : ''}

                ${trace && showTrace.checked ? `
                    <div class="trace-section">
                        <button class="trace-toggle" onclick="toggleTrace(this)">📊 Show Execution Trace</button>
                        <div class="trace-content hidden">
                            ${renderTraceVisualization(trace)}
                        </div>
                    </div>
                ` : ''}
            </div>
        </div>
    `;

    resultsEl.insertAdjacentHTML('beforeend', html);
}

function displayBaselineResult(data) {
    const trace = data.trace;

    const html = `
        <div class="result-card">
            <div class="result-header">
                <h3>📊 Traditional RAG Response</h3>
                <span class="badge badge-traditional">Baseline</span>
            </div>
            <div class="result-body">
                <div class="traditional-answer">${escapeHtml(data.answer || 'No answer available')}</div>
                <div class="meta-info">
                    <span>📄 Documents used: ${data.documents_used || 0}</span>
                    <span>📁 Sources: ${(data.sources || []).join(', ') || 'None'}</span>
                </div>

                ${trace && showTrace.checked ? `
                    <div class="trace-section">
                        <button class="trace-toggle" onclick="toggleTrace(this)">📊 Show Execution Trace</button>
                        <div class="trace-content hidden">
                            ${renderBaselineTraceVisualization(trace)}
                        </div>
                    </div>
                ` : ''}
            </div>
        </div>
    `;

    resultsEl.insertAdjacentHTML('beforeend', html);
}

function renderBaselineTraceVisualization(trace) {
    if (!trace) return '<p>No trace data available</p>';

    const maxDuration = trace.steps && trace.steps.length > 0
        ? Math.max(...trace.steps.map(s => s.duration_ms || 0))
        : 1;

    let html = `
        <div class="trace-visualization">
            <div class="trace-header">
                <h4>Traditional RAG Pipeline</h4>
                <div class="trace-summary">
                    <span class="trace-stat"><span class="label">Pipeline:</span> <span class="value">Traditional</span></span>
                    <span class="trace-stat"><span class="label">Sources:</span> <span class="value">${trace.sources_used?.join(', ') || 'N/A'}</span></span>
                    <span class="trace-stat"><span class="label">Total Time:</span> <span class="value">${trace.total_duration_ms?.toFixed(0) || 'N/A'}ms</span></span>
                </div>
                ${trace.mlflow_run_id ? `
                    <div class="trace-mlflow-link">
                        <small>MLflow Run: ${trace.mlflow_run_id.substring(0, 8)}...</small>
                    </div>
                ` : ''}
            </div>

            <div class="trace-timeline">
                <h4>Execution Timeline</h4>
    `;

    if (trace.steps && trace.steps.length > 0) {
        trace.steps.forEach((step, index) => {
            const barWidth = Math.max(5, (step.duration_ms / maxDuration) * 100);
            const stepClass = step.status === 'error' ? 'step-error' : 'step-success';
            const color = step.type === 'retriever' ? '#4ade80' : '#a78bfa';
            const icon = step.type === 'retriever' ? '📚' : '🤖';

            html += `
                <div class="trace-step ${stepClass}" onclick="toggleStepDetails(this)">
                    <div class="step-header">
                        <span class="step-icon" style="background: ${color}">${icon}</span>
                        <span class="step-name">${escapeHtml(step.name)}</span>
                        <span class="step-duration">${step.duration_ms?.toFixed(0) || 0}ms</span>
                    </div>
                    <div class="step-bar-container">
                        <div class="step-bar" style="width: ${barWidth}%; background: ${color}"></div>
                    </div>
                    <div class="step-details hidden">
                        ${step.details ? Object.entries(step.details).map(([k, v]) =>
                            `<div class="detail-item"><span class="detail-key">${escapeHtml(k)}:</span> <span class="detail-value">${escapeHtml(String(v))}</span></div>`
                        ).join('') : '<em>No details</em>'}
                    </div>
                </div>
            `;
        });
    }

    // Add LLM Calls section for baseline
    if (trace.llm_calls && trace.llm_calls.length > 0) {
        html += renderLLMCallsSection(trace.llm_calls);
    }

    html += `
            </div>
            <div class="trace-raw">
                <button class="raw-toggle" onclick="toggleRawTrace(this)">Show Raw JSON</button>
                <pre class="raw-json hidden">${escapeHtml(JSON.stringify(trace, null, 2))}</pre>
            </div>
        </div>
    `;

    return html;
}

function renderLLMCallsSection(llmCalls) {
    if (!llmCalls || llmCalls.length === 0) return '';

    let html = `
        <div class="trace-section-block llm-calls-section">
            <button class="llm-calls-toggle" onclick="toggleLLMCalls(this)">🔮 Show LLM Prompts & Responses (${llmCalls.length})</button>
            <div class="llm-calls-content hidden">
    `;

    llmCalls.forEach((call, index) => {
        const stepLabel = call.step.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase());
        const formattedPrompt = formatLLMContent(call.prompt, 'prompt');
        const formattedResponse = formatLLMContent(call.response, 'response');

        html += `
            <div class="llm-call-item">
                <div class="llm-call-header" onclick="toggleLLMCallDetails(this)">
                    <span class="llm-call-step">${escapeHtml(stepLabel)}</span>
                    <span class="llm-call-model">${escapeHtml(call.model || 'N/A')}</span>
                    <span class="llm-call-duration">${call.duration_ms?.toFixed(0) || 'N/A'}ms</span>
                    <span class="llm-call-expand">▼</span>
                </div>
                <div class="llm-call-details hidden">
                    <div class="llm-call-prompt">
                        <div class="llm-section-header" onclick="toggleLLMSection(this)">
                            <span>📝 Prompt</span>
                            <span class="char-count">(${call.prompt?.length || 0} chars)</span>
                            <span class="expand-icon">▼</span>
                        </div>
                        <div class="llm-content hidden">${formattedPrompt}</div>
                    </div>
                    <div class="llm-call-response">
                        <div class="llm-section-header" onclick="toggleLLMSection(this)">
                            <span>💬 Response</span>
                            <span class="char-count">(${call.response?.length || 0} chars)</span>
                            <span class="expand-icon">▼</span>
                        </div>
                        <div class="llm-content hidden">${formattedResponse}</div>
                    </div>
                </div>
            </div>
        `;
    });

    html += `
            </div>
        </div>
    `;

    return html;
}

function formatLLMContent(content, type) {
    if (!content || content === 'N/A') return '<span class="llm-empty">N/A</span>';

    // Try to parse as JSON first for pretty printing
    try {
        const parsed = JSON.parse(content);
        const prettyJson = JSON.stringify(parsed, null, 2);
        return formatWithSyntaxHighlighting(prettyJson, true);
    } catch (e) {
        // Not JSON, format as text with highlighting
        return formatWithSyntaxHighlighting(content, false);
    }
}

function formatWithSyntaxHighlighting(text, isJson) {
    let escaped = escapeHtml(text);

    if (isJson) {
        // JSON syntax highlighting
        // Keys (before colon)
        escaped = escaped.replace(/"([^"]+)":/g, '<span class="json-key">"$1"</span>:');
        // String values (after colon, not keys)
        escaped = escaped.replace(/: "([^"]*)"/g, ': <span class="json-string">"$1"</span>');
        // Numbers
        escaped = escaped.replace(/: (\d+\.?\d*)/g, ': <span class="json-number">$1</span>');
        // Booleans
        escaped = escaped.replace(/: (true|false)/g, ': <span class="json-boolean">$1</span>');
        // Null
        escaped = escaped.replace(/: (null)/g, ': <span class="json-null">$1</span>');
        // Brackets
        escaped = escaped.replace(/([{}\[\]])/g, '<span class="json-bracket">$1</span>');
    } else {
        // Text prompt highlighting
        // Section headers (lines ending with colon)
        escaped = escaped.replace(/^([A-Z][^:\n]*):$/gm, '<span class="text-header">$1:</span>');
        // Labels like "Question:", "Context:", etc at start of line
        escaped = escaped.replace(/^(Question|Context|Intent|Output|Example|Retrieved|Passages?):/gm, '<span class="text-label">$1:</span>');
        // Document separators
        escaped = escaped.replace(/^(---.*---)$/gm, '<span class="text-separator">$1</span>');
        // Bullet points
        escaped = escaped.replace(/^(\s*[-•*]\s)/gm, '<span class="text-bullet">$1</span>');
        // Numbered items
        escaped = escaped.replace(/^(\s*\d+\.\s)/gm, '<span class="text-number">$1</span>');
        // JSON-like content in prompts
        escaped = escaped.replace(/(\{|\}|\[|\])/g, '<span class="json-bracket">$1</span>');
        escaped = escaped.replace(/"([^"]+)":/g, '<span class="json-key">"$1"</span>:');
    }

    return `<pre class="llm-formatted">${escaped}</pre>`;
}

function toggleLLMCalls(button) {
    const content = button.nextElementSibling;
    content.classList.toggle('hidden');
    const count = button.textContent.match(/\((\d+)\)/)?.[1] || '';
    button.textContent = content.classList.contains('hidden')
        ? `🔮 Show LLM Prompts & Responses (${count})`
        : `🔮 Hide LLM Prompts & Responses (${count})`;
}

function toggleLLMCallDetails(header) {
    const details = header.nextElementSibling;
    details.classList.toggle('hidden');
    const expandIcon = header.querySelector('.llm-call-expand');
    expandIcon.textContent = details.classList.contains('hidden') ? '▼' : '▲';
}

function toggleLLMSection(header) {
    const content = header.nextElementSibling;
    content.classList.toggle('hidden');
    const expandIcon = header.querySelector('.expand-icon');
    expandIcon.textContent = content.classList.contains('hidden') ? '▼' : '▲';
}

function displayError(message) {
    const html = `
        <div class="error-message">
            <h3>❌ Error</h3>
            <p>${escapeHtml(message)}</p>
            <p>Make sure the API server is running at ${API_URL}</p>
        </div>
    `;
    resultsEl.innerHTML = html;
}

// Helper Functions
function showLoading(show) {
    loadingEl.classList.toggle('hidden', !show);
}

function clearResults() {
    resultsEl.innerHTML = '';
}

function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function toggleTrace(button) {
    const content = button.nextElementSibling;
    content.classList.toggle('hidden');
    button.textContent = content.classList.contains('hidden')
        ? '📊 Show Execution Trace'
        : '📊 Hide Execution Trace';
}

function renderTraceVisualization(trace) {
    if (!trace) return '<p>No trace data available</p>';

    const stepIcons = {
        'tool': '🔧',
        'llm': '🤖',
        'retriever': '📚',
        'chain': '🔗',
        'model': '🎯',  // For cross-encoder reranking
    };

    const stepColors = {
        'tool': '#6366f1',
        'llm': '#8b5cf6',
        'retriever': '#06b6d4',
        'chain': '#f59e0b',
        'model': '#ec4899',  // Pink for reranking model
    };

    const statusColors = {
        'success': '#10b981',
        'warning': '#f59e0b',
        'error': '#ef4444',
    };

    // Calculate max duration for scaling
    const maxDuration = trace.steps && trace.steps.length > 0
        ? Math.max(...trace.steps.map(s => s.duration_ms || 0))
        : 1;

    let html = `
        <div class="trace-visualization">
            <div class="trace-header">
                <div class="trace-summary">
                    <span class="trace-stat"><strong>Intent:</strong> ${trace.intent || 'N/A'} ${trace.intent_confidence ? `(${trace.intent_confidence})` : ''}</span>
                    <span class="trace-stat"><strong>Strategy:</strong> ${trace.strategy || 'N/A'}</span>
                    <span class="trace-stat"><strong>Sources:</strong> ${trace.sources_used?.join(', ') || 'N/A'}</span>
                    <span class="trace-stat"><strong>Total Time:</strong> ${trace.total_duration_ms?.toFixed(0) || 'N/A'}ms</span>
                </div>
                ${trace.mlflow_run_id ? `
                    <div class="trace-mlflow-link">
                        <small>MLflow Run: ${trace.mlflow_run_id.substring(0, 8)}...</small>
                    </div>
                ` : ''}
            </div>

            <div class="trace-timeline">
                <h4>Execution Timeline</h4>
    `;

    // Render steps timeline
    if (trace.steps && trace.steps.length > 0) {
        trace.steps.forEach((step, index) => {
            const icon = stepIcons[step.type] || '⚡';
            const color = stepColors[step.type] || '#6b7280';
            const statusColor = statusColors[step.status] || '#10b981';
            const barWidth = Math.max(5, (step.duration_ms / maxDuration) * 100);

            html += `
                <div class="trace-step" onclick="toggleStepDetails(this)">
                    <div class="step-header">
                        <span class="step-icon" style="background: ${color}">${icon}</span>
                        <span class="step-name">${escapeHtml(step.name)}</span>
                        <span class="step-duration">${step.duration_ms?.toFixed(0) || 0}ms</span>
                        <span class="step-status" style="color: ${statusColor}">●</span>
                    </div>
                    <div class="step-bar-container">
                        <div class="step-bar" style="width: ${barWidth}%; background: ${color}"></div>
                    </div>
                    <div class="step-details hidden">
                        ${step.details ? Object.entries(step.details).map(([k, v]) =>
                            `<div class="detail-item"><span class="detail-key">${escapeHtml(k)}:</span> <span class="detail-value">${escapeHtml(String(v))}</span></div>`
                        ).join('') : '<em>No details</em>'}
                    </div>
                </div>
            `;
        });
    } else {
        html += '<p class="no-steps">No step data available</p>';
    }

    html += `</div>`;

    // Add retrieval details if available
    if (trace.retrievals && trace.retrievals.length > 0) {
        html += `
            <div class="trace-section-block">
                <h4>Retrieval Details</h4>
                <div class="retrieval-list">
                    ${trace.retrievals.map(r => `
                        <div class="retrieval-item">
                            <span class="retrieval-iter">Iteration ${r.iteration}</span>
                            <span class="retrieval-docs">${r.documents_retrieved} docs</span>
                            <span class="retrieval-sources">${r.sources?.join(', ') || ''}</span>
                            <span class="retrieval-time">${r.duration_ms?.toFixed(0)}ms</span>
                        </div>
                    `).join('')}
                </div>
            </div>
        `;
    }

    // Add reranking details if available
    if (trace.reranking && trace.reranking.mode !== 'none') {
        html += `
            <div class="trace-section-block">
                <h4>Reranking</h4>
                <div class="refinement-details">
                    <span><strong>Mode:</strong> ${trace.reranking.mode}</span>
                    <span><strong>Model:</strong> ${trace.reranking.model || 'N/A'}</span>
                    <span><strong>Input:</strong> ${trace.reranking.input_count} docs</span>
                    <span><strong>Output:</strong> ${trace.reranking.output_count} docs</span>
                    <span><strong>Duration:</strong> ${trace.reranking.duration_ms?.toFixed(0) || 'N/A'}ms</span>
                </div>
            </div>
        `;
    }

    // Add refinement details if available
    if (trace.refinement) {
        html += `
            <div class="trace-section-block">
                <h4>Context Refinement</h4>
                <div class="refinement-details">
                    <span><strong>Mode:</strong> ${trace.refinement.mode}</span>
                    <span><strong>Input:</strong> ${trace.refinement.input_count} docs</span>
                    <span><strong>Output:</strong> ${trace.refinement.output_count} docs</span>
                    <span><strong>Dropped:</strong> ${trace.refinement.input_count - trace.refinement.output_count} docs</span>
                </div>
            </div>
        `;
    }

    // Add constraint info if available
    if (trace.constraints && Object.values(trace.constraints).some(v => v)) {
        html += `
            <div class="trace-section-block">
                <h4>Query Constraints</h4>
                <div class="constraint-details">
                    ${Object.entries(trace.constraints)
                        .filter(([k, v]) => v)
                        .map(([k, v]) => `<span class="constraint-item"><strong>${k}:</strong> ${escapeHtml(String(v))}</span>`)
                        .join('')}
                </div>
                ${trace.constraint_validation ? `
                    <div class="constraint-validation ${trace.constraint_validation.is_valid ? 'valid' : 'invalid'}">
                        ${trace.constraint_validation.is_valid ? '✅ Constraints satisfied' : '⚠️ Constraints not fully satisfied'}
                        ${trace.constraint_validation.matched_count ? ` (${trace.constraint_validation.matched_count} matches)` : ''}
                    </div>
                ` : ''}
            </div>
        `;
    }

    // Add LLM Calls section for agentic RAG
    if (trace.llm_calls && trace.llm_calls.length > 0) {
        html += renderLLMCallsSection(trace.llm_calls);
    }

    // Raw JSON toggle
    html += `
        <div class="trace-raw">
            <button class="raw-toggle" onclick="toggleRawTrace(this)">Show Raw JSON</button>
            <pre class="raw-json hidden">${escapeHtml(JSON.stringify(trace, null, 2))}</pre>
        </div>
    `;

    html += `</div>`;
    return html;
}

function toggleStepDetails(stepEl) {
    const details = stepEl.querySelector('.step-details');
    if (details) {
        details.classList.toggle('hidden');
    }
}

function toggleRawTrace(button) {
    const rawJson = button.nextElementSibling;
    rawJson.classList.toggle('hidden');
    button.textContent = rawJson.classList.contains('hidden') ? 'Show Raw JSON' : 'Hide Raw JSON';
}

// Check API health on load
async function checkApiHealth() {
    try {
        const headers = getAuthHeaders();
        const response = await fetch(`${API_URL}/health`, { headers });
        if (response.ok) {
            console.log('API is healthy');
        }
    } catch (error) {
        console.warn('API not available:', error.message);
    }
}

checkApiHealth();
