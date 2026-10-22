"""Hisab solver — exact computer-algebra engine (SymPy).

Every answer is COMPUTED by SymPy, never hallucinated. The pedagogical steps
shown to the user are derived from the actual computation (coefficients,
discriminant, substituted formula values), so they cannot drift from the
answer. This module has no network calls and no API keys: it works offline,
unlimited, forever.
"""
import re

import sympy as sp
from sympy.parsing.sympy_parser import (
    parse_expr as _parse_expr,
    standard_transformations,
    implicit_multiplication_application,
    convert_xor,
)

_TRANSFORMS = standard_transformations + (
    implicit_multiplication_application,
    convert_xor,
)

_MAIN = sp.symbols("x")
_ENGINE = f"SymPy {sp.__version__} (exact computer algebra)"


def _preprocess(text):
    """Normalize human math typing into SymPy-parseable form."""
    t = (text or "").strip()
    if not t:
        return ""
    t = t.replace("×", "*").replace("⋅", "*").replace("÷", "/")
    t = t.replace("√(", "sqrt(").replace("√", "sqrt")
    t = t.replace("²", "**2").replace("³", "**3")
    t = t.replace("π", "pi")
    # d/dx f  -> Derivative(f, x)
    m = re.match(r"(?i)^\s*d\s*/\s*d\s*([a-z])\s+(.+)$", t)
    if m:
        var, body = m.group(1), m.group(2)
        return f"Derivative({body},{var})"
    # ∫ ... dx  -> Integral(..., x)
    m = re.match(r"∫\s*(.+?)\s*d\s*([a-z])\s*$", t)
    if m:
        return f"Integral({m.group(1)},{m.group(2)})"
    # lim x->a f  -> Limit(f, x, a)
    m = re.match(r"(?i)^\s*lim\s*([a-z])\s*->\s*([^ ]+)\s+(.+)$", t)
    if m:
        return f"Limit({m.group(3)},{m.group(1)},{m.group(2)})"
    return t


_ALLOWED_NAMES = {
    "sin": sp.sin, "cos": sp.cos, "tan": sp.tan,
    "asin": sp.asin, "acos": sp.acos, "atan": sp.atan,
    "exp": sp.exp, "log": sp.log, "ln": sp.log, "sqrt": sp.sqrt,
    "pi": sp.pi, "e": sp.E, "E": sp.E,
    "Abs": sp.Abs, "abs": sp.Abs,
}


def _parse_side(t):
    """Parse one side of an equation/expression."""
    try:
        expr = _parse_expr(t, transformations=_TRANSFORMS,
                           local_dict=dict(_ALLOWED_NAMES))
    except Exception:
        raise ValueError(
            "Samajh nahi aaya — masla dobara likho, misaal: 2x+5=11 ya d/dx x^3")
    if not isinstance(expr, (sp.Expr, sp.Derivative, sp.Integral, sp.Limit)):
        raise ValueError("Samajh nahi aaya — masla dobara likho.")
    return expr


def _to_expr(text):
    """Parse text into a SymPy expression (or Eq). Raises ValueError."""
    t = _preprocess(text)
    if not t:
        raise ValueError("Khali input — masla likho ya photo upload karo.")
    if len(t) > 2000:
        raise ValueError("Input bohat lamba hai (2000 chars limit).")
    # Reject obvious non-math / code-injection shapes.
    if re.search(r"(__|import|lambda|exec|eval|open\(|os\.|sys\.)", t):
        raise ValueError("Ye math expression nahi lag raha.")
    # A real problem has a digit, an operator, '=', or a known function.
    # ("hello world" would otherwise parse as hello*world.)
    if not re.search(r"[0-9=+\-*/^()\[\]√∫]", t) and not any(
            fn in t for fn in ("sin", "cos", "tan", "log", "ln", "sqrt",
                               "exp", "pi", "Derivative", "Integral", "Limit")):
        raise ValueError("Ye math expression nahi lag raha — masla likho.")
    if "=" in t and not t.startswith(("Derivative(", "Integral(", "Limit(")):
        parts = t.split("=")
        if len(parts) != 2 or not parts[0].strip() or not parts[1].strip():
            raise ValueError("Equation mein sirf ek '=' hona chahiye.")
        return sp.Eq(_parse_side(parts[0]), _parse_side(parts[1]))
    return _parse_side(t)


def _symbols_in(expr):
    return sorted(expr.free_symbols, key=lambda s: s.name)


def _fmt(expr):
    return str(expr)


def solve_linear(coeffs, var):
    """Pedagogical steps for a*x + b = 0, derived from the coefficients."""
    a, b = coeffs
    steps = []
    steps.append({
        "title": "Standard form",
        "math": f"{_fmt(a*var + b)} = 0",
        "note": "Masle ko ax + b = 0 ki shakal mein likho.",
    })
    if b != 0:
        op = "-" if b > 0 else "+"
        steps.append({
            "title": "Dono taraf se hatayo",
            "math": f"{_fmt(a*var)} = {_fmt(-b)}",
            "note": f"Dono taraf {op} {_fmt(abs(b))} karo — barabri qaim rehti hai.",
        })
    steps.append({
        "title": f"{_fmt(a)} se divide karo",
        "math": f"{var} = {_fmt((-b)/a)}",
        "note": f"Dono taraf {_fmt(a)} se divide karo.",
    })
    return steps, sp.simplify(-b/a)


