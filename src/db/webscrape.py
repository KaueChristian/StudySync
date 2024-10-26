import requests
from bs4 import BeautifulSoup
import time

class WebScrape:
    def web_scrape(self, tags):
        results = {}
        for tag in tags:
            # URL para busca no Bing
            url = f"https://www.bing.com/search?q={tag.replace(' ', '+')}"
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.93 Safari/537.36',
            }

            try:
                response = requests.get(url, headers=headers)
                response.raise_for_status()  # Lança um erro para códigos de status HTTP errados

                soup = BeautifulSoup(response.text, 'html.parser')

                # Busca por links no Bing
                links = soup.find_all('a', href=True)

                # Filtra os links que começam com "http" ou "https"
                valid_links = [link['href'] for link in links if link['href'].startswith(('http', 'https'))]

                if valid_links:
                    results[tag] = valid_links
                else:
                    print(f"Nenhum link encontrado para a tag: {tag}")

            except requests.exceptions.HTTPError as e:
                print(f"Erro ao acessar a página: {e} para a tag: {tag}")
            except Exception as e:
                print(f"Ocorreu um erro: {e} para a tag: {tag}")

            time.sleep(1)  # Aguardar entre as requisições

        return results

'''if __name__ == "__main__":
    scraper = WebScrape()
    tags = ["carros", "motos"]
    results = scraper.web_scrape(tags)
    print(results)

    for tag, urls in results.items():
        print(f"\nResultados para '{tag}':")
        for url in urls:
            print(f" - {url}")
'''