from collections import OrderedDict
import importlib
import os
from typing import Any, Dict, Optional, Tuple, Union  # noqa
import urllib.parse

import yaml

ConfigValue = Union[str, bool, Dict[str, Any]]
ConfigStore = Dict[str, ConfigValue]

immutable_config_values = None  # type: Optional[ConfigStore]


def opts2env(opts: Dict[str, str], prefix: str) -> None:
    """ Takes opts produced by docopt and puts then in Environment variables
    with the given case-insensitive prefix. `__name__` might make a good
    prefix.

    >>> opts2env({'--monty': 'spam', '<WITCH>': True, 'duck': False, 'a': 'b'},
    ...          'ctest')
    >>> os.environ['CTEST_MONTY']
    'spam'
    >>> os.environ['CTEST_WITCH']
    '1'
    >>> os.environ.get('CTEST_DUCK', 'missing')
    'missing'
    >>> os.environ['CTEST_A']
    'b'
    """
    prefix = prefix.upper()
    for k, v in opts.items():
        name = prefix + "_" + k.upper().strip("-<> ").replace("-", "_")
        if v is not False and v is not None:
            os.environ[name] = "1" if v is True else str(v)


def load_from_env(prefix: str) -> ConfigStore:
    """ Returns a dict of environment variables with the given case-insensitive
    prefix.

    >>> os.environ['CTEST_FOO'] = '0'
    >>> os.environ['CTEST_BAR'] = 'hello'
    >>> conf = load_from_env('CtEsT')
    >>> conf['FOO']
    False
    >>> conf['BAR']
    'hello'
    """
    prefix = prefix.upper()
    config = {}  # type: ConfigStore
    k = ""  # type: str
    v = ""  # type: ConfigValue
    for k, v in os.environ.items():
        if not k.startswith(prefix + "_"):
            continue
        if type(v) is str:
            # Make falsey things actually False.
            v = False if str(v).lower() in ["0", "false", "no"] else v
        config[k.replace(prefix + "_", "")] = v
    return config


def load(opts: Dict[str, str], prefix: str, fname=None) -> ConfigStore:
    """
    CLI options overrule Config File Options which overrule Env vars.
    
    Prefix is not case-sensitive. We support the conventions that
    Enviroment Variables are typically UPPER_CASE and CLI arguments
    are typically --lower-case.
    
    >>> o = {} 
    >>> o['--foo'] = '0'
    >>> o['--bar'] = 'hello'
    >>> conf = load(o, 'CteSt')
    >>> conf['FOO']
    False
    >>> conf['BAR']
    'hello'
    >>> os.environ['CTEST_BAR']
    'hello'
    """
    global immutable_config_values
    if immutable_config_values is not None:
        raise Exception("load() function should only be called once.")
    conf = {k.upper(): v for k, v in parse_config_file(fname).items()} if fname else {}
    str_conf = {k: v for k, v in conf.items() if type(v) is str}
    str_conf.update(opts)
    opts2env(str_conf, prefix)
    conf.update(load_from_env(prefix))
    immutable_config_values = OrderedDict(conf)
    return conf


def parse_config_file(fname: str) -> Dict[str, Any]:
    with open(fname, "r") as doc:
        return yaml.full_load(doc)


def get(key=None, default=None) -> Union[ConfigStore, ConfigValue]:
    if immutable_config_values is None:
        raise Exception("Config not yet loaded. Call load() instead.")
    if key:
        val = immutable_config_values.get(key.upper(), default)
        return val.copy() if hasattr(val, "copy") else val  # type: ignore
    else:
        return immutable_config_values.copy()


if __name__ == "__main__":
    import doctest

    doctest.testmod()
