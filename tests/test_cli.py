from typer.testing import CliRunner

from fusion_calling.cli import app


runner = CliRunner()


def test_help_exposes_only_read_only_commands() -> None:
    result = runner.invoke(app, ["--help"])

    assert result.exit_code == 0
    assert "preflight" in result.stdout
    assert "audio-list" in result.stdout
    assert "spoke-inspect" in result.stdout
    assert "dial" not in result.stdout.lower()
