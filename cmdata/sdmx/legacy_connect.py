"""Functionality for dealing with SSL connection issues.

The package contains code to work around servers that use legacy SSL
verification, support for which by default is turned off in current versions
of OpenSSL. This issue otherwise can make it impossible to connect to certain
providers, including OECD Stats and the UN Data Service (at least as of
2023-04-25).
"""

import typing as tp
import io
import ssl
import requests
import urllib3


def get_legacy_server_connect_context():
    """Return an SSL context with support for legacy server connect.
    
    Returns
    -------
    ssl.SSLContext
    """
    ctx = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)
    ctx.options |= 0x4  # OP_LEGACY_SERVER_CONNECT
    return ctx
###END def get_legacy_server_connect_context

def get_legacy_session(**kwargs) -> requests.Session:
    """Return a requests.Session with support for SSL legacy server connect.

    Parameters
    ----------
    **kwargs
        Keyword arguments to pass to `requests.session` to create a `Session`
        instance.
    
    Returns
    -------
    requests.Session
        Session instance with the flag `OP_LEGACY_SERVER_CONNECT` set
    """
    ctx = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)
    ctx.options |= 0x4  # OP_LEGACY_SERVER_CONNECT
    session = requests.session()
    session.mount('https://', LegacyServerConnectAdapter())
    return session
###END def get_legacy_session

def get_legacy_connect_url_stream(
    url: str,
    session_kwargs : tp.Optional[tp.Mapping[str, tp.Any]] = None,
    get_kwargs : tp.Optional[tp.Mapping[str, tp.Any]] = None
) -> io.BytesIO:
    """Read a URL with legacy server connect, and return content as BytesIO.
    
    Parameters
    ----------
    url : str
        URL to connect to
    session_kwargs
        Additional keyword arguments to pass to `requests.session`.
    get_kwargs
        Additional keyword arguments to pass to `requests.Session.get`.
        
    Returns
    -------
    io.BytesIO
        BytesIO object with the content of the response of a GET query to
        `url`.
    """
    if session_kwargs is None:
        session_kwargs = dict()
    if get_kwargs is None:
        get_kwargs = dict()
    session: requests.Session = get_legacy_session(**session_kwargs)
    response: requests.Response = session.get(url, **get_kwargs)
    bytesio: io.BytesIO = io.BytesIO(response.content)
    return bytesio
###END def get_legacy_connect_url_stream


class CustomContextHTTPAdapter(requests.adapters.HTTPAdapter):
    """Base class for customizing requests HTTPAdapters.
    
    Attributes
    ----------
    ssl_context : ssl.SSLContext
        Custom SSL context (set through the `__init__` method)
    """

    def __init__(self, ssl_context=None, **kwargs):
        """
        Parameters
        ----------
        ssl_context : ssl.SSLContext
            Custom context to use in the HTTPAdapter
        **kwargs
            Keyword arguments for `requests.adapters.HTTPAdapter.__init__`
            method.
        """
        self.ssl_context = ssl_context
        super().__init__(**kwargs)
    ###END def CustomContextHTTPAdapter.__init__

    def init_poolmanager(self, connections, maxsize, block=False):
        """Overridden `init_poolmanager` method, utilizing custom SSL context."""
        self.poolmanager = urllib3.poolmanager.PoolManager(
            num_pools=connections,
            maxsize=maxsize,
            block=block,
            ssl_context=self.ssl_context
        )
    ###END def CustomContextHTTPAdapter.init_poolmanager

###END class CustomContextHTTPAdapter


class LegacyServerConnectAdapter(CustomContextHTTPAdapter):
    """Custom HTTP adapter which enables support for SSL legacy server connect."""

    def __init__(self, *args, **kwargs):
        """"
        Parameters
        ----------
        *args, **kwargs
            Arguments to be passed to `requests.adapters.HTTPAdapter.__init__`"""
        if 'ssl_context' in kwargs:
            raise KeyError(
                '`ssl_context` keyword is not supported by this class, use '
                'the `CustomContextHTTPAdapter` base class instead.'
            )
        super().__init__(
            ssl_context=get_legacy_server_connect_context(),
            *args,
            **kwargs
        )
    ###END def LegacyServerConnectAdapter.__init__

###END class LegacyServerConnectAdapter
