/*! ===================================================================
    ARON DESIGN  —  galeria de referências de estilo (sidebar)
    -------------------------------------------------------------------
    Substitui a aba "Componentes". O usuário escolhe um estilo (ou sobe
    o print de um site) e a Aron gera nesse visual.

    Como funciona (100% reaproveitando ganchos existentes do chat.html):
      - Estilo curado  -> seta globalDesignContext (receita de estilo)
                          via window.__aronSetDesignContext(texto)
      - Referência img -> seta currentImageData (Gemini vision)
                          via window.__aronSetReferenceImage(base64)
                          + um design context de "recrie esta referência"

    API: window.AronDesign.render()  (chamado pelo changeMode('design'))
         window.AronDesign.getActive()
         window.AronDesign.clear()
    =================================================================== */
(function () {
  'use strict';
  if (window.AronDesign) return;

  // ----- estilos curados (cada um carrega a "receita" que vai pra IA) -----
  var STYLES = [
    { key: 'saas', cls: 'ad-saas', name: 'SaaS Minimalista', tags: ['Clean', 'Indigo', 'Whitespace'],
      prompt: 'Gere o site no estilo SaaS minimalista: fundo branco, muito espaco em branco, acento indigo (#6366f1), tipografia sans-serif moderna (Inter ou Plus Jakarta Sans), secoes bem espacadas, cards com bordas suaves e sombras leves, hero centralizado com headline grande e CTA destacado. Visual limpo e profissional.' },
    { key: 'dark', cls: 'ad-dark', name: 'Dark / IA Futurista', tags: ['Dark', 'Gradiente', 'Glass'],
      prompt: 'Gere o site no estilo dark futurista de IA: fundo escuro (#0a0a12), gradientes ciano-roxo (#34D7DD ate #8b5cf6), efeito glassmorphism, textos de destaque com gradiente, brilhos sutis, tipografia bold, cards translucidos com borda fina clara. Visual high-tech e premium.' },
    { key: 'food', cls: 'ad-food', name: 'Gastronomia Elegante', tags: ['Warm', 'Serif', 'Aconchego'],
      prompt: 'Gere o site no estilo gastronomia elegante: tons quentes creme e marrom (#fdf6ec e #6f4e37), tipografia serifada refinada (EB Garamond ou Playfair), imagens grandes de comida, layout aconchegante, botoes com cantos retos, sensacao artesanal e premium.' },
    { key: 'shop', cls: 'ad-shop', name: 'E-commerce Moderno', tags: ['Grid', 'CTA', 'Produtos'],
      prompt: 'Gere o site no estilo e-commerce moderno: fundo branco limpo, grid de produtos, CTAs verdes destacados (#10b981), tipografia neutra, cards de produto com imagem, preco e botao, navegacao clara com carrinho, foco total em conversao.' },
    { key: 'folio', cls: 'ad-folio', name: 'Portfolio Criativo', tags: ['Bold', 'Tipografia', 'Arte'],
      prompt: 'Gere o site no estilo portfolio criativo: fundo quase preto (#101014), tipografia oversized e expressiva, acento amarelo (#fbbf24), layout assimetrico, muito contraste, botoes outline, animacoes sutis. Sensacao artistica e autoral.' },
    { key: 'corp', cls: 'ad-corp', name: 'Corporativo Profissional', tags: ['Navy', 'Confiavel', 'Estrutura'],
      prompt: 'Gere o site no estilo corporativo profissional: paleta azul-marinho e cinza (#1e3a8a e #f8fafc), layout estruturado e simetrico, tipografia sobria, secoes organizadas, visual confiavel e institucional, ideal para empresas e prestadores de servico.' }
  ];

  var REF_PROMPT = 'Recrie o design, o layout, as cores, a tipografia e o estilo do site da imagem de referencia anexada o mais fielmente possivel. Adapte o conteudo (textos, secoes) ao que eu pedir, mas mantenha a mesma identidade visual.';

  var activeStyle = null;
  var built = false;

  function $(id) { return document.getElementById(id); }

  function toast(msg) {
    var t = $('ad-toast');
    if (!t) { t = document.createElement('div'); t.id = 'ad-toast'; t.className = 'ad-toast'; document.body.appendChild(t); }
    t.textContent = msg;
    t.classList.add('show');
    clearTimeout(t._tm); t._tm = setTimeout(function () { t.classList.remove('show'); }, 2200);
  }

  // ===================================================================
  //  CSS
  // ===================================================================
  function injectStyles() {
    if ($('ad-style')) return;
    var css = [
      "#aron-design-root{font-family:'Inter',system-ui,sans-serif}",
      "#aron-design-root .ad-sub{color:rgba(241,245,249,.55);font-size:14px;margin-bottom:22px;max-width:680px;line-height:1.55}",
      "#aron-design-root .ad-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:16px}",
      "@media(max-width:900px){#aron-design-root .ad-grid{grid-template-columns:repeat(2,1fr)}}",
      "@media(max-width:560px){#aron-design-root .ad-grid{grid-template-columns:1fr}}",
      "#aron-design-root .ad-card{background:#13131f;border:1px solid rgba(255,255,255,.08);border-radius:16px;overflow:hidden;cursor:pointer;transition:all .2s;position:relative}",
      "#aron-design-root .ad-card:hover{border-color:rgba(99,102,241,.5);transform:translateY(-3px)}",
      "#aron-design-root .ad-card.sel{border-color:#6366f1;box-shadow:0 0 0 2px #6366f1}",
      "#aron-design-root .ad-card.sel .ad-check{opacity:1;transform:scale(1)}",
      "#aron-design-root .ad-check{position:absolute;top:10px;right:10px;width:26px;height:26px;border-radius:50%;background:linear-gradient(135deg,#6366f1,#8b5cf6);display:flex;align-items:center;justify-content:center;opacity:0;transform:scale(.5);transition:all .2s;z-index:3}",
      "#aron-design-root .ad-check svg{width:15px;height:15px}",
      "#aron-design-root .ad-thumb{height:148px;position:relative;overflow:hidden;border-bottom:1px solid rgba(255,255,255,.08)}",
      "#aron-design-root .ad-meta{padding:13px 15px}",
      "#aron-design-root .ad-meta h3{font-size:14px;font-weight:700;color:#f1f5f9;margin-bottom:7px}",
      "#aron-design-root .ad-tags{display:flex;flex-wrap:wrap;gap:5px}",
      "#aron-design-root .ad-tag{font-size:10px;font-weight:600;color:rgba(241,245,249,.55);background:#1a1a28;border:1px solid rgba(255,255,255,.08);padding:3px 8px;border-radius:6px}",
      // mini thumbnail
      "#aron-design-root .ad-t{position:absolute;inset:0;padding:12px;display:flex;flex-direction:column;gap:8px}",
      "#aron-design-root .ad-tnav{display:flex;align-items:center;justify-content:space-between}",
      "#aron-design-root .ad-tlogo{width:34px;height:8px;border-radius:3px}",
      "#aron-design-root .ad-tlinks{display:flex;gap:5px}",
      "#aron-design-root .ad-tlinks span{width:14px;height:5px;border-radius:2px;opacity:.6}",
      "#aron-design-root .ad-thero{flex:1;display:flex;flex-direction:column;justify-content:center;gap:6px}",
      "#aron-design-root .ad-th{height:11px;border-radius:3px;width:80%}",
      "#aron-design-root .ad-th.s{width:55%}",
      "#aron-design-root .ad-tp{height:5px;border-radius:2px;width:65%;opacity:.5}",
      "#aron-design-root .ad-tbtn{height:13px;width:46px;border-radius:5px;margin-top:4px}",
      "#aron-design-root .ad-tcards{display:flex;gap:6px}",
      "#aron-design-root .ad-tcards div{flex:1;height:24px;border-radius:5px}",
      // estilos
      "#aron-design-root .ad-saas{background:#fff}#aron-design-root .ad-saas .ad-tlogo{background:#6366f1}#aron-design-root .ad-saas .ad-tlinks span{background:#475569}#aron-design-root .ad-saas .ad-th{background:#0f172a}#aron-design-root .ad-saas .ad-tp{background:#64748b}#aron-design-root .ad-saas .ad-tbtn{background:#6366f1}#aron-design-root .ad-saas .ad-tcards div{background:#f1f5f9;border:1px solid #e2e8f0}",
      "#aron-design-root .ad-dark{background:linear-gradient(135deg,#0b1020,#111a33)}#aron-design-root .ad-dark .ad-tlogo{background:linear-gradient(90deg,#34D7DD,#8b5cf6)}#aron-design-root .ad-dark .ad-tlinks span{background:#94a3b8}#aron-design-root .ad-dark .ad-th{background:linear-gradient(90deg,#34D7DD,#a78bfa);width:85%}#aron-design-root .ad-dark .ad-tp{background:#64748b}#aron-design-root .ad-dark .ad-tbtn{background:linear-gradient(90deg,#6366f1,#8b5cf6)}#aron-design-root .ad-dark .ad-tcards div{background:rgba(255,255,255,.05);border:1px solid rgba(255,255,255,.12)}",
      "#aron-design-root .ad-food{background:#fdf6ec}#aron-design-root .ad-food .ad-tlogo{background:#6f4e37}#aron-design-root .ad-food .ad-tlinks span{background:#a98467}#aron-design-root .ad-food .ad-th{background:#3a2a1e;width:88%;height:13px}#aron-design-root .ad-food .ad-tp{background:#9c8466}#aron-design-root .ad-food .ad-tbtn{background:#6f4e37;border-radius:2px}#aron-design-root .ad-food .ad-tcards div{background:#f5e8d8}",
      "#aron-design-root .ad-shop{background:#fff}#aron-design-root .ad-shop .ad-tlogo{background:#111827}#aron-design-root .ad-shop .ad-tlinks span{background:#6b7280}#aron-design-root .ad-shop .ad-th{background:#111827;width:60%}#aron-design-root .ad-shop .ad-tp{background:#9ca3af}#aron-design-root .ad-shop .ad-tbtn{background:#10b981}#aron-design-root .ad-shop .ad-tcards div{background:#f9fafb;border:1px solid #e5e7eb;height:30px}",
      "#aron-design-root .ad-folio{background:#101014}#aron-design-root .ad-folio .ad-tlogo{background:#fbbf24}#aron-design-root .ad-folio .ad-tlinks span{background:#e5e7eb}#aron-design-root .ad-folio .ad-th{background:#fafafa;width:92%;height:15px}#aron-design-root .ad-folio .ad-th.s{background:#fbbf24;width:50%;height:15px}#aron-design-root .ad-folio .ad-tbtn{background:transparent;border:1.5px solid #fafafa}#aron-design-root .ad-folio .ad-tcards div{background:#1c1c22}",
      "#aron-design-root .ad-corp{background:#f8fafc}#aron-design-root .ad-corp .ad-tlogo{background:#1e3a8a}#aron-design-root .ad-corp .ad-tlinks span{background:#64748b}#aron-design-root .ad-corp .ad-th{background:#0f213f}#aron-design-root .ad-corp .ad-tp{background:#64748b}#aron-design-root .ad-corp .ad-tbtn{background:#1e3a8a}#aron-design-root .ad-corp .ad-tcards div{background:#fff;border:1px solid #e2e8f0}",
      // card upload
      "#aron-design-root .ad-up{display:flex;flex-direction:column;align-items:center;justify-content:center;text-align:center;padding:26px 18px;border-style:dashed;min-height:225px;gap:10px}",
      "#aron-design-root .ad-up:hover{background:rgba(99,102,241,.05)}",
      "#aron-design-root .ad-up .ad-ic{width:46px;height:46px;border-radius:12px;background:rgba(99,102,241,.12);display:flex;align-items:center;justify-content:center}",
      "#aron-design-root .ad-up .ad-ic svg{width:24px;height:24px;color:#6366f1}",
      "#aron-design-root .ad-up h3{font-size:14px;font-weight:700;color:#f1f5f9}",
      "#aron-design-root .ad-up p{font-size:12px;color:rgba(241,245,249,.55);line-height:1.5}",
      // badge ativo (topo)
      ".ad-badge{position:fixed;top:66px;left:50%;transform:translateX(-50%) translateY(-70px);z-index:2147483500;display:flex;align-items:center;gap:10px;background:#13131f;border:1px solid rgba(99,102,241,.5);border-radius:30px;padding:8px 8px 8px 16px;box-shadow:0 10px 30px rgba(0,0,0,.5);font-family:'Inter',sans-serif;transition:transform .3s cubic-bezier(.16,1,.3,1)}",
      ".ad-badge.show{transform:translateX(-50%) translateY(0)}",
      ".ad-badge span{font-size:13px;font-weight:600;color:#f1f5f9}",
      ".ad-badge button{background:#1a1a28;border:1px solid rgba(255,255,255,.08);color:#f1f5f9;border-radius:20px;width:26px;height:26px;cursor:pointer;font-size:14px}",
      // toast
      ".ad-toast{position:fixed;bottom:90px;left:50%;transform:translateX(-50%) translateY(20px);background:#1a1a28;border:1px solid rgba(52,215,221,.4);color:#f1f5f9;padding:12px 20px;border-radius:12px;font-size:13px;font-weight:600;opacity:0;transition:all .3s;z-index:2147483502;box-shadow:0 10px 30px rgba(0,0,0,.5);font-family:'Inter',sans-serif;text-align:center;max-width:90vw}",
      ".ad-toast.show{opacity:1;transform:translateX(-50%) translateY(0)}"
    ].join('\n');
    var s = document.createElement('style');
    s.id = 'ad-style'; s.textContent = css;
    document.head.appendChild(s);
  }

  function thumbHTML(cls) {
    return '<div class="ad-t ' + cls + '">' +
      '<div class="ad-tnav"><span class="ad-tlogo"></span><span class="ad-tlinks"><span></span><span></span><span></span></span></div>' +
      '<div class="ad-thero"><div class="ad-th"></div><div class="ad-th s"></div><div class="ad-tp"></div><div class="ad-tbtn"></div></div>' +
      '<div class="ad-tcards"><div></div><div></div><div></div></div>' +
      '</div>';
  }

  // ===================================================================
  //  RENDER
  // ===================================================================
  function render() {
    injectStyles();
    var v = $('view-design');
    if (!v) return;
    var root = $('aron-design-root');
    if (!root) { v.innerHTML = '<div id="aron-design-root"></div>'; root = $('aron-design-root'); }
    if (!root || built) return;

    var html = '<p class="ad-sub">Escolha uma referencia de estilo e a Aron vai gerar o seu site nesse visual. Pegue um modelo pronto ou suba o print de um site que voce gostou.</p><div class="ad-grid" id="ad-grid"></div>';
    root.innerHTML = html;
    var grid = $('ad-grid');

    STYLES.forEach(function (s) {
      var card = document.createElement('div');
      card.className = 'ad-card';
      card.innerHTML =
        '<div class="ad-check"><svg viewBox="0 0 24 24" fill="none" stroke="#fff" stroke-width="3"><path d="M20 6 9 17l-5-5"/></svg></div>' +
        '<div class="ad-thumb">' + thumbHTML(s.cls) + '</div>' +
        '<div class="ad-meta"><h3>' + s.name + '</h3><div class="ad-tags">' +
        s.tags.map(function (t) { return '<span class="ad-tag">' + t + '</span>'; }).join('') +
        '</div></div>';
      card.addEventListener('click', function () { chooseStyle(s, card); });
      grid.appendChild(card);
    });

    // card de upload (referencia propria)
    var up = document.createElement('div');
    up.className = 'ad-card ad-up';
    up.innerHTML =
      '<div class="ad-ic"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4M17 8l-5-5-5 5M12 3v12"/></svg></div>' +
      '<h3>Suba sua referencia</h3>' +
      '<p>Print de um site que voce gostou.<br>A Aron recria o estilo.</p>' +
      '<input type="file" id="ad-ref-file" accept="image/*" style="display:none">';
    up.addEventListener('click', function (e) { if (e.target.id !== 'ad-ref-file') $('ad-ref-file').click(); });
    grid.appendChild(up);

    $('ad-ref-file').addEventListener('change', function (e) {
      var f = e.target.files[0];
      if (!f || (f.type || '').indexOf('image/') !== 0) return;
      var r = new FileReader();
      r.onload = function (ev) { chooseReference(ev.target.result); };
      r.readAsDataURL(f);
      e.target.value = '';
    });

    built = true;
  }

  // ===================================================================
  //  SELEÇÃO
  // ===================================================================
  function chooseStyle(s, card) {
    var cards = document.querySelectorAll('#aron-design-root .ad-card');
    for (var i = 0; i < cards.length; i++) cards[i].classList.remove('sel');
    if (card) card.classList.add('sel');
    activeStyle = s;
    if (typeof window.__aronSetDesignContext === 'function') window.__aronSetDesignContext(s.prompt);
    if (typeof window.clearAttachedImage === 'function') window.clearAttachedImage(); // remove ref de imagem antiga
    showDesignBadge('✦ Estilo ativo', () => {
        if (window.__aronSetDesignContext) window.__aronSetDesignContext('');
    });
    toast('Estilo "' + s.name + '" aplicado. Agora descreva seu site!');
    if (typeof window.changeMode === 'function') window.changeMode('assistant');
  }

  function chooseReference(dataUrl) {
    activeStyle = { name: 'Referencia enviada', ref: true };
    if (typeof window.__aronSetReferenceImage === 'function') window.__aronSetReferenceImage(dataUrl);
    if (typeof window.__aronSetDesignContext === 'function') window.__aronSetDesignContext(REF_PROMPT);
    showDesignBadge('Referencia de imagem ativa', () => {
        if (window.__aronSetReferenceImage) window.__aronSetReferenceImage(null);
        const prev = document.getElementById('design-ref-preview');
        if (prev) prev.style.display = 'none';
    });
    toast('Referencia enviada. Descreva o site e a Aron recria esse estilo!');
    if (typeof window.changeMode === 'function') window.changeMode('assistant');
  }

  function clearActive() {
    activeStyle = null;
    if (typeof window.__aronSetDesignContext === 'function') window.__aronSetDesignContext('');
    if (typeof window.clearAttachedImage === 'function') window.clearAttachedImage();
    var cards = document.querySelectorAll('#aron-design-root .ad-card');
    for (var i = 0; i < cards.length; i++) cards[i].classList.remove('sel');
    document.querySelectorAll('[id^="aron-design-badge-"]').forEach(el => el.remove());
    toast('Design removido.');
  }

  // ===================================================================
  //  BADGE
  // ===================================================================
    function showDesignBadge(label, onClear) {
        const existingId = 'aron-design-badge-' + label.replace(/\s/g,'');
        document.getElementById(existingId)?.remove();

        const badge = document.createElement('div');
        badge.id = existingId;
        badge.style.cssText = [
            'position:fixed',
            'top:85px',
            'left:50%',
            'transform:translateX(-50%)',
            'z-index:9999',
            'background:rgba(30,30,50,0.95)',
            'color:#fff',
            'border:1px solid rgba(99,102,241,0.5)',
            'border-radius:999px',
            'padding:6px 16px 6px 14px',
            'font-size:13px',
            'font-weight:600',
            'display:flex',
            'align-items:center',
            'gap:10px',
            'box-shadow:0 4px 20px rgba(0,0,0,0.4)',
            'pointer-events:all',
            'cursor:default'
        ].join(';');

        const icon = document.createElement('span');
        icon.innerHTML = '<svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14.5 4h-5L7 7H4a2 2 0 0 0-2 2v9a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2V9a2 2 0 0 0-2-2h-3l-2.5-3z"/><circle cx="12" cy="13" r="3"/></svg>';
        icon.style.cssText = 'display:flex;align-items:center;opacity:0.9;';

        const span = document.createElement('span');
        span.textContent = label;

        const btn = document.createElement('button');
        btn.textContent = '×';
        btn.style.cssText = [
            'background:rgba(255,255,255,0.15)',
            'border:none',
            'color:#fff',
            'border-radius:50%',
            'width:20px',
            'height:20px',
            'cursor:pointer',
            'font-size:14px',
            'line-height:1',
            'display:flex',
            'align-items:center',
            'justify-content:center',
            'flex-shrink:0'
        ].join(';');

        btn.addEventListener('click', (e) => {
            e.stopPropagation();
            badge.remove();
            if (typeof onClear === 'function') onClear();
        });

        badge.appendChild(icon);
        badge.appendChild(span);
        badge.appendChild(btn);
        document.body.appendChild(badge);
        return badge;
    }

  window.AronDesign = { render: render, getActive: function () { return activeStyle; }, clear: clearActive };
})();