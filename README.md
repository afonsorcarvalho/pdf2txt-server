# PDF2TXT Server

Serviço automatizado para conversão de arquivos PDF para TXT no Raspberry Pi, com monitoramento em tempo real de diretórios.

## 📋 Visão Geral

Este sistema monitora continuamente um ou mais diretórios configurados, convertendo automaticamente arquivos PDF para TXT sempre que:
- Um novo arquivo PDF é adicionado
- Um arquivo PDF existente é modificado
- O arquivo TXT correspondente não existe ou está desatualizado

## 🏗️ Arquitetura

```
pdf2txt-server/
├── config.yml              # Configuração dos diretórios monitorados
├── watcher.py              # Serviço principal de monitoramento
├── pdf2txt.py              # Script original de conversão PDF→TXT
├── pdf2txt-watcher.service # Unit do systemd
├── install.sh              # Script de instalação automatizada
├── requirements.txt        # Dependências Python
└── ciclos_exemplos/        # Diretório de exemplo com PDFs
```

## 🚀 Instalação

### Pré-requisitos
- Raspberry Pi OS (Debian/Ubuntu)
- Python 3.6+
- systemd
- Acesso sudo para instalação do serviço

### Instalação Automática
```bash
# Clone o repositório
git clone https://github.com/afonsorcarvalho/pdf2txt-server.git
cd pdf2txt-server

# Execute o instalador
chmod +x install.sh
./install.sh
```

O script de instalação irá:
1. Criar ambiente virtual Python (`.venv`)
2. Instalar dependências (`pdfplumber`, `watchdog`, `PyYAML`)
3. Criar diretórios de monitoramento se não existirem
4. Registrar serviço systemd
5. Iniciar o serviço automaticamente

## ⚙️ Configuração

### Arquivo `config.yml`

#### Configuração com múltiplos diretórios (recomendado):
```yaml
# Configuração de diretórios para monitoramento
# Suporte a múltiplos diretórios
watch_directories:
  - "/caminho/para/diretorio/pdf1"
  - "/caminho/para/diretorio/pdf2"
  - "/caminho/para/diretorio/pdf3"
```

#### Configuração com um único diretório (compatibilidade):
```yaml
watch_directory: "/caminho/para/diretorio/pdf"
```

**Exemplos:**
```yaml
# Múltiplos diretórios
watch_directories:
  - "/home/pi/documentos/pdfs"
  - "/home/pi/relatorios"
  - "/home/pi/manuais"

# Ou um único diretório (formato antigo)
watch_directory: "/home/pi/documentos/pdfs"
```

### Personalização do Serviço
Para alterar o usuário do serviço, edite o `install.sh`:
```bash
RUN_USER="seu_usuario"
```

## 🔧 Funcionamento Detalhado

### 1. Inicialização
- Carrega configuração do `config.yml`
- Cria diretórios de monitoramento se necessário
- Executa sincronização inicial de PDFs existentes em todos os diretórios
- Inicia monitoramento em tempo real para cada diretório

### 2. Sincronização Inicial
O sistema verifica todos os PDFs existentes em cada diretório configurado e:
- Converte PDFs que não possuem TXT correspondente
- Atualiza TXTs desatualizados (PDF mais recente que TXT)
- Ignora PDFs já sincronizados
- Processa cada diretório sequencialmente

### 3. Monitoramento em Tempo Real
Utiliza a biblioteca `watchdog` para detectar em cada diretório configurado:
- **Criação** de novos arquivos PDF
- **Modificação** de arquivos PDF existentes
- **Movimentação** de arquivos PDF para o diretório
- Cada diretório é monitorado independentemente

### 4. Lógica de Conversão
```python
def needs_conversion(pdf_path, txt_path):
    if not txt_path.exists():
        return True  # TXT não existe
    return pdf_path.stat().st_mtime > txt_path.stat().st_mtime
```

### 5. Processo de Conversão
1. Detecta evento de arquivo PDF
2. Verifica se conversão é necessária
3. Executa `pdf2txt.py` via subprocess
4. Registra resultado nos logs
5. Mantém sincronização automática

## 📊 Monitoramento

### Logs do Serviço
```bash
# Ver logs em tempo real
journalctl -u pdf2txt-watcher -f

# Ver logs das últimas 100 linhas
journalctl -u pdf2txt-watcher -n 100

# Ver status do serviço
systemctl status pdf2txt-watcher
```

