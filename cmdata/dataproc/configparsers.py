"""Custom `configparser.ConfigParser` subclasses / functionality.

Classes
-------
ConfigParserListMixin(configparser.ConfigParser)
    A subclass of `configparser.ConfigParser` that provides a method `getlist`
    to read list-valued config file options. The default behavior is to expect
    list items to be separated by newlines and each item to be indented, but
    the class allows for specifying a different separator than newlines.

PathConfigParser(ConfigParserListMixin)
    Provides functionality for reading path-valued config file options,
    including setting a root for resolving relative paths. Also includes the
    functionality from `ConfigParserListMixin`.
"""
from __future__ import annotations

import typing as tp
from pathlib import Path
import configparser


class ConfigParserListMixin(configparser.ConfigParser):
    """Mixin for ConfigParsers with a method for reading list-valued options.
    
    Class attributes
    ----------
    DEFAULT_LIST_SEPARATOR : str
        Default list separator. Defaults to '\n', i.e., that each item in
        a list should be on a separate line. This typically means that lists
        in configuration files should be of the form:

        [Section name]
        list_name =
            item value 1
            item value 2
            item value 3
            ...

    Properties
    ----------
    list_separator : str
        Character(s) used as list separators. If not set explicitly or through
        the `__init__` method, it will be set to `DEFAULT_LIST_SEPARATOR` the
        first time it is accessed, either directly or through the `getlist`
        method.
    """

    DEFAULT_LIST_SEPARATOR: str = '\n'

    _DEFAULT_STRIP_ITEMS: bool = True

    def __init__(
        self,
        list_separator: str = None,
        strip_items: bool = None,
        **kwargs
    ):
        """
        Parameters
        ----------
        list_separator : str, optional
            Character or combination of characters to use as list separator.
            Optional, will use `DEFAULT_LIST_SEPARATOR` if not specified.
        strip_items : bool, optional
            Whether to strip leading and trailing white space from lists. Note
            that if this is not set to True, you can easily end up with empty
            leading items if `list_separator` is `'\n'`, for example if there
            is a newline directly after the option name and equal sign or
            colon. Optional, True by default.
        **kwargs
            Additional keyword arguments to pass to the superclass `__init__`.
        """
        super().__init__(**kwargs)
        if list_separator is not None:
            self.list_separator = list_separator
        if strip_items is not None:
            self.strip_items = strip_items
    ###END def ConfigParserListMixin.__init__

    @property
    def list_separator(self) -> str:
        try:
            return self.__list_separator
        except NameError:
            self.__list_separator: str = self.DEFAULT_LIST_SEPARATOR
        return self.__list_separator
    ###END def property ConfgParserListMixin.list_separator

    @list_separator.setter
    def list_separator(self, listsep: str):
        if not isinstance(listsep, str):
            raise TypeError(
                '`list_separator` must be a string instance.'
            )
        self.__list_separator: str = listsep
    ###END def list_separator.setter ConfigParserListMixin.list_separator

    @property
    def strip_items(self) -> bool:
        try:
            return self.__strip_items
        except NameError:
            self.__strip_items: bool = self._DEFAULT_STRIP_ITEMS
        return self.__strip_items
    ###END def property ConfgParserListMixin.strip_items

    @strip_items.setter
    def strip_items(self, strip_items: bool):
        if not isinstance(strip_items, bool):
            raise TypeError(
                '`strip_items` must be a bool instance.'
            )
        self.__strip_items: bool = strip_items
    ###END def strip_items.setter ConfigParserListMixin.strip_items

    def getlist(
        self,
        section: str,
        option: str,
        list_separator: str = None,
        strip_items: bool = None,
        item_type: type = str,
        **kwargs
    ) -> tp.List[tp.Any]:
        """Returns a list-valued option as a list.
        
        Parameters
        ----------
        section : str
            As in standard `ConfigParser.get` method
        option : str
            As in standard `ConfigParser.get` method
        list_separator : str, optional
            List separator to use. Will be passed to `str.split` to split the
            option value. Optional, `self.list_separator` by defaults.
        strip_items : bool, optional
            Whether to strip whitespace from the list as a whole and to each
            item after splitting (using `str.strip`). Optional,
            `self.strip_items` by default.
        item_type : type, optional
            What type to return the items as. Note that the type conversion
            will be made by feeding each item_value to `item_type` as a
            function. This must be supported by the `item_type` `__init__`
            method (i.e., the `__init__` method must take a single str value
            as an argument and convert it to the appropriate type). Optional,
            `str` by default.
        **kwargs
            Additional keyword arguments to pass to `ConfigParser.get`.

        Returns
        -------
        list
            List with items of the type specified by `item_type`.
        """
        if list_separator is None:
            list_separator = self.list_separator
        if strip_items is None:
            strip_items = self.strip_items
        _value: str = self.get(
            section=section,
            option=option,
            **kwargs
        )
        if strip_items:
            _value = _value.strip()
        _valuelist: tp.List[str] = _value.split(list_separator)
        if strip_items:
            _valuelist = [_s.strip() for _s in _valuelist]
        if item_type != str:
            return [item_type(_item) for _item in _valuelist]
        else:
            return _valuelist
    ###END def ConfigParserListMixin.getlist

