"""
Operational Transformation engine.

Three operation types:
  {"type": "insert", "pos": int, "chars": str}
  {"type": "delete", "pos": int, "length": int}
  {"type": "retain", "pos": int, "length": int}  # no-op, used for composing

transform(op1, op2) answers:
  "Given op1 and op2 were both based on the same document,
   return op1' such that applying op2 then op1' gives the
   same result as applying op1 then op2'."
"""

def apply(content: str, op: dict) -> str:
    """Apply a single operation to a string."""
    if op["type"] == "insert":
        pos = min(op["pos"], len(content))
        return content[:pos] + op["chars"] + content[pos:]

    if op["type"] == "delete":
        pos = min(op["pos"], len(content))
        end = min(pos + op["length"], len(content))
        return content[:pos] + content[end:]

    return content  # retain — no change


def apply_all(content: str, ops: list[dict]) -> str:
    """Apply a list of operations in order."""
    for op in ops:
        content = apply(content, op)
    return content


def transform(op1: dict, op2: dict) -> dict:
    """
    Transform op1 against op2.
    Returns a new op1' that can be applied after op2
    and still produce the correct result.
    """
    t1, t2 = op1["type"], op2["type"]

    # --- Insert vs Insert ---
    if t1 == "insert" and t2 == "insert":
        # If op2 inserted before or at op1's position, shift op1 right
        if op2["pos"] <= op1["pos"]:
            return {**op1, "pos": op1["pos"] + len(op2["chars"])}
        return op1

    # --- Insert vs Delete ---
    if t1 == "insert" and t2 == "delete":
        # If op2 deleted content before op1's position, shift op1 left
        if op2["pos"] + op2["length"] <= op1["pos"]:
            return {**op1, "pos": op1["pos"] - op2["length"]}
        # If op2 deleted content that overlaps op1's position
        if op2["pos"] <= op1["pos"]:
            return {**op1, "pos": op2["pos"]}
        return op1

    # --- Delete vs Insert ---
    if t1 == "delete" and t2 == "insert":
        # If op2 inserted before op1's position, shift op1 right
        if op2["pos"] <= op1["pos"]:
            return {**op1, "pos": op1["pos"] + len(op2["chars"])}
        # If op2 inserted inside op1's delete range, extend op1's length
        if op2["pos"] < op1["pos"] + op1["length"]:
            return {**op1, "length": op1["length"] + len(op2["chars"])}
        return op1

    # --- Delete vs Delete ---
    if t1 == "delete" and t2 == "delete":
        p1, l1 = op1["pos"], op1["length"]
        p2, l2 = op2["pos"], op2["length"]

        # op2 is entirely before op1 — shift op1 left
        if p2 + l2 <= p1:
            return {**op1, "pos": p1 - l2}

        # op2 is entirely after op1 — no change
        if p2 >= p1 + l1:
            return op1

        # op2 overlaps op1 — shrink or eliminate op1
        new_pos = min(p1, p2)
        # How much of op1's range was NOT deleted by op2
        overlap_start = max(p1, p2)
        overlap_end   = min(p1 + l1, p2 + l2)
        survived = l1 - (overlap_end - overlap_start)
        if survived <= 0:
            return {"type": "retain", "pos": new_pos, "length": 0}
        return {**op1, "pos": new_pos, "length": survived}

    return op1  # fallback — retain or unknown types


def transform_all(ops: list[dict], against: list[dict]) -> list[dict]:
    """Transform a list of ops against another list of ops."""
    result = list(ops)
    for base_op in against:
        result = [transform(op, base_op) for op in result]
    return result