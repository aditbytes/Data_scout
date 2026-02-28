# DataScout — Streamlit Application Package

# PEP 562 lazy-loader: makes `streamlit_app.services`, `.utils`, and
# `.components` accessible as attributes (required by unittest.mock.patch)
# without eagerly importing boto3 or AWS clients at startup.
import importlib as _importlib

_SUBPACKAGES = {'services', 'utils', 'components'}


def __getattr__(name: str):
    if name in _SUBPACKAGES:
        return _importlib.import_module(f'streamlit_app.{name}')
    raise AttributeError(f"module 'streamlit_app' has no attribute {name!r}")
