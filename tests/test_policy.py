import warnings
from webob import Request
from zope.interface.verify import verifyObject
from pyramid.security import forget
from pyramid.security import remember
from pyramid.testing import testConfig
from pyramid.testing import DummyRequest
from pyramid.testing import DummySecurityPolicy
from pyramid.interfaces import IAuthenticationPolicy
from pyramid_jwt.policy import JWTAuthenticationPolicy


def test_interface():
    verifyObject(IAuthenticationPolicy, JWTAuthenticationPolicy('secret'))


def test_minimal_roundtrip():
    policy = JWTAuthenticationPolicy('secret')
    request = Request.blank('/')
    request.authorization = ('JWT', policy.create_token(15))
    assert policy.unauthenticated_userid(request) == 15


def test_wrong_auth_scheme():
    policy = JWTAuthenticationPolicy('secret')
    request = Request.blank('/')
    request.authorization = ('Other', policy.create_token(15))
    assert policy.unauthenticated_userid(request) is None


def test_other_header():
    policy = JWTAuthenticationPolicy('secret', http_header='X-Token')
    request = Request.blank('/')
    request.headers['X-Token'] = policy.create_token(15)
    assert policy.unauthenticated_userid(request) == 15


def test_expired_token():
    policy = JWTAuthenticationPolicy('secret', expiration=-1)
    request = Request.blank('/')
    request.authorization = ('JWT', policy.create_token(15))
    assert policy.unauthenticated_userid(request) is None
    policy.leeway = 5
    assert policy.unauthenticated_userid(request) == 15


def test_remember_warning():
    policy = JWTAuthenticationPolicy('secret', http_header='X-Token')
    with testConfig() as config:
        config.set_authorization_policy(DummySecurityPolicy())
        config.set_authentication_policy(policy)
        request = DummyRequest()
        with warnings.catch_warnings(record=True) as w:
            remember(request, 15)
    assert len(w) == 1
    assert issubclass(w[-1].category, UserWarning)
    assert 'JWT tokens' in str(w[-1].message)
    assert w[-1].filename.endswith('test_policy.py')


def test_forget_warning():
    policy = JWTAuthenticationPolicy('secret', http_header='X-Token')
    with testConfig() as config:
        config.set_authorization_policy(DummySecurityPolicy())
        config.set_authentication_policy(policy)
        request = DummyRequest()
        with warnings.catch_warnings(record=True) as w:
            forget(request)
    assert len(w) == 1
    assert issubclass(w[-1].category, UserWarning)
    assert 'JWT tokens' in str(w[-1].message)
    assert w[-1].filename.endswith('test_policy.py')