def solve_quadratic(a, b, c, var):
    """Steps via the quadratic formula with substituted values."""
    disc = sp.expand(b**2 - 4*a*c)
    steps = [{
        "title": "Standard form",
        "math": f"{_fmt(a*var**2 + b*var + c)} = 0",
        "note": f"a = {_fmt(a)}, b = {_fmt(b)}, c = {_fmt(c)} pehchano.",
    }, {
        "title": "Discriminant nikalo",
        "math": f"D = b² − 4ac = {_fmt(disc)}",
        "note": ("D > 0: do haqeeqi hal; D = 0: ek dohra hal; "
                  "D < 0: koi haqeeqi hal nahi."),
    }, {
        "title": "Quadratic formula lagao",
        "math": f"x = (−b ± √D) / 2a = ({_fmt(-b)} ± √{_fmt(disc)}) / {_fmt(2*a)}",
        "note": "Qeematien rakh kar simplify karo.",
    }]
    roots = sp.solve(a*var**2 + b*var + c, var)
    return steps, roots


def _calculus_rule(expr, var):
    """Name the rule for common derivative/integral shapes (best effort)."""
    e = sp.expand(expr)
    if e.is_Pow and e.base == var and e.exp.is_number:
        return "Power rule: d/dx[xⁿ] = n·xⁿ⁻¹"
    if e.is_Add:
        return "Sum rule: har term ka alag derivative/integral lo"
    if e.is_Mul:
        return "Constant multiple rule: constant bahar nikalo"
    if isinstance(e, (sp.sin, sp.cos, sp.tan, sp.exp, sp.log)):
        return f"Standard derivative/integral of {e.func.__name__}"
    return "Standard differentiation/integration rules"


