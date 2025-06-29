import sys
from pathlib import Path
import pandas as pd
import networkx as nx
import xml.etree.ElementTree as ET


def indent(elem, level=0):
    i = "\n" + level * "  "
    if len(elem):
        if not elem.text or not elem.text.strip():
            elem.text = i + "  "
        for child in elem:
            indent(child, level + 1)
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
    else:
        if level and (not elem.tail or not elem.tail.strip()):
            elem.tail = i


# ------------------------------------------------------------------------------
# Optional flag: --deps-first
#
# When this flag is used, the script will order mods so that all mods which are
# used as dependencies by other mods are listed FIRST in the output XML.
#
# Default behavior (without the flag) uses topological sorting to ensure that
# any mod appears BEFORE the mods it depends on. This is ideal for systems that
# require dependency order to be respected.
#
# Example usage:
#   python csv_to_mods_xml.py mods.csv mods.xml # normal mode (orders Deps last)
#   python csv_to_mods_xml.py mods.csv mods.xml --deps-first  # dependency-first mode
# ------------------------------------------------------------------------------


# --------------------------------------------------------------------------- #
# 1. Parse args
# --------------------------------------------------------------------------- #
if len(sys.argv) < 3:
    sys.exit("Usage: python csv_to_mods_xml.py input.csv output.xml [--deps-first]")

csv_path = Path(sys.argv[1])
xml_path = Path(sys.argv[2])
use_deps_first = "--deps-first" in sys.argv

# --------------------------------------------------------------------------- #
# 2. Load CSV
# --------------------------------------------------------------------------- #
df = pd.read_csv(csv_path)

df["PublishedFileId"] = df["PublishedFileId"].astype(str).str.replace(r"\.0$", "", regex=True)
row_by_id = {row["PublishedFileId"]: row for _, row in df.iterrows()}
dep_cols = [c for c in df.columns if c.lower().startswith("dependency")]

# --------------------------------------------------------------------------- #
# 3. Build dependency graph + find missing dependencies
# --------------------------------------------------------------------------- #
G = nx.DiGraph()
G.add_nodes_from(row_by_id)

missing_deps = set()

for _, row in df.iterrows():
    src_id = row["PublishedFileId"]
    deps = {
        str(int(d)) if pd.notna(d) else None
        for d in row[dep_cols]
    }
    deps.discard(None)

    for dep_id in deps:
        if dep_id not in row_by_id:
            missing_deps.add(dep_id)
            G.add_node(dep_id)
        G.add_edge(src_id, dep_id)

if missing_deps:
    sys.exit(f"Error – the following dependency IDs are missing from the CSV: {', '.join(sorted(missing_deps))}")

# --------------------------------------------------------------------------- #
# 4. Determine final order
# --------------------------------------------------------------------------- #
if use_deps_first:
    print("Using dependency-first ordering...")
    df["IsDependency"] = df["PublishedFileId"].apply(
        lambda mod_id: any(mod_id in str(row[dep_cols].values) for _, row in df.iterrows())
    )
    df_sorted = (
        df.sort_values(by=["IsDependency", "FriendlyName"], ascending=[False, True])
        .drop_duplicates(subset="PublishedFileId")
        .reset_index(drop=True)
    )
    ordered_rows = df_sorted.to_dict(orient="records")

else:
    print("Using topological order (mods before dependencies)...")
    try:
        ordered_ids = list(nx.topological_sort(G))
    except nx.NetworkXUnfeasible:
        cycles = list(nx.simple_cycles(G))
        sys.exit(f"Error – circular dependencies found: {cycles}")

    ordered_rows = [row_by_id[mod_id] for mod_id in ordered_ids if mod_id in row_by_id]

# --------------------------------------------------------------------------- #
# 5. Build XML (with better formatting)
# --------------------------------------------------------------------------- #
def indent(elem, level=0):
    """Recursively pretty-print XML with correct closing tag indentation."""
    i = "\n" + "  " * level
    if len(elem):
        if not elem.text or not elem.text.strip():
            elem.text = i + "  "
        for child in elem:
            indent(child, level + 1)
        if not elem[-1].tail or not elem[-1].tail.strip():
            elem[-1].tail = i
    if level and (not elem.tail or not elem.tail.strip()):
        elem.tail = i

mods_el = ET.Element("Mods")

# For dependency marking in topological mode
is_dep_lookup = {
    mod_id: any(G.predecessors(mod_id)) for mod_id in G.nodes
}

for row in ordered_rows:
    mod_id = row["PublishedFileId"]
    item = ET.SubElement(mods_el, "ModItem", {
        "FriendlyName": row["FriendlyName"]
    })

    ET.SubElement(item, "Name").text = f"{mod_id}.sbm"
    ET.SubElement(item, "PublishedFileId").text = mod_id
    ET.SubElement(item, "PublishedServiceName").text = "Steam"

    if use_deps_first:
        if row.get("IsDependency"):
            ET.SubElement(item, "IsDependency").text = "true"
    else:
        if is_dep_lookup.get(mod_id):
            ET.SubElement(item, "IsDependency").text = "true"

indent(mods_el)

# --------------------------------------------------------------------------- #
# 6. Write XML to file with no trailing newline
# --------------------------------------------------------------------------- #
from xml.dom import minidom

xml_string = ET.tostring(mods_el, encoding="utf-8")
parsed = minidom.parseString(xml_string)
pretty = parsed.toprettyxml(indent="  ")

# Remove extra newline at the end
final = "\n".join(line for line in pretty.splitlines() if line.strip())

with open(xml_path, "w", encoding="utf-8") as f:
    f.write(final)

print(f"✅ Wrote XML to: {xml_path.resolve()}")
