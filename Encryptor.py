from cryptography.fernet import Fernet
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives import hashes

def generate_key():
    key = Fernet.generate_key()
    return key

def generate_private_key():
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048, 
        backend=default_backend())
    return private_key

def encrypt_symmetric_key(public_key, sym_key):
    e_key = public_key.encrypt(
                        sym_key,
                        padding.OAEP(
                            mgf=padding.MGF1(algorithm=hashes.SHA256()),
                            algorithm=hashes.SHA256(),
                            label=None
                        )
                    )
    return e_key

def encrypt(p_text, key):
    cipher_suite = Fernet(key)
    return cipher_suite.encrypt(p_text)

def decrypt(e_text, key):
    cipher_suite = Fernet(key)
    return cipher_suite.decrypt(e_text)

def encrypt_file(filename, key):
    cipher_suite = Fernet(key)

    p_file = open(filename, "rb")
    p_text = p_file.read()
    p_file.close()

    e_text = cipher_suite.encrypt(p_text)
    e_file = open(filename+".aes", "wb+")
    e_file.write(e_text)
    e_file.close()

def decrypt_file(filename, key):
    cipher_suite = Fernet(key)

    e_file = open(filename+".aes", "rb")
    e_text = e_file.read()
    e_file.close()
    
    d_text = cipher_suite.decrypt(e_text)
    if '/' in filename:
        index = filename.rfind('/')
        format_name = filename[0:index]
        format_name = format_name + "/decrypted_"
        format_name = format_name + filename[index+1:]
        d_file = open(format_name, "wb+")
    else:
        d_file = open("decrypted_"+filename, "wb+")
    d_file.write(d_text)
    d_file.close()

def main():
    key = generate_key()
    encrypt_file("testfiles/COPYLIST.txt",key)
    decrypt_file("testfiles/COPYLIST.txt",key)
    
if __name__ == '__main__':
    main()