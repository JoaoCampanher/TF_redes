## Simulador de Roteamento em Redes

Este projeto implementa um simulador de roteamento dinâmico usando sockets UDP em Python. Ele gerencia tabelas de roteamento entre roteadores (representados por dispositivos na rede) e permite a troca de mensagens entre os nós. A tabela de roteamento é atualizada dinamicamente com base nas mensagens recebidas dos vizinhos.

---

## Pré-requisitos

- **Python 3.8 ou superior** instalado no sistema.
- Acesso à rede para permitir a comunicação entre os dispositivos.

---

### 1. Execução

O programa pode ser executado de três formas diferentes:

#### Opção 1: Usando o arquivo `roteadores.txt` (IP automático)

O arquivo `roteadores.txt` deve conter os IPs dos roteadores vizinhos (um por linha). Você pode adicionar comentários usando `#`. Exemplo:

```
192.168.0.101 # Roteador 1
192.168.0.102 # Roteador 2
192.168.0.103 # Roteador 3
```

---

Execute o programa sem argumentos. O IP do próprio dispositivo será obtido automaticamente.

```bash
python main.py
```

#### Opção 2: Informando IPs manualmente pela linha de comando

Você pode especificar os IPs diretamente nos argumentos da execução.

##### 2.1 Com IP próprio automático

Use `-` no lugar do IP próprio e forneça os IPs dos vizinhos:

```bash
python main.py - 192.168.0.101 192.168.0.102
```

##### 2.2 Com IP próprio manual

Informe o IP próprio seguido dos IPs dos vizinhos:

```bash
python main.py 192.168.0.100 192.168.0.101 192.168.0.102
```

---

### 2. Observações

- Certifique-se de que todos os dispositivos estejam na mesma rede e que as portas necessárias (19000) estejam abertas.
- O IP automático depende de como o sistema obtém o IP. Se ocorrerem problemas, informe o IP manualmente.
- Utilize o terminal para acompanhar mensagens recebidas, enviadas e alterações na tabela de roteamento.

---

### 3. Para executar testes locais

O arquivo **`test.bat`** executa múltiplas instâncias do programa **`main.py`** em novas janelas do Prompt de Comando, simulando roteadores na rede. Cada instância é configurada com um IP próprio e os IPs de seus vizinhos.

#### Exemplo:

```bat
start cmd /k "python main.py 127.0.0.1 127.0.0.2"
start cmd /k "python main.py 127.0.0.2 127.0.0.1 127.0.0.3"
start cmd /k "python main.py 127.0.0.3 127.0.0.2"
```

Este script inicia três roteadores:

- **127.0.0.1** conectado a **127.0.0.2**.
- **127.0.0.2** conectado a **127.0.0.1** e **127.0.0.3**.
- **127.0.0.3** conectado a **127.0.0.2**.

Para executar o script, execute o seguinte comando em um terminal CMD ou powershell:
```
.\test.bat
```
