import ast
from pathlib import Path


def test_ctkfont_positional_weight_values_are_valid():
    source = Path("backgroundpxr/ui.py").read_text(encoding="utf-8")
    tree = ast.parse(source)

    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        if not (
            isinstance(func, ast.Attribute)
            and func.attr == "CTkFont"
            and isinstance(func.value, ast.Name)
            and func.value.id == "ctk"
        ):
            continue

        if len(node.args) >= 3 and isinstance(node.args[2], ast.Constant):
            assert node.args[2].value in {"normal", "bold"}, (
                "The 3rd positional CTkFont argument is font weight and must be "
                "'normal' or 'bold'. Use underline=True for underlining."
            )
