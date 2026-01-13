from flask import Flask, render_template, request, send_file, jsonify
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import mm
from reportlab.graphics.barcode import code128
from reportlab.graphics.shapes import Drawing
from reportlab.graphics import renderPDF
import re
import io
import math

app = Flask(__name__)

# Tamanho personalizado da página (99.8 x 80.0 mm)
PAGE_WIDTH = 99.8 * mm
PAGE_HEIGHT = 80.0 * mm

# Tamanho da etiqueta (90 x 35 mm)
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
    
    # Verifica se a 4ª parte é 00
    if a1 != 0 or a2 != 0:
        return 0
    
    # Verifica se a 1ª parte é igual
    if b1 != b2:
        return 0
    
    # Calcula total
    total = 0
    
    # Começa do código inicial
    b, s, p, a = b1, s1, p1, a1
    
    while True:
        total += 1
        
        # Verifica se chegou ao fim
        if b == b2 and s == s2 and p == p2 and a == a2:
            break
        
        # Incrementa: primeiro a 3ª parte até 05
        p += 1
        if p > 5:  # Se passar de 05, reseta para 01 e incrementa a 2ª parte
            p = 1
            s += 1
        
        if s > 99:  # Se passar de 99, reseta para 01 e incrementa a 1ª parte
            s = 1
            b += 1
        
        # Verifica se ultrapassou o limite
        if b > b2 or (b == b2 and s > s2) or (b == b2 and s == s2 and p > p2):
            return 0
    
    return total

