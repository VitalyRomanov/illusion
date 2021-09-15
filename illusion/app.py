import json
import os
import configparser
from enum import Enum
from pathlib import Path
from pprint import pprint
from multiprocessing import Process
from multiprocessing import Queue
from time import sleep


class App:

    class InboxTypes(Enum):
        EXISTING_IMAGES = 1
        ADDED_IMAGES = 2

    class OutboxTypes(Enum):
        GET = 1

    def __init__(self):
        self.set_conf_location()

        if not os.path.isdir(self.conf_dir):
            os.mkdir(self.conf_dir)

        self.set_db_loc()
        self.set_thumbnails_loc()
        self.set_face_thumbnails_loc()

        self.set_config()

        print(f"configfile: {self.conf_file}")
        pprint(self.config)

    def set_conf_location(self):
        self.conf_dir = os.path.join(Path.home(), ".illusion")
        self.conf_file = os.path.join(self.conf_dir, "conf")
        # os.environ["ILLUSION_CONF_DIR"] = self.conf_dir

    def set_config(self):
        config = configparser.ConfigParser()
        if os.path.isfile(self.conf_file):
            config.read(self.conf_file)
        else:
            config['DEFAULT'] = {
                "monitoring_folders": json.dumps([input("Folder for monitoring")]),
                "config_dir": json.dumps(self.conf_dir)
            }
            with open(self.conf_file, 'w') as configfile:
                config.write(configfile)

        config = config['DEFAULT']
        self.config = {key: json.loads(config[key]) for key in config}

    def set_db_loc(self):
        self.db_path = os.path.join(self.conf_dir, "illusion.db")

    def set_face_thumbnails_loc(self):
        self.face_thumbnails_path = os.path.join(self.conf_dir, "face_thumbnails")
        if not os.path.isdir(self.face_thumbnails_path):
            os.mkdir(self.face_thumbnails_path)

    def set_thumbnails_loc(self):
        self.thumbnails_path = os.path.join(self.conf_dir, "thumbnails")
        if not os.path.isdir(self.thumbnails_path):
            os.mkdir(self.thumbnails_path)

    def init_process_manager(self):
        """
        Start image store main loop in a separate process.
        :return:
        """
        self.to_process_manager = Queue()
        self.from_process_manager = Queue()

        from illusion.process_manager import start_process_manager
        self.process_manager_proc = Process(
            target=start_process_manager, args=(
                self.config, self.to_process_manager, self.from_process_manager
            )
        )
        self.process_manager_proc.start()

    def exec(self):
        self.init_process_manager()

        while True:
            while not self.from_process_manager.empty():
                # instead of checking incoming messages in the loop, an event listener should be created
                # look into signals and slots in PyQt
                incoming = self.from_process_manager.get()
                pprint(f"Message type: {incoming.descriptor}, content: {incoming.content}")
            sleep(3) # ??? this needs to be run together with GUI


if __name__ == "__main__":
    app = App()
    app.exec()