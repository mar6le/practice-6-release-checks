import json
from wsgiref.util import setup_testing_defaults

import pytest

from gateway import Settings, make_gateway


@pytest.fixture
def service(monkeypatch):
    monkeypatch.setenv("HTTP_PORT", "8080")
    monkeypatch.setenv("BUILD_REF", "practice.6")
    monkeypatch.setenv("SERVICE_STATE", "available")
    return lambda: make_gateway(Settings.from_env())


def get_json(app, path):
    request = {"PATH_INFO": path, "REQUEST_METHOD": "GET"}
    setup_testing_defaults(request)
    statuses = []
    body = b"".join(app(request, lambda status, headers, exc_info=None: statuses.append(status)))
    return int(statuses[0].split()[0]), json.loads(body)


@pytest.mark.parametrize(
    ("path", "status", "body"),
    [("/health", 200, {"status": "available"}), ("/version", 200, {"commit": "practice.6"})],
)
def test_get_endpoints(service, path, status, body):
    assert get_json(service(), path) == (status, body)


def test_maintenance_has_http_503(service, monkeypatch):
    monkeypatch.setenv("SERVICE_STATE", "maintenance")
    assert get_json(service(), "/health") == (503, {"status": "maintenance"})


@pytest.mark.parametrize(
    ("key", "value"),
    [
        ("HTTP_PORT", "99999"),
        ("HTTP_PORT", "abc"),
        ("HTTP_PORT", "80"),
        ("BUILD_REF", ""),
        ("BUILD_REF", "wrong/tag"),
        ("SERVICE_STATE", "unknown"),
    ],
)
def test_invalid_configuration(service, monkeypatch, key, value):
    monkeypatch.setenv(key, value)
    with pytest.raises(ValueError, match=key):
        service()


def test_version_sends_json_content_type(service):
    request = {"PATH_INFO": "/version", "REQUEST_METHOD": "GET"}
    setup_testing_defaults(request)
    headers = {}
    list(service()(request, lambda status, items, exc_info=None: headers.update(items)))
    assert headers["Content-Type"].startswith("application/json")
