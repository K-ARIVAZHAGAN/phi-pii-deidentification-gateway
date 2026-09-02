/**
 * PHI/PII De-Identification Gateway — Standalone Frontend Controller
 * Connects to Backend API on http://localhost:8000
 */

const BACKEND_URL = 'http://localhost:8000';

// Pre-configured Clinical Samples
const SAMPLES = {
  neurology: `PATIENT: Robert Henderson | DOB: 05/14/1958 | MRN: 884-9102-X | SSN: 078-45-9921
DATE OF CONSULT: 10/14/2023
ATTENDING: Dr. James Parkinson, MD (NPI: 1982736450, Phone: 617-555-0144)
FACILITY: St. Luke's Hospital, Boston, MA 02115

REASON FOR CONSULT: Progressive resting tremor and cogwheel rigidity.
HISTORY: Mr. Henderson is a 65-year-old male evaluated for Parkinson's disease. Prior appendectomy on 09/10/2023. Babinski reflex is negative bilaterally. Initiating carbidopa-levodopa 25/100 mg TID.

PLAN: Follow-up clinic appointment on 11/25/2023 in 6 weeks.
Signed: Dr. James Parkinson, MD`,

  oncology: `OPERATIVE NOTE & DISCHARGE PLAN
PATIENT: Eleanor Vance | DOB: 10/14/1982 | MRN: 48201-ONC
DATE OF SURGERY: 03/15/2024
SURGEON: Dr. Alan Whipple, MD (NPI: 1092837465)
ASSISTANT: Dr. Katherine Vance, MD
FACILITY: Massachusetts General Hospital, Boston, MA 02114

PREOPERATIVE DIAGNOSIS: Whipple disease and pancreatic head adenocarcinoma.
PROCEDURE PERFORMED: Classic pancreaticoduodenectomy (Whipple procedure).
FINDINGS: Successful resection. Blood loss 250 mL. Patient tolerated procedure well.

POST-OP PLAN: Prescribed Ceftriaxone IV for 2 weeks followed by oral TMP-SMX for 1 year. Follow-up in surgical clinic in 3 weeks.
Dictated by: Dr. Alan Whipple, MD`,

  geriatric: `GERIATRIC INTAKE NOTE
PATIENT: Arthur Pendelton | AGE: 94-year-old male | DOB: 01/18/1930
MRN: GER-392019 | DATE: 04/10/2024
ATTENDING: Dr. Rebecca Sterling, MD (Phone: 312-555-0199)
FACILITY: Oakwood Extended Care, Chicago, IL 60611

ASSESSMENT: 94yo nonagenarian admitted for mild cognitive impairment. Celebrated his 90th birthday in 2020. Patient ambulates with a walker.
PLAN: Continue physical therapy 3 times weekly. Follow-up on 05/10/2024.`
};

const PROMPT_TEMPLATES = {
  summarize: `Please provide a structured clinical assessment and discharge summary including patient name, attending doctor, facility, consult date, diagnosis, medication plan, and scheduled follow-up:

{text}`,
  soap: `Please extract a structured SOAP progress note (Subjective, Objective, Assessment, Plan) with full patient and provider demographics:

{text}`,
  discharge: `Please generate a structured discharge plan including patient identity, surgeon/attending, diagnosis, medication instructions, and follow-up timeline:

{text}`,
  qa: `What is the patient's name, primary diagnosis, attending physician, medication dosage, and next scheduled follow-up date based on this record?

{text}`,
  custom: `{text}`
};

// Application State
let activeResult = null;
let currentTab = 'full';

// Initialize
document.addEventListener('DOMContentLoaded', () => {
  lucide.createIcons();
  checkBackendHealth();
  setupDropzone();
  setupTextareaStats();
  setInterval(checkBackendHealth, 8000);
});

// Check Backend API Health
async function checkBackendHealth() {
  const indicator = document.getElementById('status-indicator');
  const text = document.getElementById('status-text');

  try {
    const res = await fetch(`${BACKEND_URL}/health`, { method: 'GET', headers: { 'accept': 'application/json' } });
    if (res.ok) {
      const data = await res.json();
      indicator.className = 'w-2.5 h-2.5 rounded-full bg-emerald-400';
      text.innerHTML = `Backend Online <span class="text-cyan-400 font-mono">(${data.model_parameter_count ? (data.model_parameter_count/1e6).toFixed(1)+'M' : 'Sub-1B'})</span>`;
    } else {
      throw new Error('Non-200 response');
    }
  } catch (err) {
    indicator.className = 'w-2.5 h-2.5 rounded-full bg-rose-500 live-pulse';
    text.innerText = 'Backend Offline (:8000)';
  }
}

