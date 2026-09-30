import re
import calendar

GS = "\x1d"

AI_FIXED_LEN = {
    "01": 14, "02": 14,
    "11": 6, "12": 6, "13": 6, "15": 6, "16": 6, "17": 6,
    "20": 2,
}

AI_VAR_LEN = {
    "10": 20, "21": 20, "22": 20, "23": 20,
    "240": 30, "30": 8, "37": 8,
    "90": 30, "91": 90, "92": 90, "93": 90, "94": 90,
    "95": 90, "96": 90, "97": 90, "98": 90, "99": 90,
}


def format_gs1_date(yymmdd):
    if not re.fullmatch(r"\d{6}", yymmdd):
        return None
    yy, mm, dd = int(yymmdd[:2]), int(yymmdd[2:4]), int(yymmdd[4:6])
    year = 2000 + yy if yy <= 49 else 1900 + yy
    if mm < 1 or mm > 12:
        return None
    if dd == 0:
        dd = calendar.monthrange(year, mm)[1]
    elif dd > calendar.monthrange(year, mm)[1]:
        return None
    return f"{year:04d}-{mm:02d}-{dd:02d}"


def parse_udi(code):
    result = {"gtin": "", "batch": "", "serial": "", "prod_date": "", "expiry_date": "", "ok": False, "format": ""}
    if not code:
        return result

    s = code.strip()
    s = re.sub(r"^\][A-Za-z0-9]{2}", "", s)
    s = s.strip().strip("\"'")

    if "(" in s:
        pairs = re.findall(r"\((\d{2,4})\)([^\(\)]*)", s)
        if pairs:
            result["format"] = "paren"
            _apply_pairs(pairs, result)
            return result

    if GS in s:
        segments = s.split(GS)
        result["format"] = "raw"
        for seg in segments:
            _parse_segment(seg, result)
        if result["gtin"]:
            result["ok"] = True
        return result

    result["format"] = "heuristic"
    _parse_heuristic(s, result)
    if result["gtin"]:
        result["ok"] = True
    return result


def _apply_pairs(pairs, result):
    for ai, val in pairs:
        val = val.strip()
        if ai == "01":
            result["gtin"] = val
        elif ai == "10":
            result["batch"] = val
        elif ai == "11":
            result["prod_date"] = format_gs1_date(val) or ""
        elif ai == "17":
            result["expiry_date"] = format_gs1_date(val) or ""
        elif ai == "21":
            result["serial"] = val
    result["ok"] = bool(result["gtin"])


def _parse_segment(seg, result):
    pos = 0
    while pos < len(seg):
        ai, val, new_pos = _match_ai(seg, pos)
        if ai is None:
            break
        _store_ai(ai, val, result)
        pos = new_pos


def _match_ai(seg, pos):
    for length in (3, 2, 4):
        if pos + length > len(seg):
            continue
        ai = seg[pos:pos + length]
        if ai in AI_FIXED_LEN:
            val_len = AI_FIXED_LEN[ai]
            val = seg[pos + length:pos + length + val_len]
            if len(val) == val_len:
                return ai, val, pos + length + val_len
        if ai in AI_VAR_LEN:
            val = seg[pos + length:]
            return ai, val, len(seg)
    for length in (2, 3, 4):
        if pos + length > len(seg):
            continue
        ai = seg[pos:pos + length]
        if ai in AI_VAR_LEN:
            val = seg[pos + length:]
            return ai, val, len(seg)
    return None, None, pos


def _store_ai(ai, val, result):
    if ai == "01":
        result["gtin"] = val
    elif ai == "10":
        result["batch"] = val
    elif ai == "11":
        result["prod_date"] = format_gs1_date(val) or ""
    elif ai == "17":
        result["expiry_date"] = format_gs1_date(val) or ""
    elif ai == "21":
        result["serial"] = val


def _parse_heuristic(s, result):
    pos = 0
    m = re.search(r"01(\d{14})", s)
    if m:
        result["gtin"] = m.group(1)
        pos = m.end()

    rest = s[pos:]

    m = re.search(r"17(\d{6})", rest)
    if m:
        result["expiry_date"] = format_gs1_date(m.group(1)) or ""

    m = re.search(r"11(\d{6})", rest)
    if m:
        result["prod_date"] = format_gs1_date(m.group(1)) or ""

    boundaries = [m.start() for m in re.finditer(r"(?:11\d{6}|17\d{6}|21)", rest)]
    m = re.search(r"10", rest)
    if m:
        batch_start = m.end()
        batch_end = len(rest)
        for b in boundaries:
            if b > batch_start:
                batch_end = b
                break
        result["batch"] = rest[batch_start:batch_end]

    boundaries21 = [m.start() for m in re.finditer(r"(?:10|11\d{6}|17\d{6})", rest)]
    m = re.search(r"21", rest)
    if m:
        serial_start = m.end()
        serial_end = len(rest)
        for b in boundaries21:
            if b > serial_start:
                serial_end = b
                break
        result["serial"] = rest[serial_start:serial_end]


def expand_serial_range(start, end):
    if not start or not end:
        raise ValueError("序列号不能为空")

    if start.isdigit() and end.isdigit():
        s, e = int(start), int(end)
        if s > e:
            raise ValueError("起始序列号不能大于结束序列号")
        count = e - s + 1
        if count > 10000:
            raise ValueError(f"批量数量过大: {count} (上限 10000)")
        width = max(len(start), len(end)) if start.startswith("0") else 0
        if width:
            return [str(i).zfill(width) for i in range(s, e + 1)]
        return [str(i) for i in range(s, e + 1)]

    m_start = re.fullmatch(r"^(.*?)(\d+)$", start)
    m_end = re.fullmatch(r"^(.*?)(\d+)$", end)
    if m_start and m_end and m_start.group(1) == m_end.group(1) and m_start.group(1):
        prefix = m_start.group(1)
        s, e = int(m_start.group(2)), int(m_end.group(2))
        if s > e:
            raise ValueError("起始序列号不能大于结束序列号")
        count = e - s + 1
        if count > 10000:
            raise ValueError(f"批量数量过大: {count} (上限 10000)")
        width = max(len(m_start.group(2)), len(m_end.group(2)))
        return [f"{prefix}{str(i).zfill(width)}" for i in range(s, e + 1)]

    raise ValueError("序列号格式不支持范围展开，需为纯数字或相同前缀+数字后缀")
