from typer.testing import CliRunner

from tech_brief.cli import app


def test_cli_exposes_generate_command():
    result = CliRunner().invoke(app, ["--help"])

    assert result.exit_code == 0
    assert "generate" in result.output
