import os
import sys
import pickle
import random 
import Encryptor
import KeySaver 
from multiprocessing.connection import Client
from multiprocessing.connection import Listener
from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive

folder_Id = '1pyu7scndXKk-hFBYs_dNrHxOP1NeA5rp'

def retrieve_asymmetrical_key(username, address, port, group_address, group_listener, user_key):
    skey = KeySaver.serialize_key(user_key)
    connection = Client(address, authkey=b'secret password')
    connection.send([username, port, skey])
    connection.close()
    group_connection = group_listener.accept()
    sekey = b"error"
    try:
        sekey = group_connection.recv()
    except:
        pass
    group_connection.close()
    return KeySaver.generate_symmetric_key(user_key, sekey)

def retrieve_file(symmetric_key, filename, drive, folder_id):
    file_list = drive.ListFile({'q': "'" + folder_id + "' in parents and trashed=false"}).GetList()
    for file in file_list:
        if file["title"] == filename:
            etext = file.GetContentString()    
            dtext = Encryptor.decrypt(etext.encode(), symmetric_key,)
            with open (os.path.join("downloads",filename),'wb') as d_file:
                d_file.write(dtext)
                d_file.close()

def upload_file(symmetric_key, filename, drive, folder_id):
    u_file = drive.CreateFile({"parents": [{"kind": "drive#fileLink", "id": folder_id}],'title':filename})
    with open (os.path.join("testfiles",filename),'rb') as uploadfile:
        plain_text = uploadfile.read()
        etext = Encryptor.encrypt(plain_text, symmetric_key)
        u_file.SetContentString(etext.decode())
        uploadfile.close()
    u_file.Upload()

def error_msg():
    print("Enter one of the following commands:\n1. Upload a file: upload <filename>\n2. Download a file: download <filename>\n3. Exit the program: quit\n'")

def print_fileList(drive):
    file_list = drive.ListFile({'q': "'//drive folder id' in parents and trashed=false"}).GetList()
    for file in file_list:
        print('title: %s, id: %s' % (file['title'], file['id']))
    
def main():
    username = input("Enter username?\n")
    group = input("Enter Group?\n")
    try:
        user_key = KeySaver.load_key(username)
    except:
        user_key = Encryptor.generate_private_key()
        KeySaver.save_key(username, user_key)
        
    gauth = GoogleAuth()
    gauth.LoadCredentialsFile("credentials.txt")
    
    if gauth.credentials is None or gauth.access_token_expired:
        gauth.LocalWebserverAuth()
    else: 
        gauth.Authorize()
        
    gauth.SaveCredentialsFile("credentials.txt")
    drive = GoogleDrive(gauth)
    address = ('localhost', 6000)
    port = random.randint(6001,7000)
    group_address = ('localhost', port)
    group_listener = Listener(group_address, authkey=b'secret password')
    file_list = open("Drive Folders",'rb')
    drive_folders = pickle.load(file_list)
    file_list.close()
    folder_id = drive_folders[group]
    symkey = retrieve_asymmetrical_key(username, address, port, group_address, group_listener, user_key)
    running = True
    print('To manage the files use the following commands:\n1. Upload a file: upload <filename>\n2. Download a file: download <filename>\n3. Exit the program: quit\n')
    while running:     
        inputs = input('Enter a command\n')
        symkey = retrieve_asymmetrical_key(username, address, port, group_address, group_listener, user_key)
        argv = inputs.split(' ')
        if len(argv)>2:
            print("Usage: python ex.py ")
            sys.exit(1)
        else:
            command = argv[0]
            if command == "upload":
                filename = argv[1]
                upload_file(symkey, filename, drive, folder_id)
                print(argv[1],"has been successfully uploaded on the cloud.\n")
            elif command == "download":
                filename = argv[1]
                retrieve_file(symkey, filename, drive, folder_id)
                print(argv[1], "has been successfully downloaded from the cloud.\n")
            elif command == "quit":
                running = False 
                print("Goodbye\n")
            else:
                error_msg()
    
if __name__ == '__main__':
    main()