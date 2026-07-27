
            let currentProjectId = null;
            let _cloudSaveDebounce = null;

            window.openProjectsModal = async () => {
                // Fechar sidebar no mobile
                if (window.innerWidth < 768) {
                    const sidebar = document.getElementById('app-sidebar');
                    if (sidebar?.classList.contains('translate-x-0')) toggleMobileSidebar();
                }

                const overlay = document.getElementById('projects-overlay');
                overlay.classList.remove('hidden');
                overlay.classList.add('flex');
                await listProjects();
                if (window.lucide?.createIcons) lucide.createIcons();
            };

            window.closeProjectsModal = () => {
                const overlay = document.getElementById('projects-overlay');
                overlay.classList.add('hidden');
                overlay.classList.remove('flex');
            };

            function showAutoSaveIndicator(text) {
                const el = document.getElementById('autosave-indicator');
                const txt = document.getElementById('autosave-text');
                if (!el) return;
                if (txt) txt.textContent = text || 'Salvando...';
                el.style.opacity = '1';
                setTimeout(() => { el.style.opacity = '0'; }, 2500);
            }

            window.listProjects = async () => {
                const container = document.getElementById('projects-list-container');
                try {
                    const userId = localStorage.getItem('aron_user_id');
                    const res = await apiFetch(`${API_URL}/api/projects?user_id=${userId}`);
                    const projects = await res.json();

                    if (!projects.length) {
                        container.innerHTML = `
                        <div class="flex flex-col items-center justify-center py-12 text-surface-500">
                            <i data-lucide="inbox" class="h-12 w-12 mb-4 opacity-20"></i>
                            <p class="text-sm">Nenhum projeto salvo ainda</p>
                        </div>`;
                        if (window.lucide?.createIcons) lucide.createIcons();
                        return;
                    }

                    container.innerHTML = projects.map(p => `
                    <div class="group flex items-center justify-between p-4 bg-white/5 border border-white/5 rounded-xl hover:bw-white/10 hover:border-[#34D7DD]/30 transition-all">
                        <div class="flex items-center space-x-4 cursor-pointer flex-1" onclick="loadProjectFromCloud('${p.id}')">
                            ${p.thumbnail ? '<img src="' + p.thumbnail + '" class="h-10 w-10 rounded-lg object-cover group-hover:scale-110 transition-transform flex-shrink-0" />' : '<div class="h-10 w-10 rounded-lg bg-surface-900 border border-surface-800 flex items-center justify-center group-hover:sole-110 transition-transform flex-shrink-0"><i data-lucide="layout" class="h-5 w-5 text-[#34D7DD]"></i></div>' }
                            <div>
                                <h4 class="text-sm font-bold text-white">${p.name || p.title || 'Projeto sem nome'}</h4>
                                <p class="text-[10px] text-surface-500">${window.amFmtDate(p.created_at, true)}</p>
                            </div>
                        </div>
                        <button onclick="deleteProjectFromCloud('${p.id}')" class="p-2 text-surface-500 hover:text-red-400 transition-colors">
                            <i data-lucide="trash-2" class="h-4 w-4"></i>
                        </button>
                    </div>
                `).join('');
                    if (window.lucide?.createIcons) lucide.createIcons();
                } catch (e) {
                    console.error("Erro ao listar projetos:", e);
                }
            };

            window.saveProjectToCloud = async (isAuto = true) => {
            if (typeof updateSaveStatus === 'function') updateSaveStatus('saving');
                try {
                    const userId = localStorage.getItem('aron_user_id');
                    if (!userId || !fullHtml) return;

                    if (isAuto) showAutoSaveIndicator('Salvando...');

                    if (!currentProjectId && currentChatId) {
                        currentProjectId = currentChatId;
                    }

                    const projectName = (document.getElementById('topbar-project-name')?.textContent || '').replace(/\s+/g, ' ').trim().replace(/[✏️]+/g,'').trim() || 'Projeto Sem Nome';

                    const payload = {
                        id: currentProjectId,
                        user_id: userId,
                        name: projectName,
                        html_code: fullHtml,
                        full_json: window.currentProjectData ? JSON.stringify(window.currentProjectData) : null,
                        thumbnail: (typeof generateThumbnail === "function" ? generateThumbnail(fullHtml) : null)
                    };

                    const res = await apiFetch(`${API_URL}/api/save-project`, {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify(payload)
                    });
                    const data = await res.json();
                    if (data.id) {
                        currentProjectId = data.id;
                        currentChatId = data.id;
                        window.currentChatId = data.id;
                    }

                    if (isAuto) showAutoSaveIndicator('Salvo ✓');
                    if (typeof updateSaveStatus === 'function') updateSaveStatus('saved');
                        if (!isAuto) showToast("Projeto salvo com sucesso!", "success");
                } catch (e) {
                    console.error("Erro ao salvar projeto:", e);
                    if (isAuto) showAutoSaveIndicator('Erro ao salvar');
                }
            };

            // Debounced auto-save (3 seconds)
            window.debouncedCloudSave = () => {
                clearTimeout(_cloudSaveDebounce);
                _cloudSaveDebounce = setTimeout(() => {
                    if (window.saveProjectToCloud) window.saveProjectToCloud(true);
                }, 3000);
            };

            window.loadProjectFromCloud = async (id) => {
                try {
                    const userId = localStorage.getItem('aron_user_id');
                    const res = await apiFetch(`${API_URL}/api/projects/${id}?user_id=${userId}`);
                    if (!res.ok) throw new Error("Acesso negado");
                    const p = await res.json();

                    currentProjectId = p.id;
                    currentChatId = p.id;
                    window.currentChatId = p.id;

                    const projectName = p.name || p.title || 'Projeto Sem Nome';
                    updateTopbarProjectName(projectName);

                    if (document.getElementById('project-name-input')) {
                        document.getElementById('project-name-input').value = p.name || p.title || 'Projeto Sem Nome';
                    }

                    if (p.full_json) {
                        try {
                            const projectData = JSON.parse(p.full_json);
                            if (window.renderMultiFileApp) {
                                if (projectData.project_structure) {
                                    window.renderMultiFileApp(projectData.project_structure);
                                } else {
                                    window.renderMultiFileApp(projectData);
                                }
                            }
                        } catch (parseErr) {
                            console.warn('>>> [PARSE PROTECT] full_json inválido em loadProjectFromCloud:', parseErr.message);
                            fullHtml = p.full_json;
                            renderInIframe(fullHtml);
                            if (window.monacoEditor) {
                                try { window.monacoEditor.setValue(fullHtml); } catch(e) {}
                            }
                        }
                    } else {
                        fullHtml = p.html_code || p.full_code || '';
                        renderInIframe(fullHtml);
                        if (window.monacoEditor) {
                            try { window.monacoEditor.setValue(fullHtml); } catch(e) {}
                        }
                    }

                    // Renderizar balões no chat
                    const chatMessages = document.getElementById('chat-messages');
                    if (chatMessages) {
                        chatMessages.innerHTML = '';
                        chatMessages.classList.remove('hidden');
                        chatMessages.style.display = 'block';

                        // 1. Bolha do usuário (com o título/nome do projeto)
                        const userRow = document.createElement('div');
                        userRow.className = 'aron-msg-row';
                        userRow.style.justifyContent = 'flex-end';
                        userRow.innerHTML = `
                            <div class="aron-bubble user-bubble">
                                ${projectName}
                            </div>
                        `;
                        chatMessages.appendChild(userRow);

                        // 2. Bolha da IA informando que o projeto foi carregado
                        const aiRow = document.createElement('div');
                        aiRow.className = 'aron-msg-row';
                        aiRow.innerHTML = `
                            <div class="aron-avatar" style="background:transparent;padding:2px;">
                                <img src="img/bolha-aron.png" alt="Aron" style="width:28px;height:28px;object-fit:contain;border-radius:50%;">
                            </div>
                            <div class="aron-bubble font-sans" style="background:#13131f; border:1px solid rgba(99,102,241,0.2); border-radius:4px 14px 14px 14px; padding:12px 14px; font-size:13px; color:rgba(241,245,249,0.85); line-height:1.6; max-width:85%;">
                                <div style="color:#10b981; font-weight:bold; font-size:12px; margin-bottom:4px; display:flex; align-items:center; gap:4px;">
                                    <span>✓</span> Projeto carregado com sucesso!
                                </div>
                                Você pode continuar editando este projeto enviando novos comandos no chat abaixo.
                            </div>
                        `;
                        chatMessages.appendChild(aiRow);
                        chatMessages.scrollTop = chatMessages.scrollHeight;
                    }

                    if (window.updateTopbarProjectName) updateTopbarProjectName(p.name || p.title || 'Projeto Sem Nome');
                    const _loadPc = document.getElementById('preview-container');
                    if (_loadPc) { _loadPc.classList.remove('hidden'); _loadPc.classList.add('active'); }
                    closeProjectsModal();
                    changeMode('assistant');
                    welcomeScreen.classList.remove('active');
                    if (auroraBg) auroraBg.classList.add('dimmed');
                } catch (e) {
                    console.error('>>> [loadProjectFromCloud] erro real:', e);
                    showToast('Erro ao carregar projeto: ' + e.message, 'error');
                }
            };

            window.deleteProjectFromCloud = async (id) => {
                if (!confirm("Deletar projeto permanentemente?")) return;
                try {
                    const userId = localStorage.getItem('aron_user_id');
                    await apiFetch(`${API_URL}/api/projects/${id}?user_id=${userId}`, { method: 'DELETE' });
                    await listProjects();
                } catch (e) {
                    showToast("Erro ao deletar.", "error");
                }
            };

            // ========== TOPBAR DROPDOWN ==========
            let _dropdownOpen = false;

            window.toggleProjectsDropdown = async () => {
                const dd = document.getElementById('topbar-projects-dropdown');
                const chevron = document.getElementById('topbar-chevron');
                if (!dd) return;
                _dropdownOpen = !_dropdownOpen;
                if (_dropdownOpen) {
                    dd.classList.remove('hidden');
                    if (chevron) chevron.style.transform = 'rotate(180deg)';
                    await loadDropdownProjects();
                } else {
                    dd.classList.add('hidden');
                    if (chevron) chevron.style.transform = 'rotate(0deg)';
                }
            };

            window.closeProjectsDropdown = () => {
                const dd = document.getElementById('topbar-projects-dropdown');
                const chevron = document.getElementById('topbar-chevron');
                if (dd) dd.classList.add('hidden');
                if (chevron) chevron.style.transform = 'rotate(0deg)';
                _dropdownOpen = false;
            };

            // Close on outside click
            document.addEventListener('click', (e) => {
                if (!_dropdownOpen) return;
                const dd = document.getElementById('topbar-projects-dropdown');
                const trigger = e.target.closest('[onclick*="toggleProjectsDropdown"]');
                if (!trigger && dd && !dd.contains(e.target)) {
                    closeProjectsDropdown();
                }
            });

            async function loadDropdownProjects() {
                const container = document.getElementById('topbar-projects-list');
                if (!container) return;
                try {
                    const userId = localStorage.getItem('aron_user_id');
                    const res = await apiFetch(`${API_URL}/api/projects?user_id=${userId}`);
                    const projects = await res.json();

                    if (!projects.length) {
                        container.innerHTML = `<div class="px-4 py-8 text-center text-surface-600 text-xs flex flex-col items-center">
                        <i data-lucide="inbox" class="h-8 w-8 mb-2 opacity-20"></i>Nenhum projeto salvo</div>`;
                        if (window.lucide?.createIcons) lucide.createIcons();
                        return;
                    }

                    const recent = projects.slice(0, 8);
                    container.innerHTML = recent.map(p => {
                        const isActive = currentProjectId === p.id;
                        return `<button onclick="selectProjectFromDropdown('${p.id}')" class="w-full flex items-center space-x-3 px-4 py-2.5 text-left hover:bg-white/5 transition-colors ${isActive ? 'bg-white/[0.04]' : ''}">
                        <div class="h-7 w-7 rounded-lg ${isActive ? 'bg-[#B349F5]/15 border-[#B349F5]/30' : 'bg-white/5 border-white/[0.06]'} border flex items-center justify-center flex-shrink-0">
                            <i data-lucide="${isActive ? 'folder-open' : 'file-code'}" class="h-3.5 w-3.5 ${isActive ? 'text-[#B349F5]' : 'text-surface-500'}"></i>
                        </div>
                        <div class="flex-1 min-w-0">
                            <p class="text-[12px] font-medium ${isActive ? 'text-white' : 'text-surface-300'} truncate">${p.name || p.title || 'Projeto sem nome'}</p>
                            <p class="text-[10px] text-surface-600">${window.amFmtDate(p.created_at)}</p>
                        </div>
                        ${isActive ? '<div class="h-1.5 w-1.5 rounded-full bg-[#B349F5] flex-shrink-0"></div>' : ''}
                    </button>`;
                    }).join('');
                    if (window.lucide?.createIcons) lucide.createIcons();
                } catch (e) {
                    container.innerHTML = `<div class="px-4 py-6 text-center text-red-400 text-xs">Erro ao carregar</div>`;
                }
            }

            window.selectProjectFromDropdown = async (id) => {
                closeProjectsDropdown();
                await loadProjectFromCloud(id);
            };

            window.newProjectFromDropdown = () => {
                closeProjectsDropdown();
                currentProjectId = null;
                currentChatId = null;
                fullHtml = '';
                if (window.currentProjectData) window.currentProjectData = null;
                if (window.monacoEditor) { try { window.monacoEditor.setValue(''); } catch (e) {} }
                updateTopbarProjectName('Projeto Sem Nome');
                const ws = document.getElementById('welcome-studio');
                if (ws) ws.classList.add('active');
                const pc = document.getElementById('preview-container');
                if (pc) { pc.classList.remove('active'); pc.style.display = 'none'; }
                const pi = document.getElementById('preview-iframe');
                if (pi) { pi.src = 'about:blank'; }
                const cm = document.getElementById('chat-messages');
                if (cm) { cm.classList.add('hidden'); cm.innerHTML = ''; }
                const ab = document.getElementById('aurora-container');
                if (ab) ab.classList.remove('dimmed');
            };

            window.updateTopbarProjectName = (name) => {
                const el = document.getElementById('topbar-project-name');
                const cleaned = (name || 'Projeto Sem Nome').replace(/\s+/g, ' ').trim();
                if (el) el.textContent = cleaned;
            };

            // Setup rename event on topbar project name click
            document.addEventListener('DOMContentLoaded', () => {
                const el = document.getElementById('topbar-project-name');
                if (el) {
                    el.style.cursor = 'pointer';
                    el.title = 'Clique para renomear o projeto';
                    el.addEventListener('click', async (e) => {
                        e.stopPropagation();
                        e.preventDefault();
                        const currentName = el.textContent || '';
                        const newName = await abrirModalRenomear(currentName);
                        if (newName && newName.trim() !== '' && newName.trim() !== currentName) {
                            const trimmedName = newName.trim();
                            updateTopbarProjectName(trimmedName);
                            const userId = localStorage.getItem('aron_user_id');
                            const projectId = currentProjectId || currentChatId;
                            if (projectId && userId) {
                                try {
                                    await apiFetch(`${API_URL}/api/rename-project`, {
                                        method: 'POST',
                                        headers: { 'Content-Type': 'application/json' },
                                        body: JSON.stringify({ chat_id: projectId, user_id: userId, name: trimmedName })
                                    });
                                    if (window.loadChats) window.loadChats();
                                    if (window.listProjects) window.listProjects();
                                } catch (err) {
                                    console.error("Erro ao renomear:", err);
                                }
                            }
                        }
                    });
                }
            });

            // Hook into saveProjectToCloud to show status
            const _origSave = window.saveProjectToCloud;
            window.saveProjectToCloud = async (isAuto = true) => {
                const statusEl = document.getElementById('topbar-save-status');
                if (statusEl && isAuto) {
                    statusEl.textContent = '• Salvando...';
                    statusEl.classList.remove('hidden');
                }
                await _origSave(isAuto);
                if (statusEl && isAuto) {
                    statusEl.textContent = '• Salvo ✓';
                    setTimeout(() => { statusEl.classList.add('hidden'); }, 2500);
                }
            };

            // Also update topbar when loading a project
            const _origLoad = window.loadProjectFromCloud;
            window.loadProjectFromCloud = async (id) => {
                await _origLoad(id);
            };
        