def gerar_pdf_buffer(inicio, fim, endereco_completo):
    """Gera PDF na memória com layout EXATO do exemplo"""
    quantidade = calcular_etiquetas(inicio, fim)
    if quantidade <= 0:
        return None
    
    # Extrai partes do código inicial
    padrao = r'(\d{2})\.(\d{2})\.(\d{2})\.(\d{2})'
    match = re.match(padrao, inicio)
    if not match:
        return None
    
    b, s, p, a = map(int, match.groups())
    
    # Extrai partes do código final para validação
    match_fim = re.match(padrao, fim)
    if not match_fim:
        return None
    
    b_fim, s_fim, p_fim, a_fim = map(int, match_fim.groups())
    
    # Criar buffer na memória
    buffer = io.BytesIO()
    
    # Criar canvas com tamanho personalizado
    c = canvas.Canvas(buffer, pagesize=(PAGE_WIDTH, PAGE_HEIGHT))
    
    # Calcular número de páginas (2 etiquetas por página)
    etiquetas_por_pagina = 2
    
    # Margens para centralizar verticalmente
    espacamento_vertical = (PAGE_HEIGHT - (2 * ETIQUETA_HEIGHT))
    margem_superior = espacamento_vertical / 2 + ETIQUETA_HEIGHT
    margem_inferior = espacamento_vertical / 2
    
    etiqueta_atual = 0
    pagina = 1
    
    while etiqueta_atual < quantidade:
        # Se não for a primeira etiqueta da página e for posição par, nova página
        if etiqueta_atual > 0 and etiqueta_atual % etiquetas_por_pagina == 0:
            c.showPage()
            pagina += 1
        
        # Determinar posição Y (superior para etiquetas pares, inferior para ímpares)
        posicao_na_pagina = etiqueta_atual % etiquetas_por_pagina
        if posicao_na_pagina == 0:  # Etiqueta superior
            y_pos = margem_superior - ETIQUETA_HEIGHT
        else:  # Etiqueta inferior
            y_pos = margem_inferior
        
        # Centralizar horizontalmente
        x_pos = (PAGE_WIDTH - ETIQUETA_WIDTH) / 2
        
        # Código atual
        codigo = f"{b:02d}.{s:02d}.{p:02d}.{a:02d}"
        
        # **GERAR CÓDIGO DE BARRAS - LARGURA COMPLETA E METADE DA ALTURA**
        try:
            # Código de barras Code128 ocupando 80% da largura da etiqueta
            barcode_width = ETIQUETA_WIDTH * 0.8
            barcode_height = ETIQUETA_HEIGHT * 0.4  # Metade da altura da etiqueta
            
            # Calcular posição para centralizar o código de barras
            barcode_x = x_pos + (ETIQUETA_WIDTH - barcode_width) / 2
            barcode_y = y_pos + ETIQUETA_HEIGHT - barcode_height - 5
            
            # Criar código de barras com largura ajustada
            barcode = code128.Code128(
                codigo,
                barWidth=0.35,
                barHeight=barcode_height - 10,
                humanReadable=False
            )
            
            # Ajustar escala para ocupar a largura desejada
            barcode_width_actual = barcode.width
            scale = barcode_width / barcode_width_actual
            
            # Salvar estado do canvas, aplicar transformação e desenhar
            c.saveState()
            c.translate(barcode_x, barcode_y)
            c.scale(scale, 1)  # Apenas escala horizontal
            barcode.drawOn(c, 0, 0)
            c.restoreState()
            
        except Exception as e:
            print(f"Erro ao gerar código de barras: {e}")
            # Fallback: desenhar retângulo no lugar
            c.setStrokeColorRGB(0.7, 0.7, 0.7)
            c.setLineWidth(0.5)
            c.rect(barcode_x, barcode_y, barcode_width, barcode_height, stroke=1, fill=0)
        
        # **TEXTO DO CÓDIGO - MAIOR E CENTRALIZADO**
        c.setFont("Helvetica-Bold", 12)
        c.setFillColorRGB(0, 0, 0)
        
        # Centralizar texto horizontalmente
        texto_largura = c.stringWidth(codigo, "Helvetica-Bold", 12)
        texto_x = x_pos + (ETIQUETA_WIDTH - texto_largura) / 2
        texto_y = y_pos + ETIQUETA_HEIGHT - barcode_height - 20  # Abaixo do código de barras
        
        c.drawString(texto_x, texto_y, codigo)
        
        # **ENDEREÇO - CENTRALIZADO E COM QUEBRA DE LINHA**
        c.setFont("Helvetica", 10)
        endereco_linhas = []
        palavras = endereco_completo.split()
        linha_atual = ""
        
        for palavra in palavras:
            if len(linha_atual) + len(palavra) + 1 <= 30:  # Limite de caracteres por linha
                linha_atual += (" " if linha_atual else "") + palavra
            else:
                endereco_linhas.append(linha_atual)
                linha_atual = palavra
        
        if linha_atual:
            endereco_linhas.append(linha_atual)
        
        # Calcular altura total do texto do endereço
        altura_texto = len(endereco_linhas) * 12
        
        # Posicionar endereço centralizado verticalmente na área restante
        area_restante = ETIQUETA_HEIGHT - barcode_height - 30  # Altura disponível para endereço
        inicio_endereco_y = y_pos + (area_restante - altura_texto) / 2
        
        # Desenhar cada linha do endereço centralizada
        for i, texto in enumerate(endereco_linhas):
            texto_largura = c.stringWidth(texto, "Helvetica", 10)
            linha_x = x_pos + (ETIQUETA_WIDTH - texto_largura) / 2
            linha_y = inicio_endereco_y - (i * 12)
            c.drawString(linha_x, linha_y, texto)
        
        # **VERIFICA SE CHEGOU AO FIM**
        if b == b_fim and s == s_fim and p == p_fim:
            break
        
        # **INCREMENTA COM AS REGRAS CORRETAS:**
        # 1. Incrementa a 3ª parte
        p += 1
        
        # 2. Se a 3ª parte passar de 05, reseta para 01 e incrementa a 2ª parte
        if p > 5:
            p = 1
            s += 1
            
            # 3. Se a 2ª parte passar de 99, reseta para 01 e incrementa a 1ª parte
            if s > 99:
                s = 1
                b += 1
        
        etiqueta_atual += 1
    
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
        
        # Validação básica
        padrao = r'(\d{2})\.(\d{2})\.(\d{2})\.(\d{2})'
        if not re.match(padrao, inicio) or not re.match(padrao, fim):
            return jsonify({'error': 'Formato inválido. Use: XX.XX.XX.XX'}), 400
        
        quantidade = calcular_etiquetas(inicio, fim)
        if quantidade <= 0:
            return jsonify({'error': 'Intervalo inválido ou regras não atendidas'}), 400
        
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
    
    # Validação do formato
    padrao = r'(\d{2})\.(\d{2})\.(\d{2})\.(\d{2})'
    m1 = re.match(padrao, inicio)
    m2 = re.match(padrao, fim)
    
    if not m1 or not m2:
        return jsonify({
            'quantidade': 0,
            'valido': False,
            'mensagem': 'Formato inválido! Use: XX.XX.XX.XX'
        })
    
    b1, s1, p1, a1 = map(int, m1.groups())
    b2, s2, p2, a2 = map(int, m2.groups())
    
    # Verifica a 4ª parte
    if a1 != 0 or a2 != 0:
        return jsonify({
            'quantidade': 0,
            'valido': False,
            'mensagem': 'A 4ª parte deve ser sempre 00'
        })
    
    # Verifica ordem
    if b1 > b2 or (b1 == b2 and s1 > s2) or (b1 == b2 and s1 == s2 and p1 > p2):
        return jsonify({
            'quantidade': 0,
            'valido': False,
            'mensagem': 'Código final deve ser maior que o inicial'
        })
    
    # Calcula quantidade
    quantidade = calcular_etiquetas(inicio, fim)
    valido = quantidade > 0
    
    if not valido:
        mensagem = "Intervalo inválido. Regras:\n"
        mensagem += "1. 4ª parte = 00 (fixo)\n"
        mensagem += "2. 3ª parte vai de 01 a 05\n"
        mensagem += "3. 2ª parte vai de 01 a 99\n"
        mensagem += "4. Apenas 3ª e 2ª partes podem variar"
    else:
        paginas = math.ceil(quantidade / 2)
        mensagem = f"{quantidade} etiquetas ({paginas} {'página' if paginas == 1 else 'páginas'})"
    
    return jsonify({
        'quantidade': quantidade,
        'valido': valido,
        'mensagem': mensagem
    })

@app.route('/sequencia/<inicio>/<fim>')
def mostrar_sequencia(inicio, fim):
    """Endpoint para testar a sequência gerada"""
    sequencia = []
    
    padrao = r'(\d{2})\.(\d{2})\.(\d{2})\.(\d{2})'
    m1 = re.match(padrao, inicio)
    m2 = re.match(padrao, fim)
    
    if not m1 or not m2:
        return jsonify({'error': 'Formato inválido'})
    
    b, s, p, a = map(int, m1.groups())
    b_fim, s_fim, p_fim, a_fim = map(int, m2.groups())
    
    while True:
        codigo = f"{b:02d}.{s:02d}.{p:02d}.{a:02d}"
        sequencia.append(codigo)
        
        if b == b_fim and s == s_fim and p == p_fim:
            break
        
        # Incrementa com as regras
        p += 1
        if p > 5:
            p = 1
            s += 1
        
        if s > 99:
            s = 1
            b += 1
        
        # Verifica limites
        if b > b_fim or (b == b_fim and s > s_fim) or (b == b_fim and s == s_fim and p > p_fim):
            break
    
    return jsonify({
        'sequencia': sequencia,
        'total': len(sequencia)
    })

if __name__ == '__main__':
    app.run(debug=True, port=5000)