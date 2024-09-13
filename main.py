import asyncio
import time
import os
import typing
from pydrive2.auth import GoogleAuth
from pydrive2.drive import GoogleDrive
from pydrive2.files import GoogleDriveFile
from pydrive2.files import ApiRequestError
from prettytable import PrettyTable



gauth = GoogleAuth()
gauth.LocalWebserverAuth()
drive = GoogleDrive(gauth)
my_email = os.environ['EMAIL_ADDRESS']



async def copy_or_move_folder(file: GoogleDriveFile, src: str, dest: str) -> dict[str, typing.Any]:
    result = {}
    if my_email != file["owners"][0]["emailAddress"]:  # if not mine
        duplicate_folders = await asyncio.to_thread(
            drive.ListFile,
            {
                "q": f"'{dest}' in parents and title = '{file["title"]}' and '{my_email}' in owners and trashed = false"
            }
        )
        duplicate_folders = await asyncio.to_thread(duplicate_folders.GetList)

        if len(duplicate_folders) == 0:  # if no duplicates exist
            try:
                new_folder = drive.CreateFile(
                    {
                        "title": file["title"],
                        "parents": [
                            {"kind": "drive#parentReference", "id": dest}
                        ],
                        "mimeType": "application/vnd.google-apps.folder",
                    }
                )
                new_folder.Upload()
            except ApiRequestError as err:
                return {
                    "file": file,
                    "status": -1,
                    "status_message": "Failed to copy",
                    "err": err
                }

            children_copy_results = await recursive_copy_foreign_files(file["id"], new_folder["id"])
            result = {
                "file": file,
                "status": 1,
                "status_message": "Copied",
                "task_count": children_copy_results["task_count"],
                "tasks": children_copy_results["tasks"],
                "cancelled_tasks": children_copy_results["cancelled_tasks"]
            }
        else:  # if duplicates exist
            children_copy_results = await recursive_copy_foreign_files(file["id"], duplicate_folders[0]["id"])
            result = {
                "file": file,
                "status": 0,
                "status_message": "Folder already exists",
                "task_count": children_copy_results["task_count"],
                "tasks": children_copy_results["tasks"],
                "cancelled_tasks": children_copy_results["cancelled_tasks"]
            }

    else: # if mine
        children_copy_results = await recursive_copy_foreign_files(file["id"], file["id"])
        try:
            if src != dest:
                file["parents"] = [
                    {"kind": "drive#parentReference", "id": dest}
                ]
                await asyncio.to_thread(file.Upload)
                result = {
                    "file": file,
                    "status": 1,
                    "status_message": "Moved",
                    "task_count": children_copy_results["task_count"],
                    "tasks": children_copy_results["tasks"],
                    "cancelled_tasks": children_copy_results["cancelled_tasks"]
                }
        except ApiRequestError as err:
            return {
                "file": file,
                "status": -1,
                "status_message": "Failed to move",
                "task_count": children_copy_results["task_count"],
                "tasks": children_copy_results["tasks"],
                "cancelled_tasks": children_copy_results["cancelled_tasks"],
                "err": err
            }

    return result



async def copy_or_move_file(file: GoogleDriveFile, src: str = "", dest: str = "") -> dict[str, typing.Any]:
    result = {}
    if my_email != file["owners"][0]["emailAddress"]:  # if not mine
        duplicate_files = await asyncio.to_thread(
            drive.ListFile,
            {
                "q": "'{}' in parents and title = '{}' and '{}' in owners and trashed = false".format(
                    dest, file["title"], my_email
                )
            }
        )

        duplicate_files = await asyncio.to_thread(duplicate_files.GetList)

        if len(duplicate_files) == 0:  # if no duplicates exist
            try:
                await asyncio.to_thread(
                        file.Copy,
                        drive.CreateFile({"id": dest}),
                        file["title"],
                    )
                result = {
                    "file": file,
                    "status": 1,
                    "status_message": "Copied"
                }
            except ApiRequestError as err:
                return {
                    "file": file,
                    "status": -1,
                    "status_message": "Failed to copy",
                    "err": err
                }
        else:  # if duplicates exist
            result = {
                "file": file,
                "status": 0,
                "status_message": "File with the same name exists"
            }

    else: # if mine
        result = {
            "file": file,
            "status": 0,
            "status_message": "Nothing to do"
        }
        if src != dest:
            try:
                file["parents"] = [
                    {"kind": "drive#parentReference", "id": dest}
                ]
                await asyncio.to_thread(file.Upload)
                result = {
                    "file": file,
                    "status": 1,
                    "status_message": "Moved"
                }
            except ApiRequestError as err:
                return {
                    "file": file,
                    "status": -1,
                    "status_message": "Failed to move",
                    "err": err
                }

    return result



