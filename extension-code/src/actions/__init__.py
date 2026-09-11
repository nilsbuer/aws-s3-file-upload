"""Actions module - Business logic implementations."""

from actions.output import ActionOutput
from actions.list_files import ListFiles
from actions.upload_file import UploadFile
from manager import ExtensionManager

extension_manager = ExtensionManager()

ACTION_MAPPER = {
    "List Files": lambda input_data: ListFiles(input_data).execute(),
    "Upload File": lambda input_data: UploadFile(input_data).execute(),
}
