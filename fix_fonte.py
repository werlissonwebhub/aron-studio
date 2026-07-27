p = r"C:\Users\w7\OneDrive\Área de Trabalho\ARON_STUDIO\front\index.html"
c = open(p, encoding="utf-8").read()
antes = c.count("'EB Garamond', serif")
c = c.replace("'EB Garamond', serif", "'Inter', sans-serif")
open(p, "w", encoding="utf-8").write(c)
print(f"OK - {antes} ocorrencias de EB Garamond trocadas por Inter")
