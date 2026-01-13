from flask import Flask, render_template, request, send_file, jsonify
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import mm
from reportlab.graphics.barcode import code128
from reportlab.graphics.shapes import Drawing
from reportlab.graphics import renderPDF
import re
import io
import math
import socket
import netifaces
from datetime import datetime

app = Flask(__name__)

# Configurações da rede
def get_network_info():
    """Obtém informações da rede"""
    info = {
        'hostname': socket.gethostname(),
        'local_ip': '127.0.0.1',
        'network_ips': [],
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }
    
    try:
        # Obtém todos os IPs da rede
        for interface in netifaces.interfaces():
            addrs = netifaces.ifaddresses(interface)
            if netifaces.AF_INET in addrs:
                for addr in addrs[netifaces.AF_INET]:
                    ip = addr['addr']
                    if ip != '127.0.0.1':
                        info['network_ips'].append(ip)
                        if not ip.startswith('169.254'):  # Ignora APIPA
                            info['local_ip'] = ip
    except:
        pass
    
    return info

# Tamanho da página da impressora Argox
PAGE_WIDTH = 99.8 * mm
PAGE_HEIGHT = 79.0 * mm
ETIQUETA_WIDTH = 90 * mm
ETIQUETA_HEIGHT = 35 * mm
MARGEM_HORIZONTAL = (PAGE_WIDTH - ETIQUETA_WIDTH) / 2
MARGEM_VERTICAL = (PAGE_HEIGHT - (2 * ETIQUETA_HEIGHT)) / 2

def calcular_etiquetas(inicio, fim):
    """Calcula a quantidade de etiquetas entre dois códigos"""
    padrao = r'(\d{2})\.(\d{2})\.(\d{2})\.(\d{2})'
    m1 = re.match(padrao, inicio)
    m2 = re.match(padrao, fim)
    
    if not m1 or not m2:
        return 0
    
    b1, s1, p1, a1 = map(int, m1.groups())
    b2, s2, p2, a2 = map(int, m2.groups())
    
    if a1 != 0 or a2 != 0:
        return 0
    
    if b1 != b2:
        return 0
    
    total = 0
    b, s, p, a = b1, s1, p1, a1
    
    while True:
        total += 1
        
        if b == b2 and s == s2 and p == p2 and a == a2:
            break
        
        p += 1
        if p > 5:
            p = 1
            s += 1
        
        if s > 99:
            s = 1
            b += 1
        
        if b > b2 or (b == b2 and s > s2) or (b == b2 and s == s2 and p > p2):
            return 0
    
    return total

def gerar_pdf_buffer(inicio, fim, endereco_completo):
    """Gera PDF na memória"""
    quantidade = calcular_etiquetas(inicio, fim)
    if quantidade <= 0:
        return None
    
    padrao = r'(\d{2})\.(\d{2})\.(\d{2})\.(\d{2})'
    match = re.match(padrao, inicio)
    if not match:
        return None
    
    b, s, p, a = map(int, match.groups())
    
    match_fim = re.match(padrao, fim)
    if not match_fim:
        return None
    
    b_fim, s_fim, p_fim, a_fim = map(int, match_fim.groups())
    
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=(PAGE_WIDTH, PAGE_HEIGHT))
    etiquetas_por_pagina = 2
    etiqueta_atual = 0
    
    while etiqueta_atual < quantidade:
        if etiqueta_atual > 0 and etiqueta_atual % etiquetas_por_pagina == 0:
            c.showPage()
        
        posicao_na_pagina = etiqueta_atual % etiquetas_por_pagina
        
        if posicao_na_pagina == 0:
            y_pos = PAGE_HEIGHT - MARGEM_VERTICAL - ETIQUETA_HEIGHT
        else:
            y_pos = MARGEM_VERTICAL
        
        x_pos = MARGEM_HORIZONTAL
        codigo = f"{b:02d}.{s:02d}.{p:02d}.{a:02d}"
        
        # Borda da etiqueta
        c.setStrokeColorRGB(0, 0, 0)
        c.setLineWidth(0.5)
        c.rect(x_pos, y_pos, ETIQUETA_WIDTH, ETIQUETA_HEIGHT, stroke=1, fill=0)
        
        # Código de barras
        try:
            barcode_height = ETIQUETA_HEIGHT * 0.25
            barcode_width = ETIQUETA_WIDTH * 0.8
            barcode_x = x_pos + (ETIQUETA_WIDTH - barcode_width) / 2
            barcode_y = y_pos + ETIQUETA_HEIGHT - barcode_height - 3
            
            barcode = code128.Code128(
                codigo,
                barWidth=0.25,
                barHeight=barcode_height - 2,
                humanReadable=False
            )
            
            barcode_real_width = barcode.width
            scale = barcode_width / barcode_real_width
            
            c.saveState()
            c.translate(barcode_x, barcode_y)
            c.scale(scale, 1)
            barcode.drawOn(c, 0, 0)
            c.restoreState()
            
        except Exception as e:
            print(f"Erro código de barras: {e}")
        
        # Código
        c.setFont("Helvetica-Bold", 16)
        c.setFillColorRGB(0, 0, 0)
        texto_largura = c.stringWidth(codigo, "Helvetica-Bold", 16)
        codigo_x = x_pos + (ETIQUETA_WIDTH - texto_largura) / 2
        codigo_y = y_pos + ETIQUETA_HEIGHT - barcode_height - 18
        c.drawString(codigo_x, codigo_y, codigo)
        
        # Endereço
        c.setFont("Helvetica", 12)
        endereco_texto = endereco_completo
        texto_largura_endereco = c.stringWidth(endereco_texto, "Helvetica", 12)
        
        if texto_largura_endereco > ETIQUETA_WIDTH * 0.9:
            c.setFont("Helvetica", 11)
            texto_largura_endereco = c.stringWidth(endereco_texto, "Helvetica", 11)
        
        endereco_x = x_pos + (ETIQUETA_WIDTH - texto_largura_endereco) / 2
        altura_restante = ETIQUETA_HEIGHT - barcode_height - 25
        endereco_y = y_pos + (altura_restante / 2) + 5
        c.drawString(endereco_x, endereco_y, endereco_texto)
        
        if b == b_fim and s == s_fim and p == p_fim:
            break
        
        p += 1
        if p > 5:
            p = 1
            s += 1
        
        if s > 99:
            s = 1
            b += 1
        
        etiqueta_atual += 1
    
    c.save()
    buffer.seek(0)
    return buffer

