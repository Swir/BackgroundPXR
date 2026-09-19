from backgroundpxr.studio_v046 import history_button_states, history_feedback


def test_history_button_states_follow_available_actions():
    assert history_button_states(False, False) == ("disabled", "disabled")
    assert history_button_states(True, False) == ("normal", "disabled")
    assert history_button_states(False, True) == ("disabled", "normal")
    assert history_button_states(True, True) == ("normal", "normal")


def test_history_feedback_is_localized_with_english_fallback():
    assert "Undo" in history_feedback("English", "undo")
    assert "Ponowiono" in history_feedback("Polski", "redo")
    assert "Redo" in history_feedback("Deutsch", "redo")
