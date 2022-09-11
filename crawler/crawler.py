import asyncio
from pathlib import PosixPath

import aiomysql

from change_detector import get_fs_changes
from change_populator import apply_fs_changes
from crawler_settings import CrawlerSettings

added_images = asyncio.Queue()
removed_images = asyncio.Queue()
changed_images = asyncio.Queue()


async def get_running_tasks():
    conn = await aiomysql.connect(host='127.0.0.1', port=3306,
                                  user='root', password='newpassword',
                                  db='illusion')
    tasks = await asyncio.gather(
        get_fs_changes(added_images, removed_images, changed_images),
        apply_fs_changes(conn, added_images, removed_images, changed_images)
    )
    conn.close()
    return tasks


def main():
    # loop: AbstractEventLoop = asyncio.new_event_loop()
    # loop.run_until_complete(get_running_tasks)
    # asyncio.set_event_loop(loop)
    asyncio.run(get_running_tasks())


if __name__ == '__main__':
    settings = CrawlerSettings.load()
    main()
