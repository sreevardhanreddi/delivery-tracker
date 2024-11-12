def dict_to_str(d: dict) -> str:
    s = ""
    for k, v in d.items():
        s += f"{k}: {v}\n"
    return "\n" + s
