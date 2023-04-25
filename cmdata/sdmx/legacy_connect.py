"""Functionality for dealing with SSL connection issues.

The package contains code to work around servers that use legacy SSL
verification, support for which by default is turned off in current versions
of OpenSSL. This issue otherwise can make it impossible to connect to certain
providers, including OECD Stats and the UN Data Service (at least as of
2023-04-25).
"""

import typing as tp
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

def get_legacy_session() -> requests.Session:
    """Return a requests.Session with support for SSL legacy server connect.
    
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
