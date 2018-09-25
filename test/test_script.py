from functools import partial
from unittest.mock import patch

from pytest import raises

from pychroot import __title__ as project
from pychroot.scripts import run


def test_script_run(capfd):
    """Test regular code path for running scripts."""
    script = partial(run, project)

    with patch('{}.scripts.import_module'.format(project)) as import_module:
        import_module.side_effect = ImportError("baz module doesn't exist")

        # default error path when script import fails
        with patch('sys.argv', [project]):
            with raises(SystemExit) as excinfo:
                script()
            assert excinfo.value.code == 1
            out, err = capfd.readouterr()
            err = err.strip().split('\n')
            assert len(err) == 3
            assert err[0] == "Failed importing: baz module doesn't exist!"
            assert err[1].startswith("Verify that {} and its deps".format(project))
            assert err[2] == "Add --debug to the commandline for a traceback."

        # running with --debug should raise an ImportError when there are issues
        with patch('sys.argv', [project, '--debug']):
            with raises(ImportError):
                script()
            out, err = capfd.readouterr()
            err = err.strip().split('\n')
            assert len(err) == 2
            assert err[0] == "Failed importing: baz module doesn't exist!"
            assert err[1].startswith("Verify that {} and its deps".format(project))

        import_module.reset_mock()

    # no args
    with patch('sys.argv', [project]):
        with raises(SystemExit) as excinfo:
            script()
        assert excinfo.value.code == 2
        out, err = capfd.readouterr()
        assert err.startswith("{}: error: ".format(project))
