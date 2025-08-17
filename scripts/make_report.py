import json
import os
import html
from typing import Any, List, Dict

def generate_html_report(results: List[Dict[str, Any]], input_path: str = "results.json", output_path: str = "report.html", title: str = "Automation Test Report"):
    """
    Generate a single-file responsive interactive HTML report from test results JSON.

    Args:
        results: List of test result dicts.
        input_path: Json Path to read test results 
        output_path: Path to write the HTML file.
        title: Page title shown on the report.
    """

    # Basic aggregates
    total = len(results)
    passed = sum(1 for r in results if (r.get("status") or "").lower() == "passed")
    failed = sum(1 for r in results if (r.get("status") or "").lower() == "failed")
    skipped = sum(1 for r in results if (r.get("status") or "").lower() == "skipped")
    total_duration = sum(float(r.get("duration_sec", 0) or 0) for r in results)

    # Safely embed results JSON for client-side JS. Escape '</' to avoid closing the script tag.
    results_json = json.dumps(results).replace("</", "<\\/")
    safe_title = html.escape(title)

    html_template = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>__TITLE__</title>

  <!-- Tailwind (CDN) -->
  <script src="https://cdn.tailwindcss.com"></script>
  <!-- Chart.js -->
  <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>

  <style>
    .modal-backdrop { background: rgba(0,0,0,0.5); }
    .step-clickable { 
      cursor: pointer; 
      transition: all 0.2s ease; 
    }
    .step-clickable:hover { 
      transform: translateX(4px); 
      box-shadow: 0 4px 12px rgba(0,0,0,0.15); 
    }
  </style>
