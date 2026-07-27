import re
p = r"C:\Users\w7\OneDrive\Área de Trabalho\ARON_STUDIO\front\index.html"
c = open(p, encoding="utf-8").read()
antigo = """.sc-grad {
            background: linear-gradient(120deg, #FFFFFF, #FFFFFF 60%, #B4B4B8);
            -webkit-background-clip: unset;
            background-clip: unset;
            -webkit-text-fill-color: transparent;
        }"""
novo = """.sc-grad {
            color: #B4B4B8;
            background: none;
            -webkit-text-fill-color: #B4B4B8;
        }"""
if antigo in c:
    c = c.replace(antigo, novo)
    open(p, "w", encoding="utf-8").write(c)
    print("OK - sc-grad corrigida")
else:
    print("NAO ENCONTRADO - a classe pode ter espacos diferentes")
