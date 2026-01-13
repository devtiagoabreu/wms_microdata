from flask import Flask, render_template, request, send_file, jsonify
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4, mm
from reportlab.lib.units import mm
from reportlab.graphics.barcode import code128
from reportlab.graphics.shapes import Drawing
from reportlab.graphics import renderPDF
import re
import io

app = Flask(__name__)

# Tamanho personalizado da página
PAGE_WIDTH = 99.8 * mm
PAGE_HEIGHT = 80.0 * mm

# Tamanho da etiqueta
ETIQUETA_WIDTH = 90 * mm
ETIQUETA_HEIGHT = 35 * mm

def calcular_etiquetas(inicio, fim):
    """Calcula a quantidade de etiquetas entre dois códigos"""
    padrao = r'(\d{2})\.(\d{2})\.(\d{2})\.(\d{2})'
    m1 = re.match(padrao, inicio)
    m2 = re.match(padrao, fim)
    
    if not m1 or not m2:
        return 0
    
    b1, s1, p1, a1 = map(int, m1.groups())
    b2, s2, p2, a2 = map(int, m2.groups())
    
    # Verifica se os primeiros 3 grupos são iguais
    if b1 != b2 or s1 != s2 or a1 != a2:
        return 0
    
    # Apenas o terceiro grupo (p) varia
    return (p2 - p1) + 1 if p2 >= p1 else 0

