import requests
from bs4 import BeautifulSoup
import time

        
class WebScrape:
    def __init__(self, agenda_instance):
        self.agenda = agenda_instance
        
    def web_scrape(self, tarefa_id):
        tag = self.agenda.get_topico_by_id(tarefa_id)
        
        if not tag:
            print(f"Nenhum tópico encontrado com este ID: {tarefa_id}")
            return {}
            
        results = {}
        
        url = f"https://www.bing.com/search?q={tag.replace(' ', '+')}"
            
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.93 Safari/537.36',
        }

        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()  

            soup = BeautifulSoup(response.text, 'html.parser')

            
            links = soup.find_all('a', href=True)

            
            valid_links = [link['href'] for link in links if link['href'].startswith(('http', 'https'))]

            if valid_links:
                results[tag] = valid_links
            else:
                print(f"Nenhum link encontrado para a tag: {tag}")

        except requests.exceptions.HTTPError as e:
            print(f"Erro ao acessar a página: {e} para a tag: {tag}")
        except Exception as e:
            print(f"Ocorreu um erro: {e} para a tag: {tag}")

        time.sleep(1)

        return results