// Setup Drag & Drop File Handling
function setupDropzone() {
  const dropzone = document.getElementById('dropzone');
  const fileInput = document.getElementById('file-input');

  ['dragenter', 'dragover'].forEach(eventName => {
    dropzone.addEventListener(eventName, (e) => {
      e.preventDefault();
      dropzone.classList.add('dropzone-active');
    }, false);
  });

  ['dragleave', 'drop'].forEach(eventName => {
    dropzone.addEventListener(eventName, (e) => {
      e.preventDefault();
      dropzone.classList.remove('dropzone-active');
    }, false);
  });

  dropzone.addEventListener('drop', (e) => {
    const dt = e.dataTransfer;
    const files = dt.files;
    if (files.length > 0) handleFile(files[0]);
  });

  fileInput.addEventListener('change', (e) => {
    if (e.target.files.length > 0) handleFile(e.target.files[0]);
  });
}

// Handle Ingested File (txt, docx, pdf, json, md)
async function handleFile(file) {
  const ext = file.name.split('.').pop().toLowerCase();
  const textarea = document.getElementById('raw-clinical-text');

  try {
    if (ext === 'txt' || ext === 'md' || ext === 'log') {
      const text = await file.text();
      textarea.value = text;
    } else if (ext === 'json') {
      const text = await file.text();
      try {
        const json = JSON.parse(text);
        if (json.clinical_note) textarea.value = json.clinical_note;
        else if (json.text) textarea.value = json.text;
        else textarea.value = JSON.stringify(json, null, 2);
      } catch (e) {
        textarea.value = text;
      }
    } else if (ext === 'docx') {
      const arrayBuffer = await file.arrayBuffer();
      const result = await mammoth.extractRawText({ arrayBuffer: arrayBuffer });
      textarea.value = result.value;
    } else if (ext === 'pdf') {
      const arrayBuffer = await file.arrayBuffer();
      const pdf = await pdfjsLib.getDocument({ data: arrayBuffer }).promise;
      let fullText = '';
      for (let i = 1; i <= pdf.numPages; i++) {
        const page = await pdf.getPage(i);
        const textContent = await page.getTextContent();
        const pageText = textContent.items.map(item => item.str).join(' ');
        fullText += `[--- PAGE ${i} ---]\n${pageText}\n\n`;
      }
      textarea.value = fullText.trim();
    } else {
      alert(`Unsupported file format .${ext}. Please upload a .txt, .docx, .pdf, or .json file.`);
      return;
    }
    updateTextStats();
  } catch (err) {
    alert(`Error reading file: ${err.message}`);
  }
}

// Update Textarea Word & Char Stats
function setupTextareaStats() {
  const textarea = document.getElementById('raw-clinical-text');
  textarea.addEventListener('input', updateTextStats);
}

function updateTextStats() {
  const text = document.getElementById('raw-clinical-text').value;
  const chars = text.length;
  const words = text.trim() ? text.trim().split(/\s+/).length : 0;
  document.getElementById('input-stats').innerText = `${words} words | ${chars} chars`;
}

// Load Pre-configured Sample
function loadSample(key) {
  if (SAMPLES[key]) {
    document.getElementById('raw-clinical-text').value = SAMPLES[key];
    updateTextStats();
  }
}

// Apply Prompt Template
function applyPromptTemplate() {
  const val = document.getElementById('task-prompt-select').value;
  const promptEl = document.getElementById('task-prompt');
  if (PROMPT_TEMPLATES[val]) {
    promptEl.value = PROMPT_TEMPLATES[val];
  }
}

// Update Default Model Name based on Provider
function updateModelDefault() {
  const provider = document.getElementById('adapter-provider').value;
  const modelInput = document.getElementById('model-name');
  if (provider === 'gemini') modelInput.value = 'gemini-3.6-flash';
  else if (provider === 'openai') modelInput.value = 'gpt-4o';
  else if (provider === 'anthropic') modelInput.value = 'claude-3-5-sonnet-20240620';
  else if (provider === 'mock') modelInput.value = 'mock-llm-local';
}

