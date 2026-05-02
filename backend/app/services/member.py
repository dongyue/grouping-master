def get_attribute_warnings(constraints: list | None, attrs: dict[str, str]) -> list[str]:
    warnings = []
    if not constraints:
        return warnings
    for c in constraints:
        name = c["attribute_name"]
        allowed = c["allowed_values"]
        value = attrs.get(name)
        if value is None:
            warnings.append(f"缺少属性「{name}」")
        elif value not in allowed:
            warnings.append(f"「{name}」=「{value}」不在允许范围")
    return warnings
