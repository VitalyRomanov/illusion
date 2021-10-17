from pathlib import Path
from pprint import pprint
from multiprocessing import Process
from multiprocessing import Queue
from time import sleep

from illusion.app_config import AppConfig
from illusion.process_manager import ProcessManager
from illusion.protocol import start_worker, Message


class App:
    conf_dir = None
    conf_file = None
    config = None
    to_process_manager = None
    from_process_manager = None
    process_manager_proc = None

    def __init__(self):
        self._set_conf_location()
        self._set_config()

        print(f"configfile: {self.conf_file}")
        pprint(self.config)

    def _set_conf_location(self):
        self.conf_dir = Path.home().joinpath(".illusion")
        self.conf_file = self.conf_dir.joinpath("conf")

    def _set_config(self):
        # config = configparser.ConfigParser()
        self.config = self._read_config() if self.conf_file.is_file() else self._init_config()
        # if self.conf_file.is_file():
        #     config = self._read_config(config)
        # else:
        #     config = self._init_config(config)
        #
        # self.config = config
        
    def _read_config(self):
        config = AppConfig.read_config(self.conf_file)
        return config
        # config_object.read(self.conf_file)
        # config = config_object["DEFAULT"]
        # return {key: json.loads(config[key]) for key in config}
    
    def _init_config(self):
        if not self.conf_dir.is_dir():
            self.conf_dir.mkdir()

        config = AppConfig(
            monitoring_folders=[Path(input("Folder for monitoring"))],
            config_dir=self.conf_dir,
            db_loc=self._get_db_loc(),
            thumbnails_loc=self._get_thumbnails_loc(),
            face_thumbnails_loc=self._get_face_thumbnails_loc(),
            crawler_scan_interval=60,
            face_extractor_model=self.get_face_extractor_model_loc()
        )
        config.write_config(self.conf_file)

        # config_dict = {
        #     "monitoring_folders": [input("Folder for monitoring")],
        #     "config_dir": self.conf_dir,
        #     "db_loc": self._get_db_loc(),
        #     "thumbnails_loc": self._get_thumbnails_loc(),
        #     "face_thumbnails_loc": self._get_face_thumbnails_loc(),
        #     "crawler_scan_interval": 60,
        #     "face_extractor_model": self.get_face_extractor_model_loc()
        # }
        #
        # config_object['DEFAULT'] = {key: json.dumps(val) for key, val in config_dict.items()}
        # with open(self.conf_file, 'w') as configfile:
        #     config_object.write(configfile)

        return config
        
    def _get_db_loc(self):
        return self.conf_dir.joinpath("illusion.db")

    def _get_face_thumbnails_loc(self):
        face_thumbnails_path = self.conf_dir.joinpath("face_thumbnails")
        if not face_thumbnails_path.is_dir():
            face_thumbnails_path.mkdir()

        return face_thumbnails_path

    def _get_thumbnails_loc(self):
        thumbnails_path = self.conf_dir.joinpath("thumbnails")
        if not thumbnails_path.is_dir():
            thumbnails_path.mkdir()

        return thumbnails_path

    def get_face_extractor_model_loc(self):
        return self.conf_dir.joinpath("haarcascade_frontalface_default.xml")

    def _init_process_manager(self):
        """
        Start image store main loop in a separate process.
        :return:
        """
        self.to_process_manager = Queue()
        self.from_process_manager = Queue()

        self.process_manager_proc = Process(
            target=start_worker, args=(
                ProcessManager, self.config, self.to_process_manager, self.from_process_manager
            )
        )
        self.process_manager_proc.start()

        self.to_process_manager.put(
            Message(ProcessManager.InboxTypes.GET_EXISTING_IMAGES, content=None)
        )

    def exec(self):
        self._init_process_manager()

        while True:
            while not self.from_process_manager.empty():
                # instead of checking incoming messages in the loop, an event listener should be created
                # look into signals and slots in PyQt
                incoming = self.from_process_manager.get()
                pprint(f"Message type: {incoming.descriptor}, content: {incoming.content}")
            sleep(3)  # ??? this needs to be run together with GUI


if __name__ == "__main__":
    app = App()
    app.exec()
