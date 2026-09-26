from src.tools.context_trimmer import trim_traceback

def test_trim_traceback_shortens_paths():
    sample = (
        '=== FAILURES ===\n'
        '  File "C:\\Users\\Eashwar\\repo\\test.py", line 25, in test_example\n'
        'AssertionError: assert 1 == 2'
    )
    result = trim_traceback(sample)
    assert 'File ".../test.py"' in result
    assert "AssertionError" in result

def test_trim_traceback_empty():
    assert trim_traceback("") == ""
