import requests
from bs4 import BeautifulSoup

def search(termo, materia):
    query = f"{termo} em {materia}".replace(' ', '+')
    url = f"https://www.google.com/search?q={query}"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.121 Safari/537.36'
    }
    
    response = requests.get(url, headers=headers)
    
    # Verifique o código de status
    if response.status_code != 200:
        print(f"Erro HTTP {response.status_code}")
        return []
    
    # Verifique o conteúdo da resposta
    print(response.text)  # Isso vai exibir o HTML que você está recebendo
    
    soup = BeautifulSoup(response.text, 'html.parser')
    
    resultados = []
    for item in soup.find_all('div', class_='BNeawe vvjwJb AP7Wnd'):
        resultados.append(item.text)
    
    if not resultados:
        print("Nenhum resultado encontrado. Verifique a estrutura HTML ou se houve bloqueio.")
    
    return resultados

print(search("inteligência artificial", "ciência da computação"))
