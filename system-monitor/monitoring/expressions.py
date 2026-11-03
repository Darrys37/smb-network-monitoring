"""Small data-only predicate language. No eval, attribute access or arbitrary code."""
import math
import re
import string

OPS = {"always", "all", "any", "not", "eq", "ne", "in", "not_in", "lt", "le", "gt", "ge", "is_null", "not_null", "truthy"}


def validate(expression, depth=0):
    if depth > 20 or not isinstance(expression, dict) or expression.get("op") not in OPS:
        raise ValueError("Invalid decision-table expression")
    op = expression["op"]
    if op == "always":
        if set(expression) != {"op"}:
            raise ValueError("Invalid unconditional row")
    elif op in {"all", "any"}:
        if set(expression) != {"op", "args"} or not isinstance(expression["args"], list) or not expression["args"]:
            raise ValueError("Empty/invalid logical expression")
        for item in expression["args"]:
            validate(item, depth + 1)
    elif op == "not":
        if set(expression) != {"op", "arg"}:
            raise ValueError("Invalid negation")
        validate(expression["arg"], depth + 1)
    else:
        keys = {"op", "field"}
        if op not in {"is_null", "not_null", "truthy"}:
            keys.add("other_field" if "other_field" in expression else "value")
        if set(expression) != keys or not re.fullmatch(r"[a-z][a-z0-9_]*", expression.get("field", "")):
            raise ValueError("Invalid predicate operands")
        if "other_field" in expression and not re.fullmatch(r"[a-z][a-z0-9_]*", expression["other_field"]):
            raise ValueError("Invalid comparison field")
        if op in {"in", "not_in"} and not isinstance(expression.get("value"), list):
            raise ValueError("Membership requires literal list")
    return expression


def matches(expression, facts):
    op = expression["op"]
    if op == "always":
        return True
    if op == "all":
        return all(matches(item, facts) for item in expression["args"])
    if op == "any":
        return any(matches(item, facts) for item in expression["args"])
    if op == "not":
        return not matches(expression["arg"], facts)
    actual = facts.get(expression["field"])
    if op == "is_null":
        return actual is None
    if op == "not_null":
        return actual is not None
    if op == "truthy":
        return bool(actual)
    expected = facts.get(expression["other_field"]) if "other_field" in expression else expression["value"]
    if op == "eq":
        return actual == expected
    if op == "ne":
        return actual != expected
    if op == "in":
        return actual in expected
    if op == "not_in":
        return actual not in expected
    if any(type(value) not in (int, float) or not math.isfinite(value) for value in (actual, expected)):
        return False
    return {"lt": lambda: actual < expected, "le": lambda: actual <= expected,
            "gt": lambda: actual > expected, "ge": lambda: actual >= expected}[op]()


def render(template, facts):
    output = []
    for literal, field, format_spec, conversion in string.Formatter().parse(template):
        output.append(literal)
        if field is not None:
            if not re.fullmatch(r"[a-z][a-z0-9_]*", field) or conversion or format_spec not in {"", ".2f", "g"}:
                raise ValueError("Unsafe reason-template field")
            value = facts.get(field)
            output.append(format(value, format_spec))
    return "".join(output)
