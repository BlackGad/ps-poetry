from ps.version import VersionPicker


def test_picker_pick_first_valid():
    picker = VersionPicker([])
    result = picker.pick(["invalid", "1.2.3"])
    assert result.major == 1
    assert result.minor == 2
    assert result.patch == 3


def test_picker_pick_with_condition():
    picker = VersionPicker([])
    result = picker.pick(["[in] 1.2.3"])
    assert result.major == 1
    assert result.minor == 2
    assert result.patch == 3


def test_picker_pick_invalid_condition_skips():
    picker = VersionPicker([])
    result = picker.pick(["[in 1.2.3", "1.2.3"])
    assert result.major == 1
    assert result.minor == 2
    assert result.patch == 3


def test_picker_pick_fallback():
    picker = VersionPicker([])
    result = picker.pick(["invalid", ""])
    assert result.major == 0
    assert result.minor is None
    assert result.patch is None
