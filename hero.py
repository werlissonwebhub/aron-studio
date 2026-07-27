import os
p = r"C:\Users\w7\OneDrive\Área de Trabalho\ARON_STUDIO\front\index.html"
c = open(p, encoding="utf-8").read()
S, E = "<!-- HERO-V2-START -->", "<!-- HERO-V2-END -->"

css = """
<link href="https://fonts.googleapis.com/css2?family=Fraunces:ital,opsz,wght@0,9..144,400;0,9..144,600;0,9..144,900;1,9..144,400&display=swap" rel="stylesheet">
<style>
/* ===== HERO V2 - editorial claro ===== */
body { background:#FFFFFF !important; }
section:first-of-type, header + section, .hero, #start {
  background:
    radial-gradient(circle at 1px 1px, rgba(10,10,10,.07) 1px, transparent 0) 0 0 / 22px 22px,
    #FFFFFF !important;
}
h1[class*="tracking-[0.6em]"] {
  color:#8A8A8E !important; font-family:'Inter',sans-serif !important;
  font-size:11px !important; font-weight:600 !important; letter-spacing:.42em !important;
}
p[class*="text-[#8A3FFC]"] {
  font-family:'Fraunces',serif !important; color:#0A0A0A !important;
  -webkit-text-fill-color:#0A0A0A !important; background:none !important;
  font-weight:900 !important; font-size:clamp(2.8rem,6.5vw,5.5rem) !important;
  line-height:.98 !important; letter-spacing:-.02em !important;
}
p[class*="text-[#8A3FFC]"] span {
  font-family:'Fraunces',serif !important; font-style:italic !important; font-weight:400 !important;
  color:#57575B !important; -webkit-text-fill-color:#57575B !important; background:none !important;
}
p[class*="text-[#8A3FFC]"] + p {
  font-family:'Inter',sans-serif !important; color:#8A8A8E !important; font-size:12px !important;
  font-weight:600 !important; letter-spacing:.24em !important; text-transform:uppercase !important; margin-top:1.5rem !important;
}
[class*="bg-[#B349F5]/25"], [class*="bg-[#34D7DD]/20"] { opacity:.10 !important; filter:blur(90px) !important; }

/* ===== INPUT VIRTUAL - branco, borda preta, texto/icones pretos ===== */
.virtual-input-border {
  background:#FFFFFF !important;
  border:1.5px solid #0A0A0A !important;
  border-radius:18px !important;
  box-shadow:0 8px 30px rgba(0,0,0,.08) !important;
  backdrop-filter:none !important;
  -webkit-backdrop-filter:none !important;
}
.virtual-input-border .text-zinc-200, #virtual-typing-text { color:#0A0A0A !important; }
.virtual-input-border .border-white\\/5 { border-color:rgba(0,0,0,.08) !important; }
.virtual-input-border button { color:#0A0A0A !important; }
.virtual-input-border button i { color:#0A0A0A !important; }
.virtual-input-border button:hover { color:#0A0A0A !important; background:rgba(0,0,0,.05) !important; }
.cursor-blink { color:#0A0A0A !important; }
</style>
"""

block = S + css + E + "\n"
if S in c and E in c:
    c = c[:c.find(S)] + block + c[c.find(E)+len(E):]
else:
    c = c.replace("</head>", block + "</head>", 1)
open(p, "w", encoding="utf-8").write(c)
print("HERO V2 + input aplicado")
