from lib.FileManager.workers.baseWorkerCustomer import BaseWorkerCustomer
from lib.FileManager.WebDavConnection import WebDavConnection
from config.main import TMP_DIR
import traceback
import os


class ReadImages(BaseWorkerCustomer):
    def __init__(self, paths, session, *args, **kwargs):
        super(ReadImages, self).__init__(*args, **kwargs)

        self.paths = paths
        self.session = session
        self.webdav = WebDavConnection.create(self.login, self.session.get('server_id'), self.logger)

    def run(self):
        try:
            self.preload()
            self.logger.info("WebDav ReadImages process run")

            hash_str = self.random_hash()
            download_dir = TMP_DIR + '/images/' + self.login + '/' + hash_str + '/'
            success_paths, error_paths = self.copy_files_to_tmp(download_dir)

            if len(success_paths) == 1:
                one_file = True
            else:
                one_file = False

            if len(error_paths) == 0:  # Значит все хорошо, можно дальше обрабатывать

                file_list = {
                    "succeed": list(os.path.basename(filename) for filename in success_paths),
                    "failed": list(os.path.basename(filename) for filename in error_paths)
                }

                answer = {
                    "success": True,
                    "file_list": file_list,
                    "hash": hash_str,
                    "one_file": one_file,
                    "sid": self.login
                }

                result = {
                    "data": answer
                }

                self.on_success(result)
            else:
                raise Exception("read error")

        except Exception as e:
            result = {
                "error": True,
                "message": str(e),
                "traceback": traceback.format_exc()
            }

            self.on_error(result)

    def copy_files_to_tmp(self, target_path):
        if not os.path.exists(target_path):
            os.makedirs(target_path)

        success_paths = []
        error_paths = []

        for path in self.paths:
            try:
                abs_path = self.webdav.path(path)

                if self.webdav.isfile(abs_path):
                    self.download_file_from_webdav(abs_path, target_path)

                success_paths.append(path)

            except Exception as e:
                self.logger.error(
                        "Error copy %s , error %s , %s" % (str(path), str(e), traceback.format_exc()))
                error_paths.append(path)

        return success_paths, error_paths

    def download_file_from_webdav(self, abs_path, target_path):
        try:
            download_result = self.webdav.download(abs_path, target_path)
            if not download_result['success'] or len(download_result['file_list']['failed']) > 0:
                raise download_result['error'] if download_result['error'] is not None else Exception("Download error")
        except Exception as e:
            self.logger.info("Cannot copy file %s , %s" % (abs_path, str(e)))
            raise e

