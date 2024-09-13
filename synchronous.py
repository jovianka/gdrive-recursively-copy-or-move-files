import time
from pydrive2.auth import GoogleAuth
from pydrive2.drive import GoogleDrive
import os

gauth = GoogleAuth()
gauth.LocalWebserverAuth() # Creates local webserver and auto handles authentication.
drive = GoogleDrive(gauth)
my_email = os.environ['EMAIL_ADDRESS']

def recursive_copy_unowned_files(folder_id, destination_folder_id):
    file_list = drive.ListFile({'q': "'{}' in parents and trashed = false".format(folder_id)}).GetList()
    print('currentfolder: {}'.format(folder_id))
    for file1 in file_list:

        if my_email != file1['owners'][0]['emailAddress']: # if not mine
            duplicate_files = drive.ListFile({'q': "'{}' in parents and title = '{}' and '{}' in owners and trashed = false".format(destination_folder_id, file1['title'], my_email)}).GetList()
            if file1['mimeType'] == 'application/vnd.google-apps.folder': # if folder
                if len(duplicate_files) == 0: # if no duplicates exist
                    new_folder = drive.CreateFile({
                        'title': file1['title'],
                        'parents':  [{'kind': 'drive#parentReference', 'id': destination_folder_id}],
                        'mimeType': 'application/vnd.google-apps.folder'
                    })
                    new_folder.Upload()
                    print('Created folder with title {} and ID {}'.format(new_folder['title'], new_folder['id']))
                    recursive_copy_unowned_files(file1['id'], new_folder['id'])
                else: # if duplicates exist
                    print('Folder with title {} already exists, copying'.format(duplicate_files[0]['title'], duplicate_files[0]['id']))
                    recursive_copy_unowned_files(file1['id'], duplicate_files[0]['id'])
            else: # if file
                if len(duplicate_files) == 0: # if no duplicates exist
                    new_file = file1.Copy(drive.CreateFile({'id': destination_folder_id}), file1['title'])
                    new_file.Upload()
                    print('Copied file with title {}'.format(new_file['title']))
                else: # if duplicates exist
                    print('File with title {} already exists, skipping'.format(duplicate_files[0]['title'], duplicate_files[0]['id']))

        else: # if mine
            if file1['mimeType'] == 'application/vnd.google-apps.folder': # if folder
                recursive_copy_unowned_files(file1['id'], file1['id'])
                file1['parents'] = [{'kind': 'drive#parentReference', 'id': destination_folder_id}]
                file1.Upload()
                print('Moved file with title {}'.format(file1['title']))
            else: # if file
                file1['parents'] = [{'kind': 'drive#parentReference', 'id': destination_folder_id}]
                file1.Upload()
                print('Moved file with title {}'.format(file1['title']))

    return True

start_time = time.time()

source_folder_id = os.environ["SOURCE_FOLDER_ID"]
destination_folder_id = os.environ["DESTINATION_FOLDER_ID"]
recursive_copy_unowned_files(source_folder_id, destination_folder_id)

end_time = time.time()
elapsed_time = end_time - start_time
print(elapsed_time)
