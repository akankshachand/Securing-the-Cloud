import os
import pickle 
import threading
import KeySaver 
import DriveManager 
import Encryptor 
from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive
from multiprocessing.connection import Client
from multiprocessing.connection import Listener


class CloudGroup(threading.Thread):
    
    def __init__(self, users, lock, listener, sym_key):
        super(CloudGroup,self).__init__()
        self.users = users
        self.lock = lock
        self.listener = listener
        self.key = sym_key
        self.running = True

    def change_key(self,new_key):
        self.key = new_key

    def close(self):
        self.running = False

    def run(self):
        while True:
            connection = self.listener.accept()
            message = []
            try:
                message = connection.recv()
            except:
                pass
            if len(message)==3:  
                self.lock.acquire()
                if message[0] in self.users:
                    client_address = ('localhost', message[1])
                    response = Client(client_address, authkey=b'secret password')
                    public_key = KeySaver.load_public_key(message[2])
                    encrypted_key = Encryptor.encrypt_symmetric_key(public_key, self.key)
                    response.send(encrypted_key)
                    response.close()
                else:
                    print('Unauthorised access by %s' % (message[0]))
                self.lock.release()
                
            connection.close()

def error_msg():
    print("Enter one of the following commands:\n1. List all users: list\n2. To add a user: add <user>\n3. To remove a user: remove <user>\n4. Exit the program: quit\n")

def reset(key, folder, client_handler, sym_key_filename):
    DriveManager.files_decrypt(key, folder)
    new_key = Encryptor.generate_key()
    with open(sym_key_filename, 'wb') as key_file:
        key_file.write(new_key)
    client_handler.change_key(new_key)
    DriveManager.files_encrypt(new_key, folder)
           
def main():
    groupname = input("Enter the Cloud group name:\n")
    group_path = os.path.join("Groups",groupname)
    if not os.path.isdir(group_path):
        os.mkdir(group_path)
    user_filename = os.path.join(group_path,'UserList')
    try:
        infile = open(user_filename,'rb')
        user_list = pickle.load(infile)
        infile.close()
    except IOError:
        user_list = set()
        users_file = open(user_filename,'wb')
        pickle.dump(user_list,users_file)
        users_file.close()
    sym_key_filename = os.path.join(group_path,'Symmetric_Key.txt')
    try:
        with open(sym_key_filename, 'rb') as key_file:
            sym_key = key_file.read()       
    except:
        sym_key = Encryptor.generate_key()
        with open(sym_key_filename, 'wb') as key_file:
            key_file.write(sym_key)
    gauth = GoogleAuth()
    gauth.LoadCredentialsFile("credentials.txt")
    if gauth.credentials is None or gauth.access_token_expired:
        gauth.LocalWebserverAuth()
    else: 
        gauth.Authorize()
    gauth.SaveCredentialsFile("credentials.txt")
    drive = GoogleDrive(gauth)
    root_folder_id = #insert drive folder ID here
    root_folder = drive.ListFile({'q': "'" + root_folder_id + "' in parents and trashed=false"}).GetList()
    if DriveManager.find_folder(root_folder,groupname) is None:
        folder_id = DriveManager.create_folder(root_folder_id, groupname, drive)
    else:
        folder_id = DriveManager.find_folder(root_folder,groupname)
    folder = drive.ListFile({'q': "'" + folder_id + "' in parents and trashed=false"}).GetList()
    try:
        file_list = open("Drive Folders",'rb')
        drive_folders = pickle.load(file_list)
        file_list.close()
    except IOError:
        print("Could not read drive files:")
        drive_folders = dict()
    drive_folders[groupname] = folder_id
    file_list = open("Drive Folders",'wb')
    pickle.dump(drive_folders,file_list)
    file_list.close()
    address = ('localhost', 6000)
    listener = Listener(address, authkey=b'secret password')
    lock = threading.Lock()
    client_handler = CloudGroup(user_list, lock, listener, sym_key)
    client_handler.daemon = True
    client_handler.start()
    running = True
    print('Manage the group using the following commands:\n1. List all users: list\n2. To add a user: add <user>\n3. To remove a user: remove <user>\n4. Exit the program: quit\n')
    while running:
        command = input('Enter a command\n')
        argv = command.split(' ')
        lock.acquire()
        if argv[0] == 'list':
            print('Users in the group:')
            for x in user_list:
                print(x)
            print()
        elif argv[0] == 'add':
            user_list.add(argv[1])
            print(argv[1],'has been successfully added to the group\n')
        elif argv[0] == 'remove':
            user_list.remove(argv[1])
            reset(sym_key, folder, client_handler, sym_key_filename)
            print(argv[1], 'has been successfully removed from the group\n')
        elif argv[0] == 'quit':
            users = open(user_filename,'wb')
            pickle.dump(user_list,users)
            users.close()
            client_handler.close()
            running = False
            print('Goodbye\n')
        else:
            error_msg()
        lock.release()


if __name__ == '__main__':
    main()
