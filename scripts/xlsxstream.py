"""Stream two or three named columns out of a very large .xlsx (first worksheet) without loading it: reads the
shared strings once and walks the sheet XML with iterparse. Far faster than openpyxl for files of 50–100 MB."""
import datetime as dt
import io
import re
import zipfile
import xml.etree.ElementTree as ET

NS = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"
EPOCH = dt.datetime(1899, 12, 30)


def col_of(ref):
    letters = re.match(r"[A-Z]+", ref).group(0)
    n = 0
    for ch in letters:
        n = n * 26 + ord(ch) - 64
    return n - 1


def shared_strings(z):
    try:
        f = z.open("xl/sharedStrings.xml")
    except KeyError:
        return []
    out = []
    for ev, el in ET.iterparse(f, events=("end",)):
        if el.tag == NS + "si":
            out.append("".join(t.text or "" for t in el.iter(NS + "t")))
            el.clear()
    return out


def first_sheet(z):
    names = sorted(n for n in z.namelist() if re.match(r"xl/worksheets/sheet\d+\.xml$", n))
    return names[0]


def rows(data):
    """Yield each row as a dict {column index: value} (strings resolved, numbers as float)."""
    z = zipfile.ZipFile(io.BytesIO(data))
    ss = shared_strings(z)
    for ev, el in ET.iterparse(z.open(first_sheet(z)), events=("end",)):
        if el.tag != NS + "row":
            continue
        row = {}
        for c in el.iter(NS + "c"):
            t, v = c.get("t"), c.find(NS + "v")
            if t == "inlineStr":
                is_ = c.find(NS + "is")
                val = "".join(x.text or "" for x in is_.iter(NS + "t")) if is_ is not None else None
            elif v is None:
                continue
            elif t == "s":
                val = ss[int(v.text)]
            elif t in ("str", "e", "b"):
                val = v.text
            else:
                try:
                    val = float(v.text)
                except (TypeError, ValueError):
                    val = v.text
            row[col_of(c.get("r"))] = val
        yield row
        el.clear()


def to_date(v):
    if isinstance(v, float):
        return EPOCH + dt.timedelta(days=v)
    if isinstance(v, str):
        for fmt in ("%Y-%m-%d", "%m/%d/%Y"):
            try:
                return dt.datetime.strptime(v[:10], fmt)
            except ValueError:
                pass
    return None
