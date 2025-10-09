# Protótipo de Aplicação Web com Flask

Este é o guia oficial para instalação e execução do projeto. Ele foi desenvolvido para ser uma aplicação web simples utilizando Flask como framework backend.

### Tecnologias Utilizadas

* **Frontend:** HTML 5
* **Backend:** Flask (um micro-framework em Python)
* **Banco de Dados:** SQLite 3

### Pré-requisitos

Antes de começar, certifique-se de que você tem os seguintes softwares instalados em sua máquina:
* [Python 3](https://www.python.org/downloads/)
* [Git](https://git-scm.com/downloads/)

---

### Instalação do Projeto

Siga os passos abaixo para clonar o repositório e configurar o ambiente de desenvolvimento.

1.  **Clone o repositório:**
    ```bash
    git clone [https://github.com/luiz07022009/Prototipo.git](https://github.com/luiz07022009/Prototipo.git)
    ```

2.  **Navegue até o diretório do projeto:**
    ```bash
    cd Prototipo
    ```

3.  **Crie um ambiente virtual:**
    *O ambiente virtual isola as dependências do projeto, evitando conflitos com outras aplicações Python.*
    ```bash
    python -m venv .venv
    ```

4.  **Ative o ambiente virtual:**
    * **No Windows:**
        ```powershell
        .venv\Scripts\activate
        ```
    * **No macOS e Linux:**
        ```bash
        source .venv/bin/activate
        ```

5.  **Instale as dependências:**
    *Com o ambiente virtual ativado, instale todas as bibliotecas necessárias com o seguinte comando:*
    ```bash
    pip install -r requirements.txt
    ```

---

### Como Rodar o Projeto

Com o ambiente já configurado, você pode iniciar o servidor de desenvolvimento.

1.  **Execute o servidor Flask:**
    *Certifique-se de que seu ambiente virtual ainda está ativado. Em seguida, execute:*
    ```bash
    python main.py
    ```
    > **Nota:** O comando `flutter run` não é aplicável aqui, pois ele é utilizado para projetos do framework Flutter, não para Flask.

2.  **Acesse a aplicação:**
    Após executar o comando acima, o terminal mostrará que o servidor está rodando e fornecerá um endereço local. Geralmente, será algo como:
    ```
    * Running on [http://12.0.0.1:5000](http://12.0.0.1:5000)
    ```
    Para acessar a aplicação, pressione **Ctrl** e **clique** no link, ou copie e cole a URL em seu navegador de preferência.
