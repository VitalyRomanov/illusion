import configparser
import json
from pathlib import Path
from typing import List


class AppConfig:
    def __init__(
            self, monitoring_folders: List[Path], config_dir: Path, db_loc: Path, thumbnails_loc: Path,
            face_thumbnails_loc: Path, crawler_scan_interval: int, face_extractor_model: Path
    ):
        self.monitoring_folders = monitoring_folders
        self.config_dir = config_dir
        self.db_loc = db_loc
        self.thumbnails_loc = thumbnails_loc
        self.face_thumbnails_loc = face_thumbnails_loc
        self.crawler_scan_interval = crawler_scan_interval
        self.face_extractor_model = face_extractor_model

    def write_config(self, config_file_path):
        configp = configparser.ConfigParser()

        config_dict = self.__dict__
        config_dict["monitoring_folders"] = [str(dir) for dir in config_dict["monitoring_folders"]]
        config_dict["monitoring_folders"] = json.dumps(config_dict["monitoring_folders"])
        for key in ["config_dir", "db_loc", "thumbnails_loc", "face_thumbnails_loc", "face_extractor_model"]:
            config_dict[key] = str(config_dict[key])

        configp['DEFAULT'] = config_dict
        with open(config_file_path, 'w') as configfile:
            configp.write(configfile)

    @classmethod
    def read_config(cls, config_file_path):
        configp = configparser.ConfigParser()
        configp.read(config_file_path)
        config_dict = {key: configp["DEFAULT"][key] for key in configp["DEFAULT"]}

        config_dict["monitoring_folders"] = json.loads(config_dict["monitoring_folders"])
        config_dict["monitoring_folders"] = [Path(dir_) for dir_ in config_dict["monitoring_folders"]]
        for key in ["config_dir", "db_loc", "thumbnails_loc", "face_thumbnails_loc", "face_extractor_model"]:
            config_dict[key] = Path(config_dict[key])
        config_dict["crawler_scan_interval"] = int(config_dict["crawler_scan_interval"])

        return cls(
            monitoring_folders=config_dict["monitoring_folders"],
            config_dir=config_dict["config_dir"],
            db_loc=config_dict["db_loc"],
            thumbnails_loc=config_dict["thumbnails_loc"],
            face_thumbnails_loc=config_dict["face_thumbnails_loc"],
            crawler_scan_interval=config_dict["crawler_scan_interval"],
            face_extractor_model=config_dict["face_extractor_model"]
        )

    def __repr__(self):
        return repr(self.__dict__)
