import argparse
import xml.etree.ElementTree as ET
import html
import re
import json
from caseconverter import kebabcase


def clean_label(raw):
    # decode HTML entities  (&amp;nbsp; → space, etc.)
    raw = html.unescape(raw)
    # replace >\s*< with > < to handle cases like <b>text</b><i>text</i>
    raw = re.sub(r">\s*<", "> <", raw)
    # strip HTML tags       (<font>, <div>, <span>, etc.)
    raw = re.sub(r"<[^>]+>", "", raw)
    # collapse whitespace   ("Casa  Matriz" → "Casa Matriz")
    raw = re.sub(r"\s+", " ", raw).strip()
    # return clean string
    return raw


def _get_root_ids(diagram):
    """Get only draw.io top containers: root and its direct child(ren)."""
    direct_cells = diagram.findall("./mxGraphModel/root/mxCell")

    # first root cell(s): no parent (usually "0" or "*-0")
    first_level_ids = {
        c.get("id") for c in direct_cells if c.get("parent") is None and c.get("id")
    }

    # second-level containers: parent is a first-level id (usually "1" or "*-1")
    second_level_ids = {
        c.get("id")
        for c in direct_cells
        if c.get("id") and c.get("parent") in first_level_ids
    }

    return first_level_ids | second_level_ids


def _is_group_cell(cell):
    style = cell.get("style", "")
    return re.search(r"(^|;)group(;|$)", style) is not None


def _build_node(node_id, label, geometry, parent, root_ids, is_group=False):
    x = float(geometry.get("x", 0)) if geometry is not None else 0
    y = float(geometry.get("y", 0)) if geometry is not None else 0
    w = float(geometry.get("width", 0)) if geometry is not None else 0
    h = float(geometry.get("height", 0)) if geometry is not None else 0

    node = {
        "id": node_id,
        "data": {"label": label},
        "position": {"x": x, "y": y},
    }

    # React Flow group node
    if is_group:
        node["type"] = "group"
        node["style"] = {"width": w, "height": h}

    # React Flow child node
    if parent and parent not in root_ids:
        node["parentId"] = parent
        node["extent"] = "parent"
        node["expandParent"] = "true"  # ensure group is expanded to show child

    return node


def extract_nodes(diagram):
    """Extract nodes from a draw.io diagram, including group/subflow structure."""
    nodes = []
    wrapped_cells = set()
    root_ids = _get_root_ids(diagram)

    # 1) <object> wrapper + child <mxCell vertex="1">
    for obj in diagram.findall(".//object"):
        cell = obj.find("mxCell[@vertex='1']")
        if cell is None:
            continue

        wrapped_cells.add(id(cell))
        node_id = obj.get("id")
        if not node_id:
            continue

        value = obj.get("label", "")
        label = clean_label(value) if value else ""
        geometry = cell.find("./mxGeometry")
        parent = cell.get("parent")
        is_group = _is_group_cell(cell)

        nodes.append(_build_node(node_id, label, geometry, parent, root_ids, is_group))

    # 2) plain <mxCell vertex="1"> (skip cells already handled via <object>)
    for cell in diagram.findall(".//mxCell[@vertex='1']"):
        if id(cell) in wrapped_cells:
            continue

        node_id = cell.get("id")
        if not node_id:
            continue

        value = cell.get("value")
        label = clean_label(value) if value else ""
        geometry = cell.find("./mxGeometry")
        parent = cell.get("parent")
        is_group = _is_group_cell(cell)

        nodes.append(_build_node(node_id, label, geometry, parent, root_ids, is_group))

    return nodes


def extract_edges(diagram):
    edges = []
    # for each cell where edge="1"
    for cell in diagram.findall(".//mxCell[@edge='1']"):
        # skip if source or target is missing
        source = cell.get("source")
        target = cell.get("target")
        if not source and not target:
            print(
                f"Skipping edge {cell.get('id')} because it has no source and no target"
            )
            continue
        # extract id, source, target
        edge_id = cell.get("id")
        edge = {"id": edge_id, "source": source, "target": target, "type": "smoothstep"}
        # extract style string to get extra data like arrow type
        style_string = cell.get("style", "")
        style_dict = dict(
            item.split("=") for item in style_string.split(";") if "=" in item
        )
        # for now we only care if there are startArrow or endArrow (no type or size)
        if style_dict.get("endArrow"):
            edge["markerEnd"] = {
                "type": "arrowclosed",
                "width": 20,
                "height": 20,
            }
        if style_dict.get("startArrow"):
            edge["markerStart"] = {
                "type": "arrowclosed",
                "width": 20,
                "height": 20,
            }
        # append to edges list
        edges.append(edge)
    # return edges list
    return edges


def parse_drawio_xml(filepath):
    xml_tree = ET.parse(filepath)
    # The root element is <mxfile>, inside it there are <diagram> elements, each with a name attribute (the title)
    root = xml_tree.getroot()
    # for each <diagram> element, add an entry to the result dict with title as key and diagram dict as value
    result = {"diagrams": []}
    for diagram in root.findall(".//diagram"):
        # extract title from name attribute
        title = diagram.get("name")
        id = diagram.get("id")
        url = kebabcase(title)
        print(f"Processing diagram '{title}' with id '{id}' and url '{url}'")
        # call extract_edges() and extract_nodes() to get edges and nodes lists
        nodes = extract_nodes(diagram)
        edges = extract_edges(diagram)
        # build diagram dict { "id": id, "title": title, "url": url, "nodes": [], "edges": [] }
        diagram_dict = {
            "id": id,
            "title": title,
            "url": url,
            "nodes": nodes,
            "edges": edges,
        }
        # add diagram dict to result
        result["diagrams"].append(diagram_dict)
    # return { "diagrams": { title: diagram_dict, ... } }
    return result


def write_json(data, filepath):
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def main(argv=None):
    parser = argparse.ArgumentParser(description="Converts draw.io XML to JSON format for React Flow")
    parser.add_argument("input", help="Draw.io input XML file")
    parser.add_argument(
        "output",
        nargs="?",
        default="out/diagrams.json",
        help="JSON output file (default: out/diagrams.json)",
    )
    args = parser.parse_args(argv)

    data = parse_drawio_xml(args.input)
    write_json(data, args.output)
    print(f"Written {args.output}")
    return 0


if __name__ == "__main__":
    main()
