import flet as ft
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
import re

def main(page: ft.Page):
    page.title = "Gerador de Etiquetas de Endereço"
    page.scroll = "auto"
    page.padding = 20

    # Função para calcular a quantidade de etiquetas
    def calcular_etiquetas(inicio, fim):
        padrao = r'(\d{2})\.(\d{2})\.(\d{2})\.(\d{2})'
        m1 = re.match(padrao, inicio)
        m2 = re.match(padrao, fim)
        
        if not m1 or not m2:
            return 0
        
        # Converte para inteiros
        b1, s1, p1, a1 = map(int, m1.groups())
        b2, s2, p2, a2 = map(int, m2.groups())
        
        # Calcula o total
        total = (b2 - b1) * 10000 + (s2 - s1) * 100 + (p2 - p1) * 10 + (a2 - a1) + 1
        return total if total > 0 else 0

    def gerar_pdf(e):
        inicio = txt_inicio.value.strip()
        fim = txt_fim.value.strip()
        endereco_completo = txt_endereco.value.strip()
        
        if not inicio or not fim or not endereco_completo:
            page.snack_bar = ft.SnackBar(ft.Text("Preencha todos os campos!"))
            page.snack_bar.open = True
            page.update()
            return
        
        # Calcula quantidade de etiquetas
        quantidade = calcular_etiquetas(inicio, fim)
        if quantidade == 0:
            page.snack_bar = ft.SnackBar(ft.Text("Intervalo inválido!"))
            page.snack_bar.open = True
            page.update()
            return
        
        # Nome do arquivo PDF
        nome_arquivo = f"etiquetas_{inicio}_a_{fim}.pdf"
        
        # Cria o PDF
        c = canvas.Canvas(nome_arquivo, pagesize=A4)
        width, height = A4
        
        # Configurações das etiquetas (ajustar conforme necessário)
        etiqueta_largura = 90 * mm
        etiqueta_altura = 40 * mm
        margem_x = 15 * mm
        margem_y = 15 * mm
        espacamento_x = 5 * mm
        espacamento_y = 5 * mm
        
        colunas = int((width - 2 * margem_x) / (etiqueta_largura + espacamento_x))
        linhas = int((height - 2 * margem_y) / (etiqueta_altura + espacamento_y))
        
        etiquetas_por_pagina = colunas * linhas
        
        # Extrai partes do código inicial
        padrao = r'(\d{2})\.(\d{2})\.(\d{2})\.(\d{2})'
        match = re.match(padrao, inicio)
        if not match:
            return
        
        b, s, p, a = map(int, match.groups())
        
        etiqueta_atual = 0
        pagina = 0
        
        while etiqueta_atual < quantidade:
            if etiqueta_atual % etiquetas_por_pagina == 0:
                if pagina > 0:
                    c.showPage()
                pagina += 1
            
            linha = (etiqueta_atual % etiquetas_por_pagina) // colunas
            coluna = (etiqueta_atual % etiquetas_por_pagina) % colunas
            
            x = margem_x + coluna * (etiqueta_largura + espacamento_x)
            y = height - margem_y - (linha + 1) * (etiqueta_altura + espacamento_y)
            
            # Gera o código atual
            codigo = f"{b:02d}.{s:02d}.{p:02d}.{a:02d}"
            
            # Desenha a etiqueta
            c.setFont("Helvetica-Bold", 12)
            c.drawString(x + 5, y + etiqueta_altura - 15, codigo)
            
            c.setFont("Helvetica", 10)
            # Divide o endereço em linhas se for muito longo
            endereco_linhas = []
            palavras = endereco_completo.split()
            linha_atual = ""
            for palavra in palavras:
                if len(linha_atual) + len(palavra) + 1 <= 30:  # Aprox. 30 caracteres por linha
                    linha_atual += (" " if linha_atual else "") + palavra
                else:
                    endereco_linhas.append(linha_atual)
                    linha_atual = palavra
            if linha_atual:
                endereco_linhas.append(linha_atual)
            
            for i, texto in enumerate(endereco_linhas):
                c.drawString(x + 5, y + etiqueta_altura - 35 - i*12, texto)
            
            # Incrementa o código
            a += 1
            if a > 99:
                a = 0
                p += 1
                if p > 99:
                    p = 0
                    s += 1
                    if s > 99:
                        s = 0
                        b += 1
            
            etiqueta_atual += 1
        
        c.save()
        
        # Informa o usuário
        page.snack_bar = ft.SnackBar(ft.Text(f"PDF gerado com {quantidade} etiquetas: {nome_arquivo}"))
        page.snack_bar.open = True
        page.update()
        
        # Prepara para a próxima geração
        txt_inicio.value = f"{b:02d}.{s:02d}.{p:02d}.{a:02d}"
        txt_fim.value = ""
        txt_endereco.value = ""
        page.update()

    # Componentes da interface
    txt_inicio = ft.TextField(
        label="Código Inicial (ex: 03.49.01.00)",
        width=300,
        value="03.49.01.00"
    )
    
    txt_fim = ft.TextField(
        label="Código Final (ex: 03.49.05.00)",
        width=300,
        value="03.49.05.00"
    )
    
    txt_endereco = ft.TextField(
        label="Endereço Completo",
        width=400,
        multiline=True,
        min_lines=2,
        max_lines=3,
        value="RUA | PRÉDIO | NÍVEL | APARTAMENTO"
    )
    
    btn_gerar = ft.ElevatedButton(
        "Gerar PDF de Etiquetas",
        on_click=gerar_pdf,
        icon=ft.icons.PRINT
    )
    
    # Layout
    page.add(
        ft.Text("Gerador de Etiquetas de Endereço", size=24, weight=ft.FontWeight.BOLD),
        ft.Text("Insira o intervalo de códigos e o endereço completo:"),
        ft.Row([txt_inicio, txt_fim]),
        txt_endereco,
        ft.Container(height=20),
        btn_gerar,
        ft.Container(height=20),
        ft.Text("Exemplos:", weight=ft.FontWeight.BOLD),
        ft.Text("• 03.49.01.00 até 03.49.05.00 = 5 etiquetas"),
        ft.Text("• 03.49.01.00 até 03.50.06.00 = 10 etiquetas"),
    )

# Execute a aplicação
ft.app(target=main)