// Highlight and Colorize PHI Tokens in HTML
function colorizeTokens(text) {
  if (!text) return '';
  // Match tokens like [PATIENT_1], [PROVIDER_A], [DATE_1], [HOSPITAL_1], [AGE_90+], [MRN_1], [SSN_1]
  const pattern = /\[([A-Za-z0-9_\+\-]+)\]/g;
  return text.replace(pattern, (match, inner) => {
    const upper = inner.toUpperCase();
    let cls = 'token-generic';
    if (upper.startsWith('PATIENT') || upper.startsWith('FAMILY')) cls = 'token-patient';
    else if (upper.startsWith('PROVIDER') || upper.startsWith('DOCTOR')) cls = 'token-provider';
    else if (upper.startsWith('DATE')) cls = 'token-date';
    else if (upper.startsWith('HOSPITAL') || upper.startsWith('CITY') || upper.startsWith('ADDRESS') || upper.startsWith('ZIP')) cls = 'token-hospital';
    else if (upper.startsWith('AGE')) cls = 'token-age';
    else if (upper.startsWith('MRN') || upper.startsWith('SSN') || upper.startsWith('NPI') || upper.startsWith('PHONE') || upper.startsWith('FAX') || upper.startsWith('LICENSE')) cls = 'token-id';

    return `<span class="phi-token ${cls}">${match}</span>`;
  });
}

// Execute Full Gateway Loop (/gateway/process)
async function runGatewayProcess() {
  const text = document.getElementById('raw-clinical-text').value.trim();
  if (!text) {
    alert('Please enter or upload a clinical note first.');
    return;
  }

  const prompt = document.getElementById('task-prompt').value;
  const provider = document.getElementById('adapter-provider').value;
  const modelName = document.getElementById('model-name').value;
  const btn = document.getElementById('btn-process');

  setLoadingState(true, 'Executing Gateway Pipeline...');
  setPipelineSteps(2);

  const payload = {
    clinical_note: text,
    task_prompt: prompt,
    adapter_provider: provider,
    model_name: modelName,
    date_shift_days: document.getElementById('date-shift-toggle').checked ? -42 : null
  };

  try {
    const res = await fetch(`${BACKEND_URL}/gateway/process`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'accept': 'application/json' },
      body: JSON.stringify(payload)
    });

    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || 'Gateway processing failed');
    }

    const data = await res.json();
    activeResult = data;
    renderResults(data);
    setPipelineSteps(4);
  } catch (err) {
    alert(`Error: ${err.message}. Is the backend server running on http://localhost:8000?`);
  } finally {
    setLoadingState(false);
  }
}

// Execute De-Identify Only (/deidentify)
async function runDeidentifyOnly() {
  const text = document.getElementById('raw-clinical-text').value.trim();
  if (!text) {
    alert('Please enter or upload a clinical note.');
    return;
  }

  setLoadingState(true, 'De-identifying...');
  setPipelineSteps(2);

  const payload = {
    text: text,
    date_shift_days: document.getElementById('date-shift-toggle').checked ? -42 : null,
    preserve_eponyms: document.getElementById('eponym-toggle').checked,
    preserve_relative_dates: true
  };

  try {
    const res = await fetch(`${BACKEND_URL}/deidentify`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'accept': 'application/json' },
      body: JSON.stringify(payload)
    });

    if (!res.ok) throw new Error('De-identification failed');
    const data = await res.json();
    activeResult = {
      masked_input: data.masked_text,
      mapping: data.mapping,
      entity_count: data.entity_count,
      raw_llm_response: '(LLM stage skipped — De-identification only mode)',
      final_text: '(Rehydration pending — run "Rehydrate Only")',
      latency_ms: 0,
      deid_latency_ms: 0,
      leak_check_passed: true
    };
    renderResults(activeResult);
    switchTab('deid');
  } catch (err) {
    alert(`Error: ${err.message}`);
  } finally {
    setLoadingState(false);
  }
}

