import json
import logging
import os
import configparser
from pathlib import Path
from pprint import pprint
from multiprocessing import Process
from multiprocessing import Queue
from time import sleep


class App:
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
        os.environ["ILLUSION_CONF"] = self.conf_dir

    def set_config(self):
        config = configparser.ConfigParser()
        if os.path.isfile(self.conf_file):
            config.read(self.conf_file)
        else:
            config['DEFAULT'] = {
                "monitoring_folders": json.dumps([input("Folder for monitoring")])
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

    def init_image_store(self):
        from illusion.DbPopulator import image_store_main_loop
        self.image_store_outbox = Queue()
        self.image_store_inbox = Queue()
        self.image_store_proc = Process(
            target=image_store_main_loop, args=(
                self.config["monitoring_folders"], self.image_store_outbox, self.image_store_inbox
            )
        )
        self.image_store_proc.start()

    def exec(self):
        # from illusion.DbPopulator import main_test
        # main_test()
        # start ¡¡¡DB POPULATOR!!!
        self.init_image_store()

        while True:
            while not self.image_store_inbox.empty():
                incoming = self.image_store_inbox.get()
                logging.info(f"Received message {incoming['message']}")
                print(incoming)
            sleep(3)


if __name__ == "__main__":
    app = App()
    app.exec()