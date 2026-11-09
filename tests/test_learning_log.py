"""第3回 宿題（実装）: save_learning_log と承認の流れのテスト（LLM も API キーも使わない）。"""

from pydantic_ai import DeferredToolRequests
from pydantic_ai.messages import ToolReturnPart
from pydantic_ai.models.test import TestModel

from app import tools
from app.agent import agent, run_with_approval


def _use_tmp_log_dir(monkeypatch, tmp_path):
    log_dir = tmp_path / "learning_log"
    monkeypatch.setattr(tools, "LOG_DIR", log_dir)
    return log_dir


def test_save_learning_log_writes_file(monkeypatch, tmp_path):
    log_dir = _use_tmp_log_dir(monkeypatch, tmp_path)
    message = tools.save_learning_log("第3回 ツール", "docstring がツールの説明になる")
    files = list(log_dir.glob("*.md"))
    assert len(files) == 1 and "保存しました" in message
    assert "docstring がツールの説明になる" in files[0].read_text(encoding="utf-8")


def test_save_learning_log_rejects_empty(monkeypatch, tmp_path):
    log_dir = _use_tmp_log_dir(monkeypatch, tmp_path)
    assert "保存はしていません" in tools.save_learning_log("", "")
    assert not log_dir.exists()


def test_save_stops_for_approval_before_writing(monkeypatch, tmp_path):
    log_dir = _use_tmp_log_dir(monkeypatch, tmp_path)
    result = agent.run_sync("記録して", model=TestModel(call_tools=["save_learning_log"]))
    assert isinstance(result.output, DeferredToolRequests)
    assert [c.tool_name for c in result.output.approvals] == ["save_learning_log"]
    assert not log_dir.exists()  # 承認前なので、まだ書き込まれていない


def test_approved_save_writes_file(monkeypatch, tmp_path):
    log_dir = _use_tmp_log_dir(monkeypatch, tmp_path)
    model = TestModel(call_tools=["save_learning_log"])
    result = run_with_approval(agent, "記録して", model, answer=lambda _: "y")
    assert isinstance(result.output, str)
    assert len(list(log_dir.glob("*.md"))) == 1


def test_denied_save_does_not_write(monkeypatch, tmp_path):
    log_dir = _use_tmp_log_dir(monkeypatch, tmp_path)
    model = TestModel(call_tools=["save_learning_log"])
    result = run_with_approval(agent, "記録して", model, answer=lambda _: "n")
    assert isinstance(result.output, str)
    assert not log_dir.exists()
    returns = [p for m in result.all_messages() for p in m.parts if isinstance(p, ToolReturnPart)]
    assert any("許可しませんでした" in str(p.content) for p in returns)
