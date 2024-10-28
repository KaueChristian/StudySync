import bcrypt

def gerar_hash_senha(senha: str) -> bytes:
    senha_byte = senha.encode('utf-8')
    
    salt = bcrypt.gensalt()
    
    hash_senha = bcrypt.hashpw(senha_byte, salt)
    
    return hash_senha

def verificar_senha(senha: str, hash_senha: bytes) -> bool:
    senha_byte = senha.encode('utf-8')
    
    return bcrypt.checkpw(senha_byte, hash_senha)