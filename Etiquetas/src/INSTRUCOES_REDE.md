# 🚀 Como Rodar na Rede Local

## 📋 Pré-requisitos
1. **Python 3.8 ou superior** instalado
2. Computadores na **mesma rede Wi-Fi/Ethernet**
3. **Firewall** configurado para permitir conexões na porta 5000

## 🛠️ Instalação Rápida (Windows)

### Método 1: Script Automático
1. Execute `start_server.bat` como Administrador
2. Aguarde a instalação automática das dependências
3. Anote o IP que aparece na tela

### Método 2: Manual
```cmd
# 1. Abra Prompt de Comando como Administrador
# 2. Navegue até a pasta do projeto
cd C:\caminho\para\projeto

# 3. Instale dependências
pip install flask reportlab

# 4. Execute
python app.py