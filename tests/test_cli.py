from typer.testing import CliRunner

from tech_brief.cli import app


def test_cli_exposes_product_commands():
    result = CliRunner().invoke(app, ["--help"])

    assert result.exit_code == 0
    assert "generate" in result.output
    assert "sync" in result.output
    assert "serve" in result.output
    assert "worker" in result.output
