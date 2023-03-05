# @leoohermoso bots



# PyCharm

--------------------
Para facilitar criação de ambientes virtuais, instalacoes de pacotes necessários e ter um excelente IDE para desenvolvimento
sugiro a adoção do [PyCharm](https://www.jetbrains.com/pt-br/pycharm/download/#section=windows)



# Ambiente Virtual e Pacotes Necessários
###### Instruções para quem não usar o PyCharm

------------------
### Linux - Debian

    sudo apt install python3-venv

Agora na pasta onde foi salvo o código do django trader execute:

    python -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt 


### Windows

* Substitua c:\Python310\python pelo caminho onde esta instalado o python
* Substitua c:\path\to\ para o local onde foi baixado o django trader e lembre de adicionar env   


    c:\>c:\Python310\python -m venv c:\path\to\env

Como alternativa, se você configurou as variáveis PATH e PATHEXT

    c:\>python -m venv c:\path\to\myenv

Em seguida

    c:\path\to\env\Scripts\activate.bat
    cd c:\path\to\
    pip install -r requirements
    



# TradingView
______________________________________________________

Para o tradingview funcionar corretamente atualize as variáveis em djangotrader/settings.py com os valores corretoos 

    TRADINGVIEW_USER = ''
    TRADINGVIEW_PASSWORD = ''


# Iniciando

-----------------
Para rodar a aplicação digite:

    python manage.py runserver

E acesse o admin em http://localhost:8000/admin

    usuario: djangotrader
    senha: leoohermoso





 