</head>
<body class="bg-gray-100 text-gray-900 p-4">
  <div class="max-w-7xl mx-auto py-4">
    <header class="flex flex-col sm:flex-row sm:justify-between sm:items-center mb-8">
      <h1 class="text-3xl font-bold">__TITLE__</h1>
      <div class="mt-3 sm:mt-0">
        <button id="downloadJson" class="px-3 py-1 border rounded text-sm">Download JSON</button>
      </div>
    </header>

    <!-- Summary cards -->
    <div class="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-4 mb-6">
      <div class="bg-white p-4 rounded shadow"><div class="text-sm text-gray-500">Total</div><div class="text-2xl font-bold">__TOTAL__</div></div>
      <div class="bg-white p-4 rounded shadow"><div class="text-sm text-green-700">Passed</div><div class="text-2xl font-bold text-green-800">__PASSED__</div></div>
      <div class="bg-white p-4 rounded shadow"><div class="text-sm text-red-700">Failed</div><div class="text-2xl font-bold text-red-800">__FAILED__</div></div>
      <div class="bg-white p-4 rounded shadow"><div class="text-sm text-blue-700">Skipped</div><div class="text-2xl font-bold text-blue-800">__SKIPPED__</div></div>
    </div>

    <!-- Charts -->
    <div class="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
      <div class="bg-white p-4 rounded shadow"><h3 class="font-semibold mb-2">Status distribution</h3><canvas id="statusChart"></canvas></div>
      <div class="bg-white p-4 rounded shadow"><h3 class="font-semibold mb-2">Durations (s)</h3><canvas id="durationChart"></canvas></div>
    </div>

    <!-- Controls -->
    <div class="mb-4 flex gap-2 items-center">
      <input id="searchInput" class="px-3 py-2 border rounded flex-1" placeholder="Search by test_id, name, device_id, tags..." />
      <select id="statusFilter" class="px-3 py-2 border rounded">
        <option value="">All</option>
        <option value="passed">Passed</option>
        <option value="failed">Failed</option>
        <option value="skipped">Skipped</option>
      </select>
    </div>

    <!-- Tests list (populated by JS) -->
    <div id="testsList" class="card bg-white p-4 rounded"></div>
  </div>

  <!-- Step Modal -->
  <div id="stepModal" class="hidden fixed inset-0 modal-backdrop z-50 flex items-center justify-center p-4">
    <div class="bg-white rounded-lg shadow-2xl w-full max-w-6xl max-h-[90vh] overflow-hidden">
      <div class="flex justify-between items-center p-6 border-b border-gray-200">
        <h2 id="modalTitle" class="text-2xl font-bold text-gray-800">Step Details</h2>
        <button id="closeModal" class="text-gray-400 hover:text-gray-600 text-2xl font-bold">&times;</button>
      </div>
      <div id="modalContent" class="p-6 overflow-y-auto max-h-[calc(90vh-80px)]"></div>
    </div>
  </div>

  <script>
    // Embedded results JSON
    const results = __RESULTS_JSON__;
    let allResults = [...results]; // Keep original results for charts

    function openStepModalByIndex(testIdx, stepId) {
        openStepModal(results[testIdx], stepId);  // wrapper
    }

    // Utility: safe text for HTML insertion (minimal)
    function escHtml(s){ if(s===null||s===undefined) return ''; return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;'); }

    // Function to open step modal with detailed information
    function openStepModal(testData, stepId) {
      const testId = testData.test_id;
      const step = testData.steps.find(s => s.step_id === stepId);
      if (!step) return;

      const modal = document.getElementById('stepModal');
      const title = document.getElementById('modalTitle');
      const content = document.getElementById('modalContent');

      title.textContent = `${stepId.toUpperCase()} - ${step.name || ''}`;

      // Build detailed step information
      let modalHtml = `
        <div class="space-y-6">
          <!-- Step Overview -->
          <div class="bg-gray-50 p-4 rounded-lg">
            <h3 class="text-lg font-semibold mb-3 text-gray-800">Step Information</h3>
            <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div><strong>Step ID:</strong> ${escHtml(step.step_id || '')}</div>
              <div><strong>Status:</strong> 
                <span class="px-2 py-1 rounded text-sm ${step.status === 'passed' ? 'bg-green-100 text-green-800' : step.status === 'failed' ? 'bg-red-100 text-red-800' : 'bg-yellow-100 text-yellow-800'}">
                  ${escHtml(step.status || '')}
                </span>
              </div>
              <div><strong>Duration:</strong> ${step.duration_sec ? Number(step.duration_sec).toFixed(2) + 's' : 'N/A'}</div>
              <div><strong>Timestamp:</strong> ${step.timestamp ? new Date(step.timestamp * 1000).toLocaleString() : 'N/A'}</div>
            </div>
            <div class="mt-3">
              <strong>Description:</strong> ${escHtml(step.description || 'No description available')}
            </div>
          </div>`;

      // Assertions section
      if (step.assertions && step.assertions.length > 0) {
        modalHtml += `
          <div class="bg-white border border-gray-200 p-4 rounded-lg">
            <h3 class="text-lg font-semibold mb-3 text-gray-800">Assertions (${step.assertions.length})</h3>
            <div class="space-y-3">`;

        step.assertions.forEach((assertion, idx) => {
          const statusColor = assertion.status === 'passed' ? 'bg-green-50 border-green-200' : 'bg-red-50 border-red-200';
          const statusIcon = assertion.status === 'passed' ? '✓' : '✗';
          const statusTextColor = assertion.status === 'passed' ? 'text-green-700' : 'text-red-700';

          modalHtml += `
            <div class="border rounded-lg p-3 ${statusColor}">
              <div class="flex items-center justify-between mb-2">
                <div class="flex items-center space-x-2">
                  <span class="font-bold ${statusTextColor}">${statusIcon}</span>
                  <span class="font-medium">${escHtml(assertion.name || `Assertion ${idx + 1}`)}</span>
                </div>
                <span class="text-sm px-2 py-1 rounded ${assertion.status === 'passed' ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'}">
                  ${escHtml(assertion.status || '')}
                </span>
              </div>
              <div class="text-sm text-gray-600">
                <div><strong>Type:</strong> ${escHtml(assertion.type || 'N/A')}</div>`;

          if (assertion.expected !== undefined) {
            modalHtml += `
                <div class="mt-2">
                  <strong>Expected:</strong>
                  <pre class="mt-1 p-2 bg-gray-100 rounded text-xs overflow-x-auto">${escHtml(typeof assertion.expected === 'object' ? JSON.stringify(assertion.expected, null, 2) : assertion.expected)}</pre>
                </div>`;
          }

          if (assertion.actual !== undefined) {
            modalHtml += `
                <div class="mt-2">
                  <strong>Actual:</strong>
                  <pre class="mt-1 p-2 bg-gray-100 rounded text-xs overflow-x-auto">${escHtml(typeof assertion.actual === 'object' ? JSON.stringify(assertion.actual, null, 2) : assertion.actual)}</pre>
                </div>`;
          }

          modalHtml += `
              </div>
            </div>`;
        });

        modalHtml += `
            </div>
          </div>`;
      }

      // Artifacts section
      if (step.artifacts && Object.keys(step.artifacts).length > 0) {
        modalHtml += `
          <div class="bg-white border border-gray-200 p-4 rounded-lg">
            <h3 class="text-lg font-semibold mb-3 text-gray-800">Artifacts</h3>
            <div class="space-y-2">`;

        Object.entries(step.artifacts).forEach(([key, value]) => {
          modalHtml += `
            <div class="flex justify-between items-center p-2 bg-gray-50 rounded">
              <span class="font-medium">${escHtml(key)}:</span>
              <span class="text-sm text-gray-600">${escHtml(value)}</span>
            </div>`;
        });

        modalHtml += `
            </div>
          </div>`;
      }

      // Logs section (if available)
      if (step.logs) {
        modalHtml += `
          <div class="bg-white border border-gray-200 p-4 rounded-lg">
            <h3 class="text-lg font-semibold mb-3 text-gray-800">Logs</h3>
            <pre class="bg-gray-900 text-green-400 p-4 rounded text-sm overflow-x-auto max-h-64">${escHtml(step.logs)}</pre>
          </div>`;
      }

      modalHtml += `</div>`;

      content.innerHTML = modalHtml;
      modal.classList.remove('hidden');
    }

    // Close modal functionality
    function closeModal() {
      document.getElementById('stepModal').classList.add('hidden');
    }

    document.getElementById('closeModal').addEventListener('click', closeModal);
    document.getElementById('stepModal').addEventListener('click', (e) => {
      if (e.target === document.getElementById('stepModal')) closeModal();
    });

    // Escape key to close modal
    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape') closeModal();
    });

    function createStepsSection(steps, testIndex){
      return steps.map(step=>{
        const borderColor = (step.status||'').toLowerCase()==='passed'?'border-green-500':(step.status||'').toLowerCase()==='failed'?'border-red-500':'border-yellow-500';
        const assertionsHtml = (step.assertions||[]).map(a=>{
          const bulletColor = (a.status||'').toLowerCase()==='passed'?'bg-green-500':'bg-red-500';
          return `<li class="flex items-center space-x-2"><span class="w-2 h-2 rounded-full ${bulletColor} inline-block"></span><span>${escHtml(a.name||'')}</span></li>`;
        }).join('');

        return `<div class="step step-clickable border border-r-4 bg-white p-4 hover:scale-105 transition-transform duration-300 ${borderColor} pr-3 py-2 mb-3" 
        onclick="openStepModalByIndex(${testIndex}, '${step.step_id}')" 
        title="Click to view detailed step information">
          <div class="flex justify-between items-center">
            <span class="font-semibold">${escHtml(step.step_id||'').toUpperCase()} - ${escHtml(step.name||'')}</span>
            <div class="flex items-center space-x-2">
              <span class="text-sm text-gray-500">${step.duration_sec?Number(step.duration_sec).toFixed(2)+'s':''}</span>
              <span class="text-xs text-blue-600">👁️ Click for details</span>
            </div>
          </div>
          <div class="text-xs text-gray-700 mt-1">${escHtml(step.description||'')}</div>
          ${assertionsHtml?`<ul class="mt-2 text-sm space-y-1">${assertionsHtml}</ul>`:''}
        </div>`;
      }).join('') + `</div>`;
    }

    function renderTests(list){
        const container = document.getElementById('testsList');
        container.innerHTML = '';

        list.forEach((test, idx) => {
            const status      = (test.status||'').toLowerCase();
            const statusClass = status==='passed'
                ? 'bg-green-100 text-green-800'
                : status==='failed'
                ? 'bg-red-100 text-red-800'
                : 'bg-yellow-100 text-yellow-800';
            
            const borderColor = (status||'').toLowerCase()==='passed'?'border-green-500':(status||'').toLowerCase()==='failed'?'border-red-500':'border-yellow-500';

            const openClass = idx === 0 ? '' : 'hidden';      // first open
            const rotate    = idx === 0 ? 'rotate-180' : '';  // chevron down vs up

            container.insertAdjacentHTML('beforeend', `
            <div class="bg-white rounded shadow mb-4 border-r-4 ${borderColor}">
                <button class="w-full flex justify-between items-center p-4 accordion-header" data-idx="${idx}">
                  <div>
                      <div class="text-xl font-semibold text-start">${escHtml(test.test_id)} – ${escHtml(test.name)}</div>
                      <div class="text-sm text-gray-700 text-start">Device: ${escHtml(test.device_id)} | Driver: ${escHtml(test.driver)}</div>
                  </div>

                  <div class="flex items-center space-x-3">
                      <div class="flex items-center space-x-3">
                        <a class="p-2 rounded text-xs bg-blue-100 font-semibold">screen recording</a>
                        <a class="p-2 rounded text-xs bg-blue-100 font-semibold">system logs</a>
                        <a class="p-2 rounded text-xs bg-blue-100 font-semibold">framework logs</a>
                      </div>
                      <svg class="w-5 h-5 transition-transform duration-300 ${rotate}" fill="none"
                          stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
                          <path stroke-linecap="round" stroke-linejoin="round" d="M19 9l-7 7-7-7"/>
                      </svg>
                  </div>
                </button>

                <div id="body-${idx}" class="accordion-body ${openClass} p-4 pt-0">
                ${createStepsSection(test.steps || [], idx)}
                </div>
            </div>`);
        });

        // toggle listener
        document.querySelectorAll('.accordion-header').forEach(btn => {
            btn.onclick = () => {
            const idx  = btn.dataset.idx;
            const body = document.getElementById(`body-${idx}`);
            const icon = btn.querySelector('svg');
            body.classList.toggle('hidden');
            icon.classList.toggle('rotate-180');
            };
        });
    }


    // Search & filter - MODIFIED: Only updates testsList, not charts
    const searchInput = document.getElementById('searchInput');
    const statusFilter = document.getElementById('statusFilter');

    function applyFilters() {
      const q = (searchInput.value || '').toLowerCase().trim();
      const status = (statusFilter.value || '').toLowerCase();
      const filtered = results.filter(t => {
        if (status && (t.status||'').toLowerCase() !== status) return false;
        if (!q) return true;
        const hay = ((t.test_id||'') + ' ' + (t.name||'') + ' ' + (t.device_id||'') + ' ' + ((t.tags && t.tags.join(' '))||'')).toLowerCase();
        return hay.includes(q);
      });
      // CHANGE: Only update the tests list, keep charts with original data
      renderTests(filtered);
    }

    searchInput.addEventListener('input', applyFilters);
    statusFilter.addEventListener('change', applyFilters);

    // Download JSON
    document.getElementById('downloadJson').addEventListener('click', () => {
      const blob = new Blob([JSON.stringify(results, null, 2)], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url; a.download = 'results.json'; document.body.appendChild(a); a.click(); a.remove(); URL.revokeObjectURL(url);
    });

    // CHANGE: buildCharts now only runs once with all results, not filtered results
    function buildCharts(list){
      const passed=list.filter(r=>(r.status||'').toLowerCase()==='passed').length;
      const failed=list.filter(r=>(r.status||'').toLowerCase()==='failed').length;
      const skipped=list.filter(r=>(r.status||'').toLowerCase()==='skipped').length;
      if(window._statusChart) window._statusChart.destroy();
      window._statusChart=new Chart(document.getElementById('statusChart'),{type:'doughnut',data:{labels:['Passed','Failed','Skipped'],datasets:[{data:[passed,failed,skipped],backgroundColor:['#10B981','#EF4444','#F59E0B']}]}});
      if(window._durChart) window._durChart.destroy();
      window._durChart=new Chart(document.getElementById('durationChart'),{type:'bar',data:{labels:list.map(r=>r.test_id||''),datasets:[{label:'Duration (s)',data:list.map(r=>Number(r.duration_sec)||0),backgroundColor:'#3B82F6'}]},options:{scales:{y:{beginAtZero:true}}}});
    }

    // Initialize with all results
    renderTests(results);
    buildCharts(allResults); // Charts always show all results
  </script>
</body>
</html>"""

    html_output = html_template.replace('__TITLE__', safe_title)
    html_output = html_output.replace('__TOTAL__', str(total))
    html_output = html_output.replace('__PASSED__', str(passed))
    html_output = html_output.replace('__FAILED__', str(failed))
    html_output = html_output.replace('__SKIPPED__', str(skipped))
    html_output = html_output.replace('__RESULTS_JSON__', results_json)

    os.makedirs(os.path.dirname(output_path) or '.', exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as fh:
        fh.write(html_output)
    return output_path



if __name__ == '__main__':
    src = 'artifacts/results/results.json'
    out = 'artifacts/results/results.html'
    try:
        with open(src, 'r', encoding='utf-8') as fh:
            data = json.load(fh)
    except Exception as e:
        print('Error reading JSON', e)
        data = []
    out_path = generate_html_report(data, output_path=out, title="Sanity Automation Test Reprt")
    print('Report generated:', out_path)