def gerar_pdf_buffer(inicio, fim, endereco_completo):
    """Gera PDF na memória com layout específico"""
    quantidade = calcular_etiquetas(inicio, fim)
    if quantidade <= 0:
        return None
    
    # Extrai partes do código inicial
    padrao = r'(\d{2})\.(\d{2})\.(\d{2})\.(\d{2})'
    match = re.match(padrao, inicio)
    if not match:
        return None
    
    b, s, p, a = map(int, match.groups())
    
    # Criar buffer na memória
    buffer = io.BytesIO()
    
    # Criar canvas com tamanho personalizado
    c = canvas.Canvas(buffer, pagesize=(PAGE_WIDTH, PAGE_HEIGHT))
    
    # Calcular número de páginas (2 etiquetas por página)
    etiquetas_por_pagina = 2
    total_paginas = (quantidade + 1) // etiquetas_por_pagina  # Arredonda para cima
    
    etiqueta_atual = 0
    pagina = 0
    
    # Margens para centralizar
    margem_x = (PAGE_WIDTH - ETIQUETA_WIDTH) / 2
    margem_y_superior = (PAGE_HEIGHT - (2 * ETIQUETA_HEIGHT)) / 2 + ETIQUETA_HEIGHT
    margem_y_inferior = (PAGE_HEIGHT - (2 * ETIQUETA_HEIGHT)) / 2
    
    while etiqueta_atual < quantidade:
        # Nova página se necessário
        if etiqueta_atual > 0 and etiqueta_atual % etiquetas_por_pagina == 0:
            c.showPage()
        
        # Determinar posição Y (superior ou inferior)
        posicao_na_pagina = etiqueta_atual % etiquetas_por_pagina
        if posicao_na_pagina == 0:
            y_pos = margem_y_superior
        else:
            y_pos = margem_y_inferior
        
        x_pos = margem_x
        
        # Código atual
        codigo = f"{b:02d}.{s:02d}.{p:02d}.{a:02d}"
        
        # Desenhar fundo da etiqueta (opcional)
        c.setStrokeColorRGB(0.9, 0.9, 0.9)
        c.setLineWidth(0.25)
        c.rect(x_pos, y_pos - ETIQUETA_HEIGHT, ETIQUETA_WIDTH, ETIQUETA_HEIGHT, stroke=1, fill=0)
        
        # GERAR CÓDIGO DE BARRAS - AUMENTADO
        try:
            # Criar código de barras Code128
            barcode = code128.Code128(
                codigo,
                barWidth=0.5,  # Aumentado de 0.25 para 0.5
                barHeight=15,   # Altura do código de barras
                humanReadable=False
            )
            
            # Desenhar código de barras
            barcode.drawOn(c, x_pos + 5, y_pos - 15)
            
        except:
            # Fallback se não conseguir gerar código de barras
            pass
        
        # Texto do código - MAIOR E EM NEGRITO
        c.setFont("Helvetica-Bold", 14)  # Aumentado de 12 para 14
        c.setFillColorRGB(0, 0, 0)
        c.drawString(x_pos + 5, y_pos - 35, codigo)  # Ajustada posição
        
        # Endereço - TEXTO MAIOR
        c.setFont("Helvetica", 12)  # Aumentado de 10 para 12
        endereco_linhas = []
        palavras = endereco_completo.split()
        linha_atual = ""
        
        for palavra in palavras:
            if len(linha_atual) + len(palavra) + 1 <= 25:  # Reduzido para 25 caracteres
                linha_atual += (" " if linha_atual else "") + palavra
            else:
                endereco_linhas.append(linha_atual)
                linha_atual = palavra
        
        if linha_atual:
            endereco_linhas.append(linha_atual)
        
        # Desenhar endereço
        for i, texto in enumerate(endereco_linhas):
            c.drawString(x_pos + 5, y_pos - 50 - (i * 15), texto)  # Aumentado espaçamento
        
        # Incrementar apenas a 3ª parte (p)
        p += 1
        etiqueta_atual += 1
        
        # Se chegou ao final e ainda tem etiquetas, criar nova página
        if etiqueta_atual % etiquetas_por_pagina == 0 and etiqueta_atual < quantidade:
            c.showPage()
    
    c.save()
    buffer.seek(0)
    return buffer

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/gerar', methods=['POST'])
def gerar_pdf():
    try:
        data = request.get_json()
        inicio = data.get('inicio', '').strip()
        fim = data.get('fim', '').strip()
        endereco = data.get('endereco', '').strip()
        
        if not inicio or not fim or not endereco:
            return jsonify({'error': 'Preencha todos os campos'}), 400
        
        quantidade = calcular_etiquetas(inicio, fim)
        if quantidade <= 0:
            return jsonify({'error': 'Intervalo inválido. Apenas a 3ª parte pode variar (ex: 01 a 05)'}), 400
        
        buffer = gerar_pdf_buffer(inicio, fim, endereco)
        if not buffer:
            return jsonify({'error': 'Erro ao gerar PDF'}), 500
        
        nome_arquivo = f"etiquetas_{inicio}_a_{fim}.pdf"
        
        return send_file(
            buffer,
            as_attachment=True,
            download_name=nome_arquivo,
            mimetype='application/pdf'
        )
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/calcular', methods=['POST'])
def calcular():
    data = request.get_json()
    inicio = data.get('inicio', '').strip()
    fim = data.get('fim', '').strip()
    
    quantidade = calcular_etiquetas(inicio, fim)
    valido = quantidade > 0
    
    if not valido:
        # Verifica qual parte está diferente
        padrao = r'(\d{2})\.(\d{2})\.(\d{2})\.(\d{2})'
        m1 = re.match(padrao, inicio)
        m2 = re.match(padrao, fim)
        
        if m1 and m2:
            b1, s1, p1, a1 = map(int, m1.groups())
            b2, s2, p2, a2 = map(int, m2.groups())
            
            partes_erradas = []
            if b1 != b2:
                partes_erradas.append("1ª parte")
            if s1 != s2:
                partes_erradas.append("2ª parte")
            if a1 != a2:
                partes_erradas.append("4ª parte")
            
            if partes_erradas:
                mensagem = f"As seguintes partes devem ser iguais: {', '.join(partes_erradas)}"
            else:
                mensagem = "A 3ª parte final deve ser maior que a inicial"
        else:
            mensagem = "Formato inválido"
    else:
        mensagem = f"Serão geradas {quantidade} etiquetas"
    
    return jsonify({
        'quantidade': quantidade,
        'valido': valido,
        'mensagem': mensagem
    })

if __name__ == '__main__':
    app.run(debug=True, port=5000)