"""Label definitions and mappings for IEA statistics"""
import typing as tp
from pathlib import Path

from ..labelfiles import LabelfileManager
from ..labelfiles import LabelMap


_filemanager: LabelfileManager = LabelfileManager(
    yamlfiles_root=Path(__file__).parent,
    yamlfiles={
        'CO2_bigco2': Path('CO2_bigco2_labels.yaml')
        # 'WEB_wbal': Path('WEB_wbal_labels.yaml')
    }
)

yamlfiles: tp.Dict[str, Path] = _filemanager.yamlfiles
labelsets: tp.Dict[str, tp.List[str]] = _filemanager.labelsets
get_label_map: tp.Callable[[str, str], LabelMap] = _filemanager.get_label_map
