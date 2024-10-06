import google.generativeai as genai

genai.configure(api_key="AIzaSyCyhvDgJlEbBqyq_kvjCwoag_hjTzscdB0") # Checa a chave da API e faz as requisições ao gemini

model = genai.GenerativeModel('gemini-pro')

# Inicialização do Chat
chat = model.start_chat(history=[])

materia = "Historia"
subtopico = "Era vargas"

prompt = f"Gemini, quero que vc me passe um link da materia {materia} com o tópico {subtopico}"

# Loop de interação com o usuário 
while True:
    texto =  input("Digite uma mensagem: ")

    if texto == "sair":
        break

    response = chat.send_message(texto)
    print("Gemini:", response.text, "\n")

print("Encerrando Chat")

