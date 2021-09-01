"""Tests for `nldi-xstool` CLI."""
import json
from tempfile import NamedTemporaryFile

from click.testing import CliRunner

from nldi_xstool.__main__ import main


def test_command_line_interface():
    """Test the CLI."""
    runner = CliRunner()
    result = runner.invoke(main)
    print(result)
    assert result.exit_code == 0
    assert "xsatpoint" in result.output
    help_result = runner.invoke(main, ["--help"])
    assert help_result.exit_code == 0
    assert "Usage:" in help_result.output


def test_xsatpoint():
    """Test xsatpoint CLI."""
    runner = CliRunner()

    with NamedTemporaryFile(mode="w+") as tf:
        result = runner.invoke(
            main,
            [
                "xsatpoint",
                "-f",
                tf.name,
                "--lonlat",
                "-103.80119",
                "40.2684",
                "--width",
                "100",
                "--numpoints",
                "11",
                "-r",
                "10m",
            ],
        )
        assert result.exit_code == 0
        ogdata = json.load(tf)
        feat = ogdata.get("features")
        assert len(feat) == 11


def test_xsatendpts():
    """Test xsatendpts CLI."""
    runner = CliRunner()

    with NamedTemporaryFile(mode="w+") as tf:
        result = runner.invoke(
            main,
            [
                "xsatendpts",
                "-f",
                tf.name,
                "-s",
                "-103.801134",
                "40.26733",
                "-e",
                "-103.800787",
                " 40.272798",
                "-c",
                "epsg:4326",
                "-n",
                "11",
                "-r",
                "10m",
                "-v",
                "True",
            ],
        )
        assert result.exit_code == 0
        ogdata = json.load(tf)
        feat = ogdata.get("features")
        assert len(feat) == 11


def test_xsatendpts_wres():
    """Test xsatendpts with varying 3DEP resolutions."""
    runner = CliRunner()
    res = ["1m", "3m", "5m", "10m", "30m"]
    for tr in res:
        print(f"resoluition: {tr}")
        with NamedTemporaryFile(mode="w+") as tf:
            result = runner.invoke(
                main,
                [
                    "xsatendpts",
                    "-f",
                    tf.name,
                    "-s",
                    "-103.801134",
                    "40.26733",
                    "-e",
                    "-103.800787",
                    " 40.272798",
                    "-c",
                    "epsg:4326",
                    "-n",
                    "11",
                    "-r",
                    tr,
                ],
            )
            assert result.exit_code == 0
            ogdata = json.load(tf)
            feat = ogdata.get("features")
            assert len(feat) == 11