async def copy_or_move_shortcut_target(file: GoogleDriveFile, src: str = "", dest: str = ""):
    await asyncio.to_thread(file.FetchMetadata, "shortcutDetails")
    file_to_be_copied = drive.CreateFile({"id": file["shortcutDetails"]["targetId"]})
    match file["shortcutDetails"]["targetMimeType"]:
        case "application/vnd.google-apps.folder":
            return await copy_or_move_folder(file_to_be_copied, file_to_be_copied["id"], dest)

        case "application/vnd.google-apps.shortcut":
            if len(file_to_be_copied["parents"]) > 0:
                return await copy_or_move_shortcut_target(file_to_be_copied, file_to_be_copied["parents"][0]["id"], dest)
            else:
                return await copy_or_move_shortcut_target(file_to_be_copied, "", dest)

        case _:
            if len(file_to_be_copied["parents"]) > 0:
                return await copy_or_move_file(file_to_be_copied, file_to_be_copied["parents"][0]["id"], dest)
            else:
                return await copy_or_move_file(file_to_be_copied, "", dest)



async def recursive_copy_foreign_files(src: str, dest: str) -> dict[str, typing.Any]:
    tasks = []
    file_list = drive.ListFile(
        {"q": "'{}' in parents and trashed = false".format(src)}
    ).GetList()

    for file in file_list:
        match file["mimeType"]:
            case "application/vnd.google-apps.folder":
                task = asyncio.create_task(copy_or_move_folder(file, src, dest))
                tasks.append(task)

            case "application/vnd.google-apps.shortcut":
                task = asyncio.create_task(copy_or_move_shortcut_target(file, src, dest))
                tasks.append(task)

            case _:
                task = asyncio.create_task(copy_or_move_file(file, src, dest))
                tasks.append(task)
    
    done, pending = await asyncio.wait(tasks, return_when=asyncio.ALL_COMPLETED)
    results = [task.result() for task in done]

    cancelled_tasks = []
    task_count = len(tasks)
    all_results = results

    for result in results:
        if result["status"] == -1:
            cancelled_tasks.append(result)
        if result["file"]["mimeType"] == "application/vnd.google-apps.folder":
            all_results.extend(result["tasks"])
            cancelled_tasks.extend(result["cancelled_tasks"]) 
            task_count += result["task_count"]

    return {
        "task_count": task_count,
        "tasks": all_results,
        "cancelled_tasks": cancelled_tasks,
    }

async def main():
    src = os.environ["SOURCE_FOLDER_ID"]
    dest = os.environ["DESTINATION_FOLDER_ID"]
    result = await recursive_copy_foreign_files(src, dest)

    file_list = [
        [
            x["file"]["title"],
            x["file"]["mimeType"],
            x["file"]["owners"][0]["emailAddress"],
            x["status_message"],
            x["file"]["parents"][0]["id"]
        ] if len(x["file"]["parents"]) > 0
        else [
            x["file"]["title"],
            x["file"]["mimeType"],
            x["file"]["owners"][0]["emailAddress"],
            x["status_message"],
            "No parent (orphaned)"
        ]
        for x in result["tasks"]
    ]

    table = PrettyTable()
    table.field_names = ["Title", "Type", "Owner", "Status", "Parent"]
    table.add_rows(file_list)
    table.align = "l"

    print(table)
    print(f"Failed/Total: {len(result['cancelled_tasks'])}/{len(result['tasks'])}")

    with open(f"results/{src}.txt", 'w') as w:
        w.write(table.get_string())
        w.write(f"\nFailed/Total: {len(result['cancelled_tasks'])}/{len(result['tasks'])}")

start_time = time.time()
# logging.basicConfig(level=logging.DEBUG)

asyncio.run(main())

end_time = time.time()
elapsed_time = end_time - start_time
print(f"Elapsed time: {elapsed_time}")