def solve_problem(text, mode="auto"):
    """Solve a math problem. Returns a dict with derived steps and answer.

    mode: auto | solve | simplify | factor | expand | differentiate |
          integrate | limit
    """
    expr = _to_expr(text)
    var = _MAIN
    free = _symbols_in(expr)
    if free and var not in free:
        var = free[0]

    # --- Derivative / Integral / Limit wrappers from preprocessing ---
    if isinstance(expr, sp.Derivative):
        f, v = expr.args[0], (expr.args[1][0] if expr.args[1:] else var)
        result = sp.diff(f, v)
        return {
            "ok": True, "engine": _ENGINE, "kind": "derivative",
            "input": text.strip(),
            "steps": [
                {"title": "Function", "math": f"f({_fmt(v)}) = {_fmt(f)}",
                 "note": _calculus_rule(f, v)},
                {"title": "Differentiate karo",
                 "math": f"f′({_fmt(v)}) = {_fmt(result)}",
                 "note": "Har term par rule lagao, phir simplify karo."},
            ],
            "answer": _fmt(result),
            "answer_latex": sp.latex(result),
        }
    if isinstance(expr, sp.Integral):
        f, v = expr.args[0], (expr.args[1][0] if expr.args[1:] else var)
        result = sp.integrate(f, v)
        return {
            "ok": True, "engine": _ENGINE, "kind": "integral",
            "input": text.strip(),
            "steps": [
                {"title": "Integrand", "math": f"∫ {_fmt(f)} d{_fmt(v)}",
                 "note": _calculus_rule(f, v)},
                {"title": "Integrate karo",
                 "math": f"= {_fmt(result)} + C",
                 "note": "Indefinite integral — constant C mat bhoolo."},
            ],
            "answer": f"{_fmt(result)} + C",
            "answer_latex": sp.latex(result) + " + C",
        }
    if isinstance(expr, sp.Limit):
        f, v, a = expr.args[0], expr.args[1], expr.args[2]
        result = sp.limit(f, v, a)
        num = sp.simplify(f.as_numer_denom()[0].subs(v, a)) \
            if hasattr(f, "as_numer_denom") else None
        note = "Direct substitution se hal ho gaya."
        try:
            if num is not None and num == 0:
                note = ("0/0 form — L'Hôpital ya standard limits "
                        "(jaise sin x / x → 1) istemal hue.")
        except Exception:
            pass
        return {
            "ok": True, "engine": _ENGINE, "kind": "limit",
            "input": text.strip(),
            "steps": [
                {"title": "Limit", "math": f"lim({_fmt(v)}→{_fmt(a)}) {_fmt(f)}",
                 "note": note},
                {"title": "Evaluate karo", "math": f"= {_fmt(result)}",
                 "note": "Qeemat rakho aur simplify karo."},
            ],
            "answer": _fmt(result),
            "answer_latex": sp.latex(result),
        }

    is_equation = isinstance(expr, sp.Equality) or (
        mode in ("auto", "solve") and "=" in (text or ""))

    if mode in ("auto", "solve") and is_equation:
        if not isinstance(expr, sp.Equality):
            raise ValueError("Equation mein sirf ek '=' hona chahiye.")
        lhs, rhs = expr.lhs, expr.rhs
        poly_expr = sp.expand(lhs - rhs)
        # System of equations: solve() with multiple symbols.
        unknowns = [s for s in _symbols_in(poly_expr)
                    if s.name in "xyz" or len(_symbols_in(poly_expr)) > 1]
        if len(_symbols_in(poly_expr)) > 1:
            sol = sp.solve(poly_expr, unknowns, dict=True)
            if not sol:
                raise ValueError("Is system ka hal nahi mila.")
            d = sol[0]
            steps = [{
                "title": "System",
                "math": f"{_fmt(lhs)} = {_fmt(rhs)}",
                "note": ("Aik equation se variable ki qeemat nikalo, "
                         "doosri mein rakho (substitution)."),
            }, {
                "title": "Hal",
                "math": ", ".join(f"{k} = {_fmt(v)}" for k, v in d.items()),
                "note": "Jawab ko dono equations mein rakh kar verify karo.",
            }]
            return {"ok": True, "engine": _ENGINE, "kind": "system",
                    "input": text.strip(), "steps": steps,
                    "answer": ", ".join(f"{k} = {_fmt(v)}"
                                        for k, v in d.items()),
                    "answer_latex": ", ".join(
                        f"{sp.latex(k)} = {sp.latex(v)}" for k, v in d.items())}
        try:
            poly = sp.Poly(poly_expr, var)
        except Exception:
            poly = None
        if poly is not None and poly.degree() == 1:
            a, b = poly.all_coeffs()
            steps, ans = solve_linear((a, b), var)
            return {"ok": True, "engine": _ENGINE, "kind": "linear",
                    "input": text.strip(), "steps": steps,
                    "answer": f"{var} = {_fmt(ans)}",
                    "answer_latex": f"{sp.latex(var)} = {sp.latex(ans)}"}
        if poly is not None and poly.degree() == 2:
            a, b, c = poly.all_coeffs()
            steps, roots = solve_quadratic(a, b, c, var)
            ans = ", ".join(f"{var} = {_fmt(r)}" for r in roots)
            return {"ok": True, "engine": _ENGINE, "kind": "quadratic",
                    "input": text.strip(), "steps": steps, "answer": ans,
                    "answer_latex": ", ".join(
                        f"{sp.latex(var)} = {sp.latex(r)}" for r in roots)}
        # General equation: SymPy solves, steps describe the move honestly.
        roots = sp.solve(poly_expr, var)
        if not roots:
            raise ValueError("Is equation ka hal nahi mila.")
        return {
            "ok": True, "engine": _ENGINE, "kind": "equation",
            "input": text.strip(),
            "steps": [
                {"title": "Standard form",
                 "math": f"{_fmt(poly_expr)} = 0",
                 "note": "Sab kuch ek taraf lao."},
                {"title": "Hal karo",
                 "math": ", ".join(f"{var} = {_fmt(r)}" for r in roots),
                 "note": ("Exact algebra se hal — jawab ko wapas rakh kar "
                          "verify karo.")},
            ],
            "answer": ", ".join(f"{var} = {_fmt(r)}" for r in roots),
            "answer_latex": ", ".join(
                f"{sp.latex(var)} = {sp.latex(r)}" for r in roots),
        }

    if mode == "factor" or (mode == "auto" and False):
        result = sp.factor(expr)
        kind = "factor"
    elif mode == "expand":
        result = sp.expand(expr)
        kind = "expand"
    elif mode == "differentiate":
        result = sp.diff(expr, var)
        kind = "derivative"
    elif mode == "integrate":
        result = sp.integrate(expr, var)
        kind = "integral"
        return {
            "ok": True, "engine": _ENGINE, "kind": kind,
            "input": text.strip(),
            "steps": [
                {"title": "Integrand", "math": f"∫ {_fmt(expr)} d{_fmt(var)}",
                 "note": _calculus_rule(expr, var)},
                {"title": "Integrate karo",
                 "math": f"= {_fmt(result)} + C",
                 "note": "Indefinite integral — constant C mat bhoolo."}],
            "answer": f"{_fmt(result)} + C",
            "answer_latex": sp.latex(result) + " + C"}
    elif mode == "limit":
        raise ValueError("Limit ke liye 'lim x->a expression' likho.")
    else:
        result = sp.simplify(expr)
        kind = "simplify"

    note = {"factor": "Common factors nikalo.",
            "expand": "Brackets khol kar simplify karo.",
            "derivative": _calculus_rule(expr, var),
            "simplify": "Terms jama karo aur qeematien ghatayo."}[kind]
    return {
        "ok": True, "engine": _ENGINE, "kind": kind,
        "input": text.strip(),
        "steps": [
            {"title": "Expression", "math": _fmt(expr), "note": note},
            {"title": "Nateeja", "math": _fmt(result),
             "note": "Exact computer-algebra se verify shuda."},
        ],
        "answer": _fmt(result),
        "answer_latex": sp.latex(result),
    }
