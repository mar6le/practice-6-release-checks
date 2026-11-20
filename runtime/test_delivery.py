def test_required_source_and_lockfile(host):
    assert host.file("/srv/gateway/gateway.py").is_file
    requirements = host.file("/srv/gateway/requirements.txt").content_string
    assert "waitress==3.0.2" in requirements


def test_gateway_is_pid_one(host):
    assert b"gateway.py" in host.file("/proc/1/cmdline").content.split(b"\0")


def test_gateway_tcp_port(host):
    port = host.check_output("printenv HTTP_PORT")
    probe = (
        "import socket\n"
        f"with socket.create_connection(('127.0.0.1', {int(port)}), timeout=2):\n"
        "    pass\n"
    )
    assert host.run("python -c %s", probe).rc == 0


def test_gateway_has_no_root_uid(host):
    identity = host.file("/proc/1/status").content_string
    fields = next(line for line in identity.splitlines() if line.startswith("Uid:")).split()
    assert fields[1:] == ["12540"] * 4
