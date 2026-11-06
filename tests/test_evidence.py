import hashlib
import json
from pathlib import Path
import pytest
from scripts.export_dashboard import validate
from scripts.policy import REQUIRED
from scripts.run_lab import probe_container


def report_for(path):
    path.write_text('real test evidence\n')
    checks = {key: {'status': 'pass'} for key in REQUIRED}
    return {'schema_version': 1, 'kind': 'laboratory_execution',
            'scenarios': [{'id': s, 'checks': checks, 'decision': 'approved'} for s in ['candidate', 'health-failure', 'root-user']],
            'files': [{'path': path.name, 'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}]}


def test_tampered_evidence_is_rejected(tmp_path):
    path = tmp_path / 'test.log'
    report = report_for(path)
    validate(report, tmp_path)
    path.write_text('tampered')
    with pytest.raises(ValueError, match='Integridad'):
        validate(report, tmp_path)


def test_path_traversal_is_rejected(tmp_path):
    report = report_for(tmp_path / 'test.log')
    report['files'][0]['path'] = '../outside.log'
    with pytest.raises(ValueError, match='Ruta'):
        validate(report, tmp_path)


def test_inconsistent_approval_is_rejected(tmp_path):
    report = report_for(tmp_path / 'test.log')
    report['scenarios'][0]['checks']['scan']['status'] = 'not_run'
    with pytest.raises(ValueError, match='Decisión'):
        validate(report, tmp_path)


@pytest.mark.parametrize('http_status,uids,docker_state,health_result,user_result', [
    (200, [10001]*4, 'healthy', 'pass', 'pass'),
    (503, [10001]*4, 'unhealthy', 'fail', 'pass'),
    (200, [0]*4, 'healthy', 'pass', 'fail'),
    (200, [10001, 0, 10001, 10001], 'healthy', 'pass', 'fail'),
])
def test_probe_uses_measured_http_and_process_credentials(monkeypatch, tmp_path, http_status, uids, docker_state, health_result, user_result):
    # Command-boundary unit test; NOT represented as a real container execution.
    def fake_run(command, timeout=300):
        if 'inspect' in command:
            return 0, json.dumps({'Status': docker_state})
        if '/proc/1/status' in command[-1]:
            return 0, json.dumps({'uids': uids})
        return 0, json.dumps({'http_status': http_status, 'body': {'status': 'ok'} if http_status == 200 else 'unavailable'})
    monkeypatch.setattr('scripts.run_lab.run', fake_run)
    health, user = probe_container('arbitrary-container-name', tmp_path)
    assert health['status'] == health_result
    assert user['status'] == user_result