@app.route('/')
def index():
    network_info = get_network_info()
    return render_template('index.html', 
                         network_info=network_info,
                         local_ip=network_info['local_ip'])

@app.route('/network')
def network_info():
    """Página com informações da rede"""
    info = get_network_info()
    return render_template('network_info.html', info=info)

@app.route('/gerar', methods=['POST'])
def gerar_pdf():
    try:
        data = request.get_json()
        inicio = data.get('inicio', '').strip()
        fim = data.get('fim', '').strip()
        endereco = data.get('endereco', '').strip()
        
        if not inicio or not fim or not endereco:
            return jsonify({'error': 'Preencha todos os campos'}), 400
        
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
    
    if a1 != 0 or a2 != 0:
        return jsonify({
            'quantidade': 0,
            'valido': False,
            'mensagem': 'A 4ª parte deve ser sempre 00'
        })
    
    if b1 > b2 or (b1 == b2 and s1 > s2) or (b1 == b2 and s1 == s2 and p1 > p2):
        return jsonify({
            'quantidade': 0,
            'valido': False,
            'mensagem': 'Código final deve ser maior que o inicial'
        })
    
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
        mensagem = f"{quantidade} etiquetas em {paginas} {'página' if paginas == 1 else 'páginas'} (2 por página)"
    
    return jsonify({
        'quantidade': quantidade,
        'valido': valido,
        'mensagem': mensagem
    })

if __name__ == '__main__':
    # Configurações para rede
    network_info = get_network_info()
    local_ip = network_info['local_ip']
    port = 5000
    
    print("=" * 60)
    print("🚀 GERADOR DE ETIQUETAS - SERVIDOR DE REDE")
    print("=" * 60)
    print(f"📛 Hostname: {network_info['hostname']}")
    print(f"📍 IP Local: 127.0.0.1")
    print(f"🌐 IP da Rede: {local_ip}")
    print(f"🔌 Porta: {port}")
    print("=" * 60)
    print(f"🔗 URL Local: http://127.0.0.1:{port}")
    print(f"🌍 URL da Rede: http://{local_ip}:{port}")
    print("=" * 60)
    
    if network_info['network_ips']:
        print("📡 IPs disponíveis na rede:")
        for ip in network_info['network_ips']:
            print(f"   → http://{ip}:{port}")
    print("=" * 60)
    print("📢 Acesse de qualquer computador na rede local!")
    print("=" * 60)
    
    # Rodar servidor
    app.run(
        host='0.0.0.0',  # Aceita conexões de qualquer IP
        port=port,
        debug=True,
        threaded=True  # Permite múltiplas conexões simultâneas
    )