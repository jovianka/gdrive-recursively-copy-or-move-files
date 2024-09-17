# Installation
1. Clone the repo
   ```sh
   git clone https://github.com/jovianka/gdrive-recursively-copy-or-move-files.git && cd gdrive-recursively-copy-or-move-files
   ```

2. Make a python virtual environment
Linux/MacOS:
   ```sh
   python -m venv ./venv
   source ./venv/bin/activate
   ```
   
   Windows:
   ```sh
   python -m venv .\venv
   .\venv\bin\activate.bat
   ```

   To get out of the virtual environment, call
   ```sh
   deactivate
   ```
   or
   ```sh
   deactivate.bat
   ```

4. Install package requirements
   ```sh
   pip install -r requirements.txt
   ```



# Usage
1. Since this script uses pydrive2, follow the steps on [their docs](https://docs.iterative.ai/PyDrive2/quickstart/) to setup your OAuth2 authentication.
2. Setup environment variables
   - SOURCE_FOLDER_ID -> The **content** of this folder will be moved/copied to DESTINATION_FOLDER_ID
   - DESTINATION_FOLDER_ID
   - EMAIL_ADDRESS -> Email that own/will own the files being moved/copied 
3. Run `python main.py`



# Things to Note
- The [revisions](https://developers.google.com/drive/api/guides/change-overview) of copied files will not be copied.
- Copied files will be left untouched, but moved files (which are owned by EMAIL_ADDRESS) will only be present in the directory owned by EMAIL_ADDRESS after the script completes.
- You can get a folder's ID from the folder's link e.g. https://drive.google.com/drive/folders/id
- Copied files will be checked for duplicates.
- API requests will be sent asynchronously using [asyncio](https://docs.python.org/3/library/asyncio.html)
- **Might not work** for files in [shared drives](https://support.google.com/a/users/answer/7212025?hl=en)



# Useful Resources
- https://docs.iterative.ai/PyDrive2/
- https://docs.python.org/3/library/asyncio-task.html 
- https://developers.google.com/drive/api/guides/v2-to-v3-reference