// Execute Rehydrate Only (/rehydrate)
async function runRehydrateOnly() {
  if (!activeResult || !activeResult.mapping) {
    alert('No active mapping dictionary found. Please run De-Identify first.');
    return;
  }

  const rawResponse = activeResult.raw_llm_response || activeResult.masked_input;
  setLoadingState(true, 'Rehydrating response...');
  setPipelineSteps(4);

  try {
    const res = await fetch(`${BACKEND_URL}/rehydrate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'accept': 'application/json' },
      body: JSON.stringify({
        response: rawResponse,
        mapping: activeResult.mapping
      })
    });

    if (!res.ok) throw new Error('Rehydration failed');
    const data = await res.json();
    activeResult.final_text = data.rehydrated_text;
    renderResults(activeResult);
    switchTab('rehydrate');
  } catch (err) {
    alert(`Error: ${err.message}`);
  } finally {
    setLoadingState(false);
  }
}

// Render Results into UI Elements
function renderResults(data) {
  // 1. Previews in Side-by-Side tab
  document.getElementById('full-masked-preview').innerHTML = colorizeTokens(data.masked_input);
  document.getElementById('full-rehydrated-preview').innerText = data.final_text;

  // 2. Specific tab views
  document.getElementById('deid-view').innerHTML = colorizeTokens(data.masked_input);
  document.getElementById('mapping-view').innerText = JSON.stringify(data.mapping, null, 2);
  document.getElementById('llm-view').innerText = data.raw_llm_response;
  document.getElementById('rehydrate-view').innerText = data.final_text;

  // 3. Mapping Table
  const tbody = document.getElementById('mapping-table-body');
  const tokenMap = data.mapping?.token_to_original || {};
  const entries = Object.entries(tokenMap);
  document.getElementById('mapping-count-badge').innerText = entries.length;

  if (entries.length > 0) {
    tbody.innerHTML = entries.map(([token, orig]) => {
      let cat = 'IDENTIFIER';
      if (token.includes('PATIENT')) cat = 'PATIENT';
      else if (token.includes('PROVIDER')) cat = 'PROVIDER';
      else if (token.includes('DATE')) cat = 'DATE';
      else if (token.includes('HOSPITAL') || token.includes('CITY') || token.includes('ZIP')) cat = 'GEOGRAPHY';
      else if (token.includes('AGE')) cat = 'AGE >= 90';
      else if (token.includes('MRN') || token.includes('SSN') || token.includes('NPI')) cat = 'STRUCTURED ID';

      return `
        <tr class="hover:bg-slate-800/50">
          <td class="py-1.5 px-2">${colorizeTokens(token)}</td>
          <td class="py-1.5 px-2 text-[10px] text-slate-400 font-semibold">${cat}</td>
          <td class="py-1.5 px-2 text-emerald-300 font-semibold">${escapeHtml(orig)}</td>
        </tr>
      `;
    }).join('');
  } else {
    tbody.innerHTML = `<tr><td colspan="3" class="text-center py-4 text-slate-500">No surrogate tokens in this mapping.</td></tr>`;
  }

  // 4. Telemetry HUD
  document.getElementById('telemetry-leak').innerText = data.leak_check_passed ? 'PASSED (0 Leaks)' : 'FAILED';
  document.getElementById('telemetry-entities').innerText = data.entity_count || entries.length;
  document.getElementById('telemetry-deid-lat').innerText = `${(data.deid_latency_ms || 0).toFixed(2)} ms`;
  document.getElementById('telemetry-total-lat').innerText = `${(data.latency_ms || 0).toFixed(2)} ms`;
}

// Switch Result Tabs
function switchTab(tab) {
  currentTab = tab;
  ['full', 'deid', 'mapping', 'llm', 'rehydrate'].forEach(t => {
    const el = document.getElementById(`tab-${t}`);
    const btn = document.getElementById(`tab-btn-${t}`);
    if (t === tab) {
      el.classList.remove('hidden');
      btn.className = 'tab-btn px-3 py-1.5 rounded-lg bg-cyan-500/20 text-cyan-300 font-semibold border border-cyan-500/30';
    } else {
      el.classList.add('hidden');
      btn.className = 'tab-btn px-3 py-1.5 rounded-lg text-slate-400 hover:text-slate-200';
    }
  });
  lucide.createIcons();
}

// Copy Outputs
function copyCurrentOutput() {
  if (!activeResult) return;
  let text = '';
  if (currentTab === 'full' || currentTab === 'rehydrate') text = activeResult.final_text;
  else if (currentTab === 'deid') text = activeResult.masked_input;
  else if (currentTab === 'mapping') text = JSON.stringify(activeResult.mapping, null, 2);
  else if (currentTab === 'llm') text = activeResult.raw_llm_response;

  navigator.clipboard.writeText(text).then(() => alert('Copied to clipboard!'));
}

function copyText(elemId) {
  const el = document.getElementById(elemId);
  navigator.clipboard.writeText(el.innerText).then(() => alert('Copied to clipboard!'));
}

// Helpers
function setLoadingState(isLoading, message = 'Processing...') {
  const btn = document.getElementById('btn-process');
  if (isLoading) {
    btn.disabled = true;
    btn.innerHTML = `<i data-lucide="loader-2" class="w-4 h-4 animate-spin"></i><span>${message}</span>`;
  } else {
    btn.disabled = false;
    btn.innerHTML = `<i data-lucide="play" class="w-4 h-4 fill-current"></i><span>Execute Full Gateway Loop</span>`;
  }
  lucide.createIcons();
}

function setPipelineSteps(step) {
  for (let i = 1; i <= 4; i++) {
    const circle = document.getElementById(`step-${i}-circle`);
    if (i < step) circle.className = 'step-circle step-completed';
    else if (i === step) circle.className = 'step-circle step-active';
    else circle.className = 'step-circle step-idle';
  }
}

function escapeHtml(str) {
  return (str || '').replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
}

function toggleTheme() {
  document.documentElement.classList.toggle('dark');
}
