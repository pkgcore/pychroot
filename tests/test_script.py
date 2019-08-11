from functools import partial
from unittest.mock import patch

from pytest import raises

from pychroot import __title__ as project
from pychroot.scripts import run


def test_script_run(capfd):
    """Test regular code path for running scripts."""
    script = partial(run, project)

    with patch(f'{project}.scripts.import_module') as import_module:
        import_exception = ImportError("baz module doesn't exist")
        import_exception.__cause__ = Exception('cause of ImportError')
        import_exception.__context__ = Exception('context of ImportError')
        import_module.side_effect = import_exception
        # explicitly handled ImportErrors don't show a backtrace
        with patch('sys.argv', [project]):
            with raises(SystemExit) as excinfo:
                script()
            assert excinfo.value.code == 1
            out, err = capfd.readouterr()
            err = err.strip().split('\n')
            assert len(err) == 3
            assert err[0] == "Failed importing: baz module doesn't exist!"
            assert err[1].startswith(f"Verify that {project} and its deps")
            assert err[2] == "Add --debug to the commandline for a traceback."
        import_module.reset_mock()

        import_module.side_effect = ImportError("baz module doesn't exist")
        # import errors show backtrace for unhandled exceptions or when --debug is passed
        for args in ([], ['--debug']):
            with patch('sys.argv', [project] + args):
                with raises(ImportError):
                    script()
                out, err = capfd.readouterr()
                err = err.strip().split('\n')
                assert len(err) == 2
                assert err[0] == "Failed importing: baz module doesn't exist!"
                assert err[1].startswith(f"Verify that {project} and its deps")
        import_module.reset_mock()

    # no args
    with patch('sys.argv', [project]):
        with raises(SystemExit) as excinfo:
            script()
        assert excinfo.value.code == 2
        out, err = capfd.readouterr()
        assert err.startswith(f"{project}: error: ")
