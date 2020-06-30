import Encryptor
from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive

def create_folder(parent_folderid, folder_name, drive):
    file = drive.CreateFile({'title': folder_name, "parents":  [{"kind":"drive#fileLink", "id": parent_folderid}], "mimeType": "application/vnd.google-apps.folder"})
    file.Upload()
    return file["id"]

def find_folder(folder, folder_name):
    for file in folder:
        if file["title"] == folder_name:
            return file["id"]
    return None

def files_encrypt(key, folder):
    for file in folder:
        p_text = file.GetContentString()
        e_text = Encryptor.encrypt(p_text.encode(), key)
        file.SetContentString(e_text.decode())
        file.Upload()
            
def files_decrypt(key, folder):
    for file in folder:
        find_folder(folder, file['title'])
        e_text = file.GetContentString()    
        d_text = Encryptor.decrypt(e_text.encode(), key)
        file.SetContentString(d_text.decode())
        file.Upload()

def files_list(folder):
    for file in folder:
        print('title: %s, id: %s' % (file['title'], file['id']))

def files_delete(folder):
    for file in folder:
        print('Deleting file... title: %s, id: %s' % (file['title'], file['id']))
        file.Delete()
    
def main():
    gauth = GoogleAuth()
    gauth.LoadCredentialsFile("credentials.txt")
    
    if gauth.credentials is None or gauth.access_token_expired:
        gauth.LocalWebserverAuth() 
        
    else: 
        gauth.Authorize()
        
    gauth.SaveCredentialsFile("credentials.txt")

    drive = GoogleDrive(gauth)
    
    key = Encryptor.generate_key()
    folder = drive.ListFile({'q': "'//drive folder id' in parents and trashed=false"}).GetList()

    files_encrypt(key, folder)
    files_decrypt(key, folder)
    files_list(folder)
    files_delete(folder)
    
if __name__ == '__main__':
    main()