
// Alternar Preview / Código no Editor Visual
window.toggleEditorView = function(view) {
    const prev = document.getElementById('editor-preview-pane');
    const code = document.getElementById('editor-code-pane');
    const tP   = document.getElementById('editor-tab-preview');
    const tC   = document.getElementById('editor-tab-code');
    const apply= document.getElementById('editor-apply-btn');
    if (!prev || !code) return;
    if (view === 'code') {
        prev.style.display = 'none';
        code.style.display = 'flex';
        if (apply) apply.style.display = 'block';
        tC.style.background = 'linear-gradient(135deg,#6366f1,#8b5cf6)'; tC.style.color = 'white';
        tP.style.background = 'transparent'; tP.style.color = 'rgba(241,245,249,0.6)';
        if (window.monacoEditor && window.fullHtml) window.monacoEditor.setValue(window.fullHtml);
        if (window.monacoEditor) setTimeout(() => window.monacoEditor.layout(), 50);
    } else {
        prev.style.display = 'block';
        code.style.display = 'none';
        if (apply) apply.style.display = 'none';
        tP.style.background = 'linear-gradient(135deg,#6366f1,#8b5cf6)'; tP.style.color = 'white';
        tC.style.background = 'transparent'; tC.style.color = 'rgba(241,245,249,0.6)';
        const ifr = document.getElementById('editor-preview-iframe');
        if (ifr && window.fullHtml) ifr.srcdoc = window.fullHtml;
    }
};

// Enviar pedido de ajuste para a IA
window.sendEditorChatMessage = async function() {
    const input = document.getElementById('editor-chat-input');
    const box   = document.getElementById('editor-chat-messages');
    const btn   = document.getElementById('editor-chat-send');
    if (!input || !box) return;
    const msg = input.value.trim();
    if (!msg) return;

    const currentHtml = window.fullHtml || '';
    if (!currentHtml || currentHtml.length < 50) { showToast('Gere um site primeiro!', 'error'); return; }

    const u = document.createElement('div');
    u.style.cssText = 'background:linear-gradient(135deg,#6366f1,#8b5cf6);border-radius:14px 4px 14px 14px;padding:12px 14px;font-size:13px;color:white;line-height:1.6;align-self:flex-end;max-width:90%;';
    u.textContent = msg;
    box.appendChild(u);
    input.value = ''; input.style.height = 'auto';
    box.scrollTop = box.scrollHeight;

    const ai = document.createElement('div');
    ai.style.cssText = 'background:#13131f;border:1px solid rgba(99,102,241,0.2);border-radius:4px 14px 14px 14px;padding:12px 14px;font-size:13px;color:rgba(241,245,249,0.85);line-height:1.6;display:flex;align-items:center;gap:8px;';
    ai.innerHTML = '<div style="width:12px;height:12px;border-radius:50%;border:2px solid rgba(99,102,241,0.3);border-top:2px solid #6366f1;animation:dotSpin 0.85s linear infinite;"></div> Aplicando ajuste...';
    box.appendChild(ai);
    box.scrollTop = box.scrollHeight;
    if (btn) btn.disabled = true;

    const modPrompt = 'Você está editando um site existente. Aqui está o HTML atual:\n\n```html\n' + currentHtml + '\n```\n\nINSTRUÇÃO: ' + msg + '\n\nAplique APENAS a modificação pedida, mantendo todo o resto intacto. Retorne o HTML completo e atualizado.';

    try {
        const userId = localStorage.getItem('aron_user_id');
        let chatId = window.currentChatId;
        const base = window.API_URL || 'http://127.0.0.1:8000';

        if (!chatId) {
            try {
                const ir = await apiFetch(base + '/chat/init', {
                    method:'POST', headers:{'Content-Type':'application/json'},
                    body: JSON.stringify({ first_prompt: msg, mode:'assistant', user_id:userId })
                });
                const id = await ir.json();
                chatId = id.chat_id; window.currentChatId = chatId;
            } catch(e) {}
        }

        let token = null;
        try { if (typeof auth !== 'undefined' && auth.currentUser) token = await auth.currentUser.getIdToken(); } catch(e) {}
        const headers = { 'Content-Type':'application/json' };
        if (token) headers['Authorization'] = 'Bearer ' + token;

        const resp = await fetch(base + '/generate/stream', {
            method:'POST', headers: headers,
            body: JSON.stringify({ chat_id: chatId, prompt: modPrompt, mode:'assistant', model_alias: window.currentModel || 'gemini', user_id: userId })
        });
        if (!resp.ok) throw new Error('HTTP ' + resp.status);

        const reader = resp.body.getReader();
        const dec = new TextDecoder();
        let buf = '', htmlB64 = null;
        while (true) {
            const { done, value } = await reader.read();
            if (done) break;
            buf += dec.decode(value, { stream:true });
            const lines = buf.split('\n'); buf = lines.pop();
            for (const ln of lines) {
                if (!ln.startsWith('data: ')) continue;
                let evt; try { evt = JSON.parse(ln.slice(6)); } catch { continue; }
                if (evt.type === 'done') htmlB64 = evt.html_base64;
                if (evt.type === 'error') throw new Error(evt.message || 'Erro IA');
            }
        }

        if (!htmlB64) throw new Error('IA não retornou HTML');
        const bin = atob(htmlB64);
        const bytes = new Uint8Array(bin.length);
        for (let i=0;i<bin.length;i++) bytes[i] = bin.charCodeAt(i);
        const newHtml = new TextDecoder('utf-8').decode(bytes);

        window.fullHtml = newHtml;
        const ifr = document.getElementById('editor-preview-iframe');
        if (ifr) ifr.srcdoc = newHtml;
        if (window.monacoEditor) window.monacoEditor.setValue(newHtml);
        if (typeof renderInIframe === 'function') renderInIframe(newHtml);
        if (typeof window.updateCodePanel === 'function') window.updateCodePanel(newHtml);
        if (window.debouncedCloudSave) window.debouncedCloudSave();

        ai.innerHTML = '✓ Ajuste aplicado com sucesso!';
        ai.style.color = '#10b981';
    } catch(err) {
        ai.innerHTML = '❌ Erro: ' + err.message;
        ai.style.color = '#f87171';
    } finally {
        if (btn) btn.disabled = false;
        box.scrollTop = box.scrollHeight;
    }
};