### Exemplo de Logs
```
2024-01-15 10:30:15 INFO Convertendo PDF para TXT: /path/documento.pdf
2024-01-15 10:30:16 INFO Conversão concluída: /path/documento.txt
2024-01-15 10:30:20 INFO Convertendo PDF para TXT: /path/novo.pdf
```

## 🛠️ Gerenciamento do Serviço

### Comandos Úteis
```bash
# Iniciar serviço
sudo systemctl start pdf2txt-watcher

# Parar serviço
sudo systemctl stop pdf2txt-watcher

# Reiniciar serviço
sudo systemctl restart pdf2txt-watcher

# Habilitar inicialização automática
sudo systemctl enable pdf2txt-watcher

# Desabilitar inicialização automática
sudo systemctl disable pdf2txt-watcher

# Ver status
sudo systemctl status pdf2txt-watcher
```

### Desinstalação
```bash
# Parar e desabilitar serviço
sudo systemctl disable --now pdf2txt-watcher

# Remover arquivo do serviço
sudo rm -f /etc/systemd/system/pdf2txt-watcher.service

# Recarregar systemd
sudo systemctl daemon-reload

# Remover ambiente virtual (opcional)
rm -rf .venv
```

## 📁 Estrutura de Arquivos

### Entrada
- **Formato:** PDF
- **Localização:** Diretórios configurados em `config.yml`
- **Suporte:** Arquivos PDF padrão
- **Múltiplos diretórios:** Suporte a monitoramento simultâneo

### Saída
- **Formato:** TXT (UTF-8)
- **Localização:** Mesmo diretório do PDF
- **Nomenclatura:** `arquivo.pdf` → `arquivo.txt`

### Exemplo
```
# Estrutura com múltiplos diretórios
documentos/
├── relatorio.pdf    # Arquivo original
├── relatorio.txt    # Arquivo convertido
├── manual.pdf
└── manual.txt

relatorios/
├── vendas.pdf
└── vendas.txt

manuais/
├── usuario.pdf
└── usuario.txt
```

## 🔍 Dependências

### Python
- `pdfplumber` - Extração de texto de PDFs
- `watchdog` - Monitoramento de sistema de arquivos
- `PyYAML` - Leitura de arquivos de configuração

### Sistema
- `systemd` - Gerenciamento de serviços
- `python3` - Interpretador Python
- `git` - Controle de versão (opcional)

## 🐛 Solução de Problemas

### Serviço não inicia
```bash
# Verificar logs de erro
journalctl -u pdf2txt-watcher -n 50

# Verificar permissões do diretório
ls -la /caminho/do/diretorio

# Verificar configuração
cat config.yml
```

### Conversão falha
```bash
# Testar conversão manual
python3 pdf2txt.py arquivo.pdf

# Verificar dependências
pip list | grep pdfplumber
```

### Permissões
```bash
# Corrigir permissões do diretório
sudo chown -R $USER:$USER /caminho/do/diretorio
chmod 755 /caminho/do/diretorio
```

## 📝 Desenvolvimento

### Estrutura do Código
- `watcher.py` - Lógica principal de monitoramento
- `pdf2txt.py` - Conversão PDF→TXT (script original)
- `config.yml` - Configuração do sistema
- `install.sh` - Automação de instalação

### Adicionando Funcionalidades
1. Modifique `watcher.py` para nova lógica
2. Atualize `requirements.txt` se necessário
3. Teste com `python3 watcher.py --config config.yml`
4. Atualize documentação
5. Faça commit das alterações

## 📄 Licença

Este projeto está sob a licença MIT. Veja o arquivo LICENSE para detalhes.

## 🤝 Contribuição

1. Fork o projeto
2. Crie uma branch para sua feature (`git checkout -b feature/AmazingFeature`)
3. Commit suas mudanças (`git commit -m 'Add some AmazingFeature'`)
4. Push para a branch (`git push origin feature/AmazingFeature`)
5. Abra um Pull Request

## 📞 Suporte

Para dúvidas ou problemas:
- Abra uma issue no GitHub
- Verifique os logs do sistema
- Consulte a documentação do systemd

---

**Desenvolvido para Raspberry Pi** 🍓
