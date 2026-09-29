// ========================================================
// API Configuration for Decoupled Frontend/Backend Deployment
// ========================================================
const API_BASE_URL = window.ENV_API_URL || 
    (window.location.port === '3000' || window.location.port === '5173' || window.location.protocol === 'file:' 
        ? 'http://localhost:8000' 
        : '');

const jdSelect = document.getElementById('jd-select');
        const runBtn = document.getElementById('run-btn');
        const runSpinner = document.getElementById('run-spinner');
        const btnText = document.getElementById('btn-text');
        const resultsContainer = document.getElementById('results-container');
        const metricsSummary = document.getElementById('metrics-summary');
        
        const countHigh = document.getElementById('count-high');
        const countRec = document.getElementById('count-rec');
        const countConsider = document.getElementById('count-consider');
        const countNot = document.getElementById('count-not');
        const statPool = document.getElementById('stat-pool');

        const domainCard = document.getElementById('domain-card');
        const domainNameBadge = document.getElementById('domain-name-badge');
        const domainSummaryText = document.getElementById('domain-summary-text');
        const weightsList = document.getElementById('weights-list');

        let allCandidates = [];
        let currentSelectedJD = "";
        let activeHRQueries = [];
        let totalSystemResumes = 280;

        async function fetchJobs() {
            try {
                const response = await fetch(`${API_BASE_URL}/api/jobs');
                const data = await response.json();
                jdSelect.innerHTML = '<option value="">-- Select Job Description --</option>';
                data.forEach(job => {
                    const opt = document.createElement('option');
                    opt.value = job.filename;
                    opt.textContent = `[${job.domain}] ${job.title}`;
                    jdSelect.appendChild(opt);
                });
                jdSelect.addEventListener('change', () => {
                    runBtn.disabled = !jdSelect.value;
                });

                const rRes = await fetch(`${API_BASE_URL}/api/resumes');
                const rData = await rRes.json();
                totalSystemResumes = Array.isArray(rData) ? rData.length : (rData.total_count || 280);
                if (statPool) statPool.textContent = `20 evaluated out of ${totalSystemResumes} Resumes`;
                if (data && data.length > 0) {
                    const defaultJob = data.find(j => j.filename.includes('react') || j.filename.includes('devops')) || data[0];
                    jdSelect.value = defaultJob.filename;
                    runBtn.disabled = false;
                    runScreeningPipeline();
                }
            } catch (err) {
                console.error(err);
            }
        }

        function addCustomHRQuery() {
            const input = document.getElementById('hr-q-input');
            const impSelect = document.getElementById('hr-q-importance');
            const text = (input ? input.value : '').trim();
            const imp = impSelect ? impSelect.value : 'Important';
            if (!text) return alert('Please enter a custom HR question or requirement.');
            
            const newQ = { id: 'hr_' + Date.now(), question: text, importance: imp };
            activeHRQueries.push(newQ);
            if (input) input.value = '';
            renderHRQueries();
        }

        function addHRPreset(question, importance) {
            if (activeHRQueries.some(q => q.question.toLowerCase() === question.toLowerCase())) {
                showToast("✓ Requirement already added to active queries");
                return;
            }
            activeHRQueries.push({ id: 'hr_' + Date.now(), question: question, importance: importance });
            renderHRQueries();
            showToast("✓ Added HR query preset");
        }

        function removeHRQuery(id) {
            activeHRQueries = activeHRQueries.filter(q => q.id !== id);
            renderHRQueries();
        }

        function renderHRQueries() {
            const listContainer = document.getElementById('hr-query-list');
            const countSpan = document.getElementById('hr-q-count');
            if (countSpan) countSpan.textContent = activeHRQueries.length;
            
            if (!listContainer) return;
            if (activeHRQueries.length === 0) {
                listContainer.innerHTML = `<div style="font-size:0.75rem; color:#94a3b8; font-style:italic;">No custom queries added. Click quick presets above or type a question.</div>`;
                return;
            }

            let html = "";
            activeHRQueries.forEach(q => {
                let badgeColor = "background:rgba(99, 102, 241, 0.2); color:#c7d2fe; border:1px solid rgba(99, 102, 241, 0.4);";
                if (q.importance === "Required") badgeColor = "background:rgba(239, 68, 68, 0.2); color:#fca5a5; border:1px solid rgba(239, 68, 68, 0.4);";
                else if (q.importance === "Optional") badgeColor = "background:rgba(255, 255, 255, 0.08); color:#cbd5e1; border:1px solid rgba(255, 255, 255, 0.12);";

                html += `
                    <div style="display:flex; justify-content:space-between; align-items:center; background:rgba(15,23,42,0.6); padding:0.35rem 0.6rem; border-radius:6px; border:1px solid var(--glass-border);">
                        <div style="font-size:0.76rem; color:#e2e8f0; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; max-width:180px;" title="${q.question}">
                            <span style="font-size:0.68rem; padding:0.1rem 0.35rem; border-radius:4px; margin-right:0.3rem; ${badgeColor}">${q.importance}</span>
                            ${q.question}
                        </div>
                        <button onclick="removeHRQuery('${q.id}')" style="background:none; border:none; color:#fca5a5; font-size:0.9rem; cursor:pointer; font-weight:700; padding:0 0.2rem;">&times;</button>
                    </div>
                `;
            });
            listContainer.innerHTML = html;
        }

        // ========================================================
        // Aesthetic Reloader Controller & Shimmer Skeletons
        // ========================================================
        let reloaderInterval = null;

        function renderSkeletonCards() {
            return `
                <div class="skeleton-grid">
                    ${[1, 2, 3].map(i => `
                        <div class="skeleton-card">
                            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:1rem;">
                                <div style="display:flex; gap:0.65rem; align-items:center;">
                                    <div class="skeleton-pill" style="width:34px; height:24px;"></div>
                                    <div class="skeleton-pill" style="width:160px; height:22px;"></div>
                                </div>
                                <div class="skeleton-pill" style="width:110px; height:26px; border-radius:12px;"></div>
                            </div>
                            <div class="skeleton-pill" style="width:55%; height:14px; margin-bottom:0.75rem;"></div>
                            <div class="skeleton-pill" style="width:90%; height:14px; margin-bottom:1.25rem;"></div>
                            <div style="display:grid; grid-template-columns:repeat(auto-fit, minmax(100px, 1fr)); gap:0.65rem;">
                                <div class="skeleton-pill" style="height:48px; border-radius:8px;"></div>
                                <div class="skeleton-pill" style="height:48px; border-radius:8px;"></div>
                                <div class="skeleton-pill" style="height:48px; border-radius:8px;"></div>
                                <div class="skeleton-pill" style="height:48px; border-radius:8px;"></div>
                            </div>
                        </div>
                    `).join('')}
                </div>
            `;
        }

        function showAestheticReloader(jobTitle = "") {
            const overlay = document.getElementById('agent-reloader-overlay');
            const subTitle = document.getElementById('reloader-status-subtitle');
            const phaseText = document.getElementById('reloader-phase-text');
            const percentText = document.getElementById('reloader-percent-text');
            const barFill = document.getElementById('reloader-bar-fill');
            const reloadBtn = document.getElementById('btn-header-reload');
            
            if (reloadBtn) reloadBtn.classList.add('is-reloading');
            if (subTitle && jobTitle) subTitle.textContent = `Screening & evaluating candidates for ${jobTitle}...`;
            
            // Reset steps
            for (let i = 1; i <= 5; i++) {
                const s = document.getElementById(`step-item-${i}`);
                const b = document.getElementById(`step-badge-${i}`);
                if (s) { s.classList.remove('active', 'completed'); }
                if (b) { b.textContent = i; }
            }
            const s1 = document.getElementById('step-item-1');
            if (s1) s1.classList.add('active');

            if (barFill) barFill.style.width = '15%';
            if (percentText) percentText.textContent = '15%';
            if (phaseText) phaseText.textContent = 'Phase 1 / 5: Domain Classification';

            if (overlay) overlay.classList.add('active');

            // Smooth progressive animation across LangGraph stages
            const stages = [
                { progress: 34, phase: 'Phase 2 / 5: Concurrent Profile Extraction', step: 2 },
                { progress: 60, phase: 'Phase 3 / 5: FAISS Dense Vector Similarity', step: 3 },
                { progress: 80, phase: 'Phase 4 / 5: Scipy Empirical Pool Percentiles', step: 4 },
                { progress: 94, phase: 'Phase 5 / 5: Recruiter Synthesis & Quartiles', step: 5 }
            ];

            let stageIdx = 0;
            clearInterval(reloaderInterval);
            reloaderInterval = setInterval(() => {
                if (stageIdx < stages.length) {
                    const st = stages[stageIdx];
                    if (barFill) barFill.style.width = `${st.progress}%`;
                    if (percentText) percentText.textContent = `${st.progress}%`;
                    if (phaseText) phaseText.textContent = st.phase;

                    for (let k = 1; k < st.step; k++) {
                        const prev = document.getElementById(`step-item-${k}`);
                        const prevB = document.getElementById(`step-badge-${k}`);
                        if (prev) { prev.classList.remove('active'); prev.classList.add('completed'); }
                        if (prevB) { prevB.textContent = '✓'; }
                    }
                    const curr = document.getElementById(`step-item-${st.step}`);
                    if (curr) curr.classList.add('active');
                    stageIdx++;
                }
            }, 420);
        }

        function hideAestheticReloader() {
            clearInterval(reloaderInterval);
            const overlay = document.getElementById('agent-reloader-overlay');
            const percentText = document.getElementById('reloader-percent-text');
            const barFill = document.getElementById('reloader-bar-fill');
            const phaseText = document.getElementById('reloader-phase-text');
            const reloadBtn = document.getElementById('btn-header-reload');

            if (reloadBtn) reloadBtn.classList.remove('is-reloading');

            if (barFill) barFill.style.width = '100%';
            if (percentText) percentText.textContent = '100%';
            if (phaseText) phaseText.textContent = '✓ Multi-Agent Pipeline Completed';

            for (let i = 1; i <= 5; i++) {
                const s = document.getElementById(`step-item-${i}`);
                const b = document.getElementById(`step-badge-${i}`);
                if (s) { s.classList.remove('active'); s.classList.add('completed'); }
                if (b) { b.textContent = '✓'; }
            }

            setTimeout(() => {
                if (overlay) overlay.classList.remove('active');
            }, 360);
        }

        function triggerPipelineReload() {
            runScreeningPipeline();
        }

        async function runScreeningPipeline() {
            const val = jdSelect.value;
            if (!val) return;
            currentSelectedJD = val;

            const selectedText = jdSelect.options[jdSelect.selectedIndex] ? jdSelect.options[jdSelect.selectedIndex].text : '';
            const rankingModeSelect = document.getElementById('ranking-mode-select');
            const rankingMode = rankingModeSelect ? rankingModeSelect.value : 'overall_percentile';

            runBtn.disabled = true;
            runSpinner.style.display = 'inline-block';
            btnText.textContent = 'Evaluating Multi-Agent Pipeline...';
            
            // Show shimmering skeleton placeholders & modal reloader
            resultsContainer.innerHTML = renderSkeletonCards();
            metricsSummary.style.display = 'none';
            showAestheticReloader(selectedText);

            try {
                const response = await fetch(`${API_BASE_URL}/api/screen', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ 
                        jd_filename: val,
                        hr_queries: activeHRQueries,
                        ranking_mode: rankingMode
                    })
                });
                
                if (!response.ok) {
                    const errDetail = await response.json();
                    throw new Error(errDetail.detail || "Server error");
                }
                
                const resData = await response.json();
                renderResults(resData.dashboard_data);
                
                if (activeHRQueries.length > 0) {
                    showToast(`✓ Evaluated ${activeHRQueries.length} custom HR queries against candidate resumes!`);
                } else {
                    showToast(`✓ Candidate screening diagnostics completed successfully!`);
                }

                document.getElementById('btn-dl-pdf').style.display = 'inline-block';
                document.getElementById('btn-dl-md').style.display = 'inline-block';
            } catch (err) {
                resultsContainer.innerHTML = `<div class="no-data" style="color:var(--tier-not);">Pipeline Execution Error: ${err.message}</div>`;
            } finally {
                runBtn.disabled = false;
                runSpinner.style.display = 'none';
                btnText.textContent = 'Run Diagnostics';
                hideAestheticReloader();
            }
        }

        runBtn.addEventListener('click', runScreeningPipeline);

        function renderResults(data) {
            allCandidates = data.candidates;
            if (statPool) statPool.textContent = `${allCandidates.length || 20} evaluated out of ${totalSystemResumes || 280} Resumes`;
            
            // Domain Card
            const dInfo = data.domain_info || {};
            domainNameBadge.textContent = dInfo.domain_name || "General";
            domainSummaryText.textContent = dInfo.domain_summary || "";
            
            let weightsHtml = "";
            const weights = dInfo.weights || {};
            for (const [k, v] of Object.entries(weights)) {
                if (v > 0) {
                    const pct = Math.round(v * 100);
                    const title = k.replace('_', ' ').toUpperCase();
                    weightsHtml += `
                        <div>
                            <div class="weight-row">
                                <span>${title}</span>
                                <span>${pct}%</span>
                            </div>
                            <div class="weight-bar-bg">
                                <div class="weight-bar-fill" style="width: ${pct}%;"></div>
                            </div>
                        </div>
                    `;
                }
            }
            weightsList.innerHTML = weightsHtml;
            domainCard.style.display = 'block';

            // Metrics Summary
            const counts = data.quantiles_count || {};
            countHigh.textContent = counts["Q1"] || 0;
            countRec.textContent = counts["Q2"] || 0;
            countConsider.textContent = counts["Q3"] || 0;
            countNot.textContent = counts["Q4"] || 0;
            metricsSummary.style.display = 'grid';

            filterAndRenderCandidates();
        }

        let activeFilterType = 'all';

        function setCandidateFilterType(type) {
            activeFilterType = type;
            const btnAll = document.getElementById('filter-all-btn');
            const btnCustom = document.getElementById('filter-custom-btn');
            if (btnAll) btnAll.classList.toggle('active', type === 'all');
            if (btnCustom) btnCustom.classList.toggle('active', type === 'custom');
            filterAndRenderCandidates();
        }

        function clearCandidateSearch() {
            const input = document.getElementById('candidate-search-input');
            if (input) input.value = '';
            const clearBtn = document.getElementById('clear-search-btn');
            if (clearBtn) clearBtn.style.display = 'none';
            filterAndRenderCandidates();
        }

        function filterAndRenderCandidates() {
            const searchInput = document.getElementById('candidate-search-input');
            const query = searchInput ? (searchInput.value || '').trim().toLowerCase() : '';
            const clearBtn = document.getElementById('clear-search-btn');
            if (clearBtn) clearBtn.style.display = query ? 'inline-block' : 'none';

            if (!allCandidates || allCandidates.length === 0) return;

            const benchmarkPrefixes = ["hc_", "law_", "fin_", "eng_", "fe_", "ds_", "ai_", "fs_"];

            const filtered = allCandidates.filter(c => {
                const rName = (c.resume_json ? c.resume_json.name : '').toLowerCase();
                const rEmail = (c.resume_json ? c.resume_json.email : '').toLowerCase();
                const rPath = (c.resume_path || '').toLowerCase();
                const rFilename = rPath.split('/').pop() || '';
                const hrLabel = (c.hr_fit_label || '').toLowerCase();
                const skills = (c.resume_json && Array.isArray(c.resume_json.skills) ? c.resume_json.skills.join(' ') : '').toLowerCase();

                const isCustom = !benchmarkPrefixes.some(prefix => rFilename.startsWith(prefix));

                if (activeFilterType === 'custom' && !isCustom) {
                    return false;
                }

                if (!query) return true;

                return rName.includes(query) ||
                       rEmail.includes(query) ||
                       rFilename.includes(query) ||
                       rPath.includes(query) ||
                       hrLabel.includes(query) ||
                       skills.includes(query) ||
                       (c.candidate_label || '').toLowerCase().includes(query);
            });

            renderCandidateTable(filtered, query);
        }

        function renderCandidateTable(candidatesToDisplay, searchFilterQuery = '') {
            const container = document.getElementById('results-container');
            const matchCounter = document.getElementById('match-counter');

            if (matchCounter) {
                if (searchFilterQuery || activeFilterType === 'custom') {
                    matchCounter.textContent = `Showing ${candidatesToDisplay.length} of ${allCandidates.length} candidates`;
                } else {
                    matchCounter.textContent = `Total Candidates: ${allCandidates.length}`;
                }
            }

            if (!candidatesToDisplay || candidatesToDisplay.length === 0) {
                container.innerHTML = `
                    <div class="no-data">
                        ${searchFilterQuery ? `No candidates found matching "<strong>${searchFilterQuery}</strong>"` : 'No custom uploaded resumes found for this screening pool.'}
                    </div>
                `;
                return;
            }

            let html = `
                <table>
                    <thead>
                        <tr>
                            <th>Rank</th>
                            <th>Candidate Name</th>
                            <th>Skill Percentile</th>
                            <th>Exp Percentile</th>
                            <th>Cert Percentile</th>
                            <th>Percentile Rank</th>
                            <th>Category Tier</th>
                            <th>Action</th>
                        </tr>
                    </thead>
                    <tbody>
            `;

            candidatesToDisplay.forEach(c => {
                let tierClass = "tier-not";
                if (c.candidate_label === "Highly Recommended") tierClass = "tier-high";
                else if (c.candidate_label === "Recommended") tierClass = "tier-rec";
                else if (c.candidate_label === "Consider") tierClass = "tier-consider";

                let hrClass = "tier-not";
                const hrLabel = c.hr_fit_label || "";
                if (hrLabel === "Strong Fit") hrClass = "tier-high";
                else if (hrLabel === "Moderate Fit") hrClass = "tier-rec";
                else if (hrLabel === "Weak Fit") hrClass = "tier-not";

                const rName = c.resume_json ? c.resume_json.name : "Candidate";
                const rEmail = c.resume_json ? c.resume_json.email : "";
                const safeName = (rName || "").replace(/'/g, "");

                const perc = c.percentile_score !== undefined ? c.percentile_score : c.final_score;
                const techP = c.technical_percentile !== undefined ? c.technical_percentile : c.technical_score;
                const expP = c.experience_percentile !== undefined ? c.experience_percentile : c.experience_score;
                const certP = c.certification_percentile !== undefined ? c.certification_percentile : c.certification_score;

                const showHRBadge = hrLabel && (activeHRQueries.length > 0 || (c.hr_query_results && c.hr_query_results.length > 0));

                html += `
                    <tr class="table-row" onclick="showDetails(${c.candidate_rank})">
                        <td><strong>#${c.candidate_rank}</strong></td>
                        <td>
                            <div style="font-weight: 700;">${rName}</div>
                            <div style="font-size: 0.75rem; color: var(--text-secondary);">${rEmail}</div>
                            ${showHRBadge ? `<div style="margin-top:0.25rem;"><span class="tier-tag ${hrClass}" style="font-size:0.68rem; padding:0.12rem 0.4rem; min-width:auto;">HR Fit: ${hrLabel}</span></div>` : ''}
                        </td>
                        <td><span style="font-weight:600;">${techP}th</span></td>
                        <td><span style="font-weight:600;">${expP}th</span></td>
                        <td><span style="font-weight:600;">${certP}th</span></td>
                        <td><span class="score-pill">${perc}th Percentile</span></td>
                        <td><span class="tier-tag ${tierClass}" style="white-space: nowrap;">${c.candidate_label}</span></td>
                        <td onclick="event.stopPropagation();">
                            <button onclick="removeCandidateFromWebpage('${c.resume_path || ''}', '${safeName}')" style="background:rgba(239, 68, 68, 0.18); border:1px solid rgba(239, 68, 68, 0.4); color:#fca5a5; border-radius:6px; font-size:0.75rem; padding:0.25rem 0.55rem; cursor:pointer; font-weight:600; display:inline-flex; align-items:center; gap:0.3rem;">
                                🗑️ Remove
                            </button>
                        </td>
                    </tr>
                `;
            });

            html += "</tbody></table>";
            container.innerHTML = html;
        }

        function showToast(message, isError = false) {
            let toast = document.getElementById('toast-notification');
            if (!toast) {
                toast = document.createElement('div');
                toast.id = 'toast-notification';
                toast.style.cssText = 'position:fixed; bottom:24px; right:24px; z-index:9999; padding:12px 20px; border-radius:8px; font-weight:600; font-size:0.85rem; color:#fff; box-shadow:0 10px 25px rgba(0,0,0,0.5); transition:all 0.3s ease; transform:translateY(100px); opacity:0; backdrop-filter:blur(10px);';
                document.body.appendChild(toast);
            }
            toast.style.background = isError ? 'rgba(239, 68, 68, 0.9)' : 'rgba(16, 185, 129, 0.9)';
            toast.style.border = isError ? '1px solid #f87171' : '1px solid #34d399';
            toast.innerText = message;
            toast.style.transform = 'translateY(0)';
            toast.style.opacity = '1';

            setTimeout(() => {
                toast.style.transform = 'translateY(100px)';
                toast.style.opacity = '0';
            }, 3000);
        }

        async function deleteCustomResume(filename) {
            try {
                await fetch(`${API_BASE_URL}/api/resumes/${encodeURIComponent(filename)}`, { method: 'DELETE' });
                showToast(`✓ Removed ${filename}`);
                fetchJobs();
            } catch (err) {
                console.error(err);
                showToast(`⚠ Failed to remove file: ${err.message}`, true);
            }
        }

        async function removeCandidateFromWebpage(resumePath, candidateName) {
            if (!resumePath) {
                showToast("⚠ Resume file path not available", true);
                return;
            }
            const filename = (resumePath || "").split('/').pop().split(String.fromCharCode(92)).pop();
            if (!filename) return;
            
            try {
                closeDetailsModal();
                
                await fetch(`${API_BASE_URL}/api/resumes/${encodeURIComponent(filename)}`, { method: 'DELETE' });
                
                allCandidates = allCandidates.filter(c => {
                    const p = (c.resume_path || "").split('/').pop().split(String.fromCharCode(92)).pop();
                    return p !== filename;
                });
                
                allCandidates.forEach((c, idx) => c.candidate_rank = idx + 1);
                
                const qCounts = { "Q1": 0, "Q2": 0, "Q3": 0, "Q4": 0 };
                allCandidates.forEach(c => {
                    if (c.candidate_label === "Highly Recommended") qCounts["Q1"]++;
                    else if (c.candidate_label === "Recommended") qCounts["Q2"]++;
                    else if (c.candidate_label === "Consider") qCounts["Q3"]++;
                    else if (c.candidate_label === "Not Recommended") qCounts["Q4"]++;
                });
                
                renderResults({
                    candidates: allCandidates,
                    quantiles_count: qCounts,
                    domain_info: {
                        domain_name: domainNameBadge.textContent,
                        domain_summary: domainSummaryText.textContent
                    }
                });
                
                showToast(`✓ Removed ${candidateName || filename} from screening pool`);
                fetchJobs();
            } catch (err) {
                console.error(err);
                showToast(`⚠ Failed to remove candidate: ${err.message}`, true);
            }
        }

        window.showDetails = function(rank) {
            const c = allCandidates.find(x => x.candidate_rank === rank);
            if (!c) return;

            const rJson = c.resume_json || {};
            const rName = rJson.name || "Candidate";
            document.getElementById('modal-name').textContent = rName;
            document.getElementById('modal-contact').textContent = `Email: ${rJson.email || 'N/A'} | Phone: ${rJson.phone || 'N/A'}`;
            document.getElementById('modal-rec').textContent = c.recommendation || "";
            document.getElementById('modal-explanation').textContent = c.explanation || "";

            const modalDeleteBtn = document.getElementById('modal-delete-btn');
            if (modalDeleteBtn) {
                modalDeleteBtn.onclick = () => removeCandidateFromWebpage(c.resume_path, rName);
            }

            const rawS = c.raw_score !== undefined ? c.raw_score : c.final_score;
            const perc = c.percentile_score !== undefined ? c.percentile_score : c.final_score;
            const techP = c.technical_percentile !== undefined ? c.technical_percentile : c.technical_score;
            const expP = c.experience_percentile !== undefined ? c.experience_percentile : c.experience_score;
            const eduP = c.education_percentile !== undefined ? c.education_percentile : c.education_score;
            const certP = c.certification_percentile !== undefined ? c.certification_percentile : c.certification_score;
            const projP = c.project_percentile !== undefined ? c.project_percentile : c.project_score;

            const hrFitScore = c.hr_fit_score !== undefined ? c.hr_fit_score : 100.0;
            const hrFitLabel = c.hr_fit_label || "N/A";

            // Scorecards
            document.getElementById('modal-scores').innerHTML = `
                <div class="score-card" style="border-top: 3px solid #818cf8;"><p>Overall Percentile</p><h3 style="color:#a5b4fc;">${perc}th</h3></div>
                <div class="score-card"><p>Raw Score</p><h3>${rawS}</h3></div>
                <div class="score-card"><p>HR Fit</p><h3>${hrFitScore}%</h3></div>
                <div class="score-card"><p>Technical Skills</p><h3>${techP}th</h3></div>
                <div class="score-card"><p>Experience Fit</p><h3>${expP}th</h3></div>
                <div class="score-card"><p>Education</p><h3>${eduP}th</h3></div>
                <div class="score-card"><p>Certifications</p><h3>${certP}th</h3></div>
                <div class="score-card"><p>Project Fit</p><h3>${projP}th</h3></div>
            `;

            // Custom HR Query Breakdown Table
            const hrResults = c.hr_query_results || [];
            const hrSec = document.getElementById('modal-hr-query-section');
            const hrTab = document.getElementById('modal-hr-queries-table');
            if (hrSec && hrTab) {
                if (hrResults.length > 0) {
                    hrSec.style.display = 'block';
                    let hrTableHtml = `
                        <table style="font-size:0.8rem; border:1px solid var(--glass-border); border-radius:8px; margin-top:0.4rem;">
                            <thead>
                                <tr style="background:rgba(255,255,255,0.04);">
                                    <th style="padding:0.6rem;">HR Question / Requirement</th>
                                    <th style="padding:0.6rem;">Importance</th>
                                    <th style="padding:0.6rem;">Resume Answer</th>
                                    <th style="padding:0.6rem;">Evidence / Reason</th>
                                    <th style="padding:0.6rem;">Fit Result</th>
                                </tr>
                            </thead>
                            <tbody>
                    `;
                    hrResults.forEach(hrq => {
                        let fitBadge = "color:#fca5a5; background:rgba(239,68,68,0.2); border:1px solid rgba(239,68,68,0.4);";
                        if (hrq.fit_result === "Yes") fitBadge = "color:#6ee7b7; background:rgba(16,185,129,0.2); border:1px solid rgba(16,185,129,0.4);";
                        else if (hrq.fit_result === "Partially/Unclear") fitBadge = "color:#fde047; background:rgba(245,158,11,0.2); border:1px solid rgba(245,158,11,0.4);";

                        let impBadge = "color:#cbd5e1;";
                        if (hrq.importance === "Required") impBadge = "color:#fca5a5; font-weight:700;";

                        hrTableHtml += `
                            <tr>
                                <td style="padding:0.6rem; font-weight:600; color:#f8fafc;">${hrq.question}</td>
                                <td style="padding:0.6rem;"><span style="${impBadge}">${hrq.importance}</span></td>
                                <td style="padding:0.6rem; color:#e2e8f0;">${hrq.answer}</td>
                                <td style="padding:0.6rem; font-style:italic; color:#94a3b8;">${hrq.evidence}</td>
                                <td style="padding:0.6rem;"><span style="padding:0.2rem 0.5rem; border-radius:4px; font-weight:700; font-size:0.75rem; ${fitBadge}">${hrq.fit_result}</span></td>
                            </tr>
                        `;
                    });
                    hrTableHtml += `</tbody></table>`;
                    hrTab.innerHTML = hrTableHtml;
                } else {
                    hrSec.style.display = 'none';
                }
            }

            // Strengths
            let strHtml = "";
            (c.strengths || []).forEach(s => strHtml += `<span class="pill pill-strength">✓ ${s}</span>`);
            document.getElementById('modal-strengths').innerHTML = strHtml || '<p style="color:#94a3b8; font-size:0.8rem;">None recorded</p>';

            // Skills
            let skHtml = "";
            (rJson.skills || []).forEach(s => skHtml += `<span class="pill">${s}</span>`);
            document.getElementById('modal-skills').innerHTML = skHtml || '<p style="color:#94a3b8;">None listed</p>';

            // Certs & Licenses
            let certsHtml = "";
            const certList = (rJson.certifications || []).concat(rJson.licenses || []);
            certList.forEach(ct => certsHtml += `<span class="pill" style="background:rgba(16, 185, 129, 0.15); color:#6ee7b7;">📜 ${ct}</span>`);
            document.getElementById('modal-certs').innerHTML = certsHtml || '<p style="color:#94a3b8;">None listed</p>';

            // Education
            let eduHtml = "";
            (rJson.education || []).forEach(e => {
                if (typeof e === 'object') {
                    const deg = e.degree || '';
                    const maj = e.major || '';
                    const showMajor = maj && !deg.toLowerCase().includes(maj.toLowerCase()) ? ` in ${maj}` : '';
                    eduHtml += `<div style="background:rgba(15,23,42,0.4); padding:8px; border-radius:6px; margin-top:4px;">🎓 <strong>${deg}${showMajor}</strong> (${e.institution || ''})</div>`;
                }
            });
            document.getElementById('modal-education').innerHTML = eduHtml;

            // Experience
            let expHtml = "";
            (rJson.experience || []).forEach(e => {
                if (typeof e === 'object') {
                    expHtml += `<div style="margin-top:8px;"><strong>${e.job_title || ''}</strong> at ${e.company || ''} (${e.duration || ''})<p style="font-size:0.8rem; color:#cbd5e1;">${e.description || ''}</p></div>`;
                }
            });
            document.getElementById('modal-experience').innerHTML = expHtml;

            document.getElementById('details-modal').style.display = 'flex';
        }

        function closeDetailsModal() { document.getElementById('details-modal').style.display = 'none'; }
        function openUploadModal() { document.getElementById('upload-modal').style.display = 'flex'; }
        function closeUploadModal() { document.getElementById('upload-modal').style.display = 'none'; }

        async function uploadResumes() {
            const files = document.getElementById('resume-files').files;
            if (!files.length) return alert('Select files first');
            const formData = new FormData();
            for (let i = 0; i < files.length; i++) formData.append('files', files[i]);
            const res = await fetch(`${API_BASE_URL}/api/upload-resumes', { method: 'POST', body: formData });
            const data = await res.json();
            alert(data.message);
            closeUploadModal();
            fetchJobs();
        }

        async function uploadJDFile() {
            const file = document.getElementById('jd-file').files[0];
            if (!file) return alert('Select a text file first');
            const formData = new FormData();
            formData.append('file', file);
            const res = await fetch(`${API_BASE_URL}/api/upload-jd', { method: 'POST', body: formData });
            const data = await res.json();
            alert(data.message);
            closeUploadModal();
            fetchJobs();
        }

        function downloadReport(type) {
            if (!currentSelectedJD) return;
            window.open(`/api/reports/download/${type}/${currentSelectedJD}`, '_blank');
        }

        fetchJobs();
