p = r"C:\Users\w7\OneDrive\Área de Trabalho\ARON_STUDIO\front\index.html"
c = open(p, encoding="utf-8").read()
antes = c.count("818cf8")
# troca o hex em qualquer formato (#818cf8, 818cf8)
c = c.replace("#818cf8", "#B4B4B8").replace("818cf8", "B4B4B8")
# troca o mesmo azul em rgb/rgba (129,140,248)
import re
c = re.sub(r"129,\s*140,\s*248", "180,180,184", c)
depois = c.count("818cf8")
open(p, "w", encoding="utf-8").write(c)
print(f"Trocadas: {antes} ocorrencias de 818cf8, restam {depois}")
