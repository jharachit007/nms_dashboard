from xml.etree import ElementTree
from xml.etree.ElementTree import Element


class OpenNMSXMLParseError(Exception):
    """Raised when OpenNMS XML cannot be parsed safely."""


def parse_xml_document(raw_xml: str) -> Element:
    if not raw_xml or not raw_xml.strip():
        raise OpenNMSXMLParseError("OpenNMS XML response is empty")

    try:
        return ElementTree.fromstring(raw_xml)
    except ElementTree.ParseError as exc:
        raise OpenNMSXMLParseError("OpenNMS XML response is invalid") from exc


def local_name(tag: str) -> str:
    if "}" in tag:
        return tag.rsplit("}", 1)[1]
    return tag


def element_to_raw_xml(element: Element) -> str:
    return ElementTree.tostring(element, encoding="unicode")


def element_to_dict(element: Element) -> dict:
    payload: dict = {
        "tag": local_name(element.tag),
    }
    if element.attrib:
        payload["attributes"] = dict(element.attrib)

    text = (element.text or "").strip()
    if text:
        payload["text"] = text

    children: dict[str, list[dict]] = {}
    for child in list(element):
        children.setdefault(local_name(child.tag), []).append(element_to_dict(child))
    if children:
        payload["children"] = children

    return payload


def iter_records(root: Element, record_names: set[str]) -> list[Element]:
    if local_name(root.tag) in record_names:
        return [root]

    direct = [child for child in list(root) if local_name(child.tag) in record_names]
    if direct:
        return direct

    return [
        child
        for child in root.iter()
        if child is not root and local_name(child.tag) in record_names
    ]
