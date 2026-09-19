from __future__ import annotations

import customtkinter as ctk

from .studio_v045 import BackgroundPXRStudio045App


HISTORY_TX = {
    "English": {
        "undo": "Undo",
        "redo": "Redo",
        "undo_status": "Undo applied — mask restored one step.",
        "redo_status": "Redo applied — mask restored one step.",
    },
    "Polski": {
        "undo": "Cofnij",
        "redo": "Ponów",
        "undo_status": "Cofnięto ostatnią zmianę maski.",
        "redo_status": "Ponowiono zmianę maski.",
    },
}


def history_button_states(can_undo: bool, can_redo: bool) -> tuple[str, str]:
    """Map editor history availability to CustomTkinter button states."""
    return ("normal" if can_undo else "disabled", "normal" if can_redo else "disabled")


def history_feedback(language: str, action: str) -> str:
    table = HISTORY_TX.get(language, HISTORY_TX["English"])
    key = "redo_status" if action == "redo" else "undo_status"
    return table[key]


class BackgroundPXRStudio046App(BackgroundPXRStudio045App):
    """Studio Pro with visible, state-aware undo/redo mask history."""

    def __init__(self, root):
        super().__init__(root)
        self.root.bind("<Control-Shift-z>", lambda _event: self._redo())
        self.root.bind("<Control-Shift-Z>", lambda _event: self._redo())
        self._sync_history_controls()

    def _build_manual_card(self, parent):
        super()._build_manual_card(parent)

        # Reuse the existing islands/reset row so history controls add no
        # vertical height to the 1600x900 CREATE inspector.
        actions = self.islands_btn.master
        actions.grid_columnconfigure((0, 1, 2, 3), weight=1)

        self.undo_mask_btn = ctk.CTkButton(
            actions,
            text="",
            image=self._icon("undo", "#BFEAFF", 14),
            command=self._undo,
            height=25,
            fg_color="#0F2946",
            hover_color="#163A5D",
            font=ctk.CTkFont("Segoe UI", 9),
        )
        self.undo_mask_btn.grid(row=0, column=2, sticky="ew", padx=2)

        self.redo_mask_btn = ctk.CTkButton(
            actions,
            text="",
            image=self._icon("redo", "#BFEAFF", 14),
            command=self._redo,
            height=25,
            fg_color="#0F2946",
            hover_color="#163A5D",
            font=ctk.CTkFont("Segoe UI", 9),
        )
        self.redo_mask_btn.grid(row=0, column=3, sticky="ew", padx=2)
        self._sync_history_controls()

    def _apply_language(self):
        super()._apply_language()
        if not hasattr(self, "undo_mask_btn"):
            return
        table = HISTORY_TX.get(self.language.get(), HISTORY_TX["English"])
        self.undo_mask_btn.configure(text=table["undo"])
        self.redo_mask_btn.configure(text=table["redo"])
        self._sync_history_controls()

    def _sync_history_controls(self) -> tuple[str, str]:
        editor = getattr(self, "editor", None)
        states = history_button_states(
            bool(editor and editor.can_undo),
            bool(editor and editor.can_redo),
        )
        undo_state, redo_state = states

        if hasattr(self, "undo_mask_btn"):
            self.undo_mask_btn.configure(state=undo_state)
            self.redo_mask_btn.configure(state=redo_state)

        tool_buttons = getattr(self, "tool_buttons", {})
        if "undo" in tool_buttons:
            tool_buttons["undo"].configure(state=undo_state)
        if "redo" in tool_buttons:
            tool_buttons["redo"].configure(state=redo_state)
        return states

    def _finish_active_stroke_for_history(self) -> None:
        if not getattr(self, "_painting", False) or self.editor is None:
            return
        self.editor.end_stroke()
        self._painting = False
        self._last_brush_point = None

    def _history_action(self, action: str) -> bool:
        self._cancel_live_recompose()
        editor = self.editor
        if editor is None:
            self._sync_history_controls()
            return False

        # Keyboard undo can arrive while the mouse button is still down. Close
        # the stroke first so a single Ctrl+Z always means one complete gesture.
        self._finish_active_stroke_for_history()
        changed = editor.redo() if action == "redo" else editor.undo()
        if not changed:
            self._sync_history_controls()
            return False

        self._recompose()
        self._refresh_previews()
        self.status_text.set(history_feedback(self.language.get(), action))
        self._sync_history_controls()
        return True

    def _undo(self):
        return self._history_action("undo")

    def _redo(self):
        return self._history_action("redo")

    def _on_after_release(self, event):
        result = super()._on_after_release(event)
        self._sync_history_controls()
        return result

    def _smart_cleanup(self):
        result = super()._smart_cleanup()
        self._sync_history_controls()
        return result

    def _remove_islands(self):
        result = super()._remove_islands()
        self._sync_history_controls()
        return result

    def _reset_mask(self):
        result = super()._reset_mask()
        self._sync_history_controls()
        return result

    def _set_tool(self, tool):
        result = super()._set_tool(tool)
        self._sync_history_controls()
        return result

    def _select_file(self, index):
        result = super()._select_file(index)
        self._sync_history_controls()
        return result

    def _clear_files(self):
        result = super()._clear_files()
        self._sync_history_controls()
        return result