###END class ConfigParserListMixin


class PathConfigParser(ConfigParserListMixin):
    """ConfigParser with functionality for a default root path."""

    _DEFAULT_ROOT_PATH_OPTION: str = 'root_path'

    def __init__(
        self,
        root_path_option_name: tp.Optional[str] = None,
        root_path: tp.Optional[Path] = None,
        **kwargs
    ):
        """
        Parameters
        ----------
        root_path_option_name : str, optional
            Option name used for the default root path. Optional, uses the class
            attribute `_DEFAULT_ROOT_PATH_OPTION` by default.
        root_path : Path
            Default root path (as a Path instance) to set on the instance.
            Optional, defaults to `None`. If set, it will override any value
            that might be set in the default section of configuration files that
            are later read. If not set, the instance will first try to read it
            from the default setion of any file that is read, with the `read`
            method. If not present in the configuration file, the directory that
            contains the file will be used.
        **kwargs, optional
            Remaining keyword arguments, which will be passed to
            `configparser.ConfigParser.__init__`.
        """
        super().__init__(**kwargs)
        if root_path_option_name is None:
            self.root_path_option_name: str = self._DEFAULT_ROOT_PATH_OPTION
        else:
            self.root_path_option_name: str = root_path_option_name
        if root_path is not None:
            self.root_path: Path = root_path
    ###END def PathConfigParser.__init__

    def read(
        self,
        filenames: tp.Union[str, Path],
        encoding: tp.Optional[str] = None
    ) -> tp.List[str]:
        """Overriding `read` method, with functionality for setting root_path.
        
        The method functions like the superclass `read` method for a single
        file, but sets the default root path if not contained in the file
        and not already set in the `__init__` method.

        Parameters
        ----------
        filenames : Path or str
            Filename or Path instance of the file to read. Unlike the
            superclass `read` method, reading a list of files is *not*
            supported.
        encoding : str, optional
            File encoding, passed to the superclass `read` method.

        Returns
        -------
        list of str (single-element list)
            Returns the name of the file that was read, as a single-element
            list, to retain compatibility with the superclass `read` method.
        """
        # Back up self.root_path in case it is set in the file
        _root_path_backup: Path = self.root_path
        if not (isinstance(filenames, str) or isinstance(filenames, Path)):
            raise TypeError(
                '`filenames` must be a single string or a Path instance.'
            )
        super().read(filenames=filenames, encoding=encoding)
        if _root_path_backup is not None \
                and _root_path_backup != self.root_path:
            self.root_path = _root_path_backup
        if self.root_path is None:
            self.root_path = Path(filenames).parent.absolute().resolve()
        return [str(filenames)]
    ###END def PathConfigParser.read

    @property
    def root_path(self) -> Path:
        _path: tp.Optional[Path] = self.get(
            section=self.default_section,
            option=self.root_path_option_name,
            fallback=None
        )
        if _path is None:
            return _path
        else:
            return Path(_path)
    ###END def property PathConfigParser.root_path

    @root_path.setter
    def root_path(self, _path: Path):
        if not (isinstance(_path, str) or isinstance(_path, Path)):
            raise TypeError(
                '`root_path` only supports string and Path values.'
            )
        self.set(
            section=self.default_section,
            option=self.root_path_option_name,
            value=str(_path)
        )
    ###END def property.setter PathConfigParser.set_root_path

    def get_path(
        self,
        section: str,
        option: str,
        return_absolute: bool = True,
        root_path: Path = None,
        **kwargs
    ) -> Path:
        """Get an option as a Path instance, optionally relative to root path.
        
        Parameters
        ----------
        section : str
            Section name to get
        option : str
            Option name to get
        return_absolute : bool, optional
            Whether to return an absolute path. If the option is a relative
            path, it will be assumed to be relative to `root_path`. If it
            is already absolute, this option has no effect. Optional, defaults
            to True.
        root_path : Path, optional
            The root path that relative paths will be resolved relative to.
            Only used if `return_absolute` is True, and the path in question
            is not already absolute. Optional, `self.root_path` by default.
        **kwargs
            Additional keyword arguments to pass to superclass `get` method
            (including, e.g., `fallback` or `raw`).

        Returns
        -------
        Path
            The option interpreted as a path, as a `pathlib.Path` instance.

        Raises
        ------
        PathError
            If the option cannot be converted to a Path object.
        """
        if root_path is None:
            root_path = self.root_path
        _path: Path = Path(
            self.get(
                section=section,
                option=option,
                **kwargs
            )
        )
        if return_absolute and not _path.is_absolute():
            _path = (root_path / _path).absolute().resolve()
        return _path
    ###END def PathConfigParser.get_path

###END class PathConfigParser
