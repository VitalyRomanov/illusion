import asyncio

from colorama import Fore
from illusion.settings import LOCAL_IMAGE_ROOT


async def apply_fs_changes(conn, added_images, removed_images, changed_images):
    cur = await conn.cursor()
    # await cur.execute('CREATE TABLE IF NOT EXISTS base_image (id INT PRIMARY KEY AUTO_INCREMENT, '
    #                   'path VARCHAR(70), '
    #                   'last_mod_time BIGINT, '
    #                   'is_deleted TINYINT DEFAULT 1);')
    # await conn.commit()
    while True:
        if not added_images.empty():
            print(Fore.GREEN, 'added_images')
        while not added_images.empty():
            img = await added_images.get()
            await cur.execute(f"INSERT INTO base_image (file_path, last_modified_time, is_deleted) "
                              f"VALUES('{str(img.relative_to(LOCAL_IMAGE_ROOT))}',{img.stat().st_mtime_ns}, 0)")
            await conn.commit()
            print(f'Image {img} is inserted')

        if not removed_images.empty():
            print(Fore.GREEN, 'removed_images')
        while not removed_images.empty():
            img = await removed_images.get()
            await cur.execute(f"UPDATE base_image "
                              f"SET is_deleted = 1 "
                              f"WHERE file_path = '{str(img)}';")
            await conn.commit()
            print(f'Image {img} is marked as removed')

        if not changed_images.empty():
            print(Fore.GREEN, 'changed_images')
        while not changed_images.empty():
            print(await changed_images.get())

        print('END OF CYCLe')
        await asyncio.sleep(5)

    await cur.close()
