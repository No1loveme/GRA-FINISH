from Crypto.Cipher import AES
import base64

def aes_encrypt(data, key_size):
    key = b'This is a key128' if key_size == 128 else b'This is a key456This is a key456'
    cipher = AES.new(key, AES.MODE_EAX)
    ciphertext, tag = cipher.encrypt_and_digest(data.encode())
    return base64.b64encode(cipher.nonce + tag + ciphertext).decode()

def aes_decrypt(encrypted_data, key_size):
    key = b'This is a key128' if key_size == 128 else b'This is a key456This is a key456'
    try:
        data = base64.b64decode(encrypted_data)
        nonce = data[:16]
        tag = data[16:32]
        ciphertext = data[32:]
        cipher = AES.new(key, AES.MODE_EAX, nonce=nonce)
        return cipher.decrypt_and_verify(ciphertext, tag).decode()
    except (ValueError, KeyError):
        return "解密失败"