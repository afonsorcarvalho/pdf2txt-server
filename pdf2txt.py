import pdfplumber 
import sys

if len(sys.argv) != 2:
	print("Uso: python script.py arquivo.pdf")
	sys.exit(1)
texto = ""
caminho_pdf = sys.argv[1]

with pdfplumber.open(caminho_pdf) as pdf:
	for pagina in pdf.pages:
		pagina_texto = pagina.extract_text()
		if pagina_texto:
			texto += pagina_texto + "\n"

	
# Nome do arquivo de saída baseado no nome do PDF
saida_txt = caminho_pdf.rsplit(".", 1)[0] + ".txt"

with open(saida_txt, "w", encoding="utf-8") as f: 
	f.write(texto)
