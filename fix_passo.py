p = r"C:\Users\w7\OneDrive\Área de Trabalho\ARON_STUDIO\front\index.html"
c = open(p, encoding="utf-8").read()
n = 0
# cor do texto "Passo 01"
if "color: #818cf8;" in c:
    c = c.replace("color: #818cf8;", "color: #B4B4B8;"); n += 1
# cor da linha (rgba do mesmo azul) -> grafite translucido
import re
c2 = re.sub(r"rgba\(129,\s*140,\s*248[^)]*\)", "rgba(180,180,184,0.5)", c)
if c2 != c:
    c = c2; n += 1
open(p, "w", encoding="utf-8").write(c)
print(f"OK - {n} substituicoes feitas")
