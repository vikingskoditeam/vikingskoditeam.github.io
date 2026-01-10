import os
import hashlib
import xml.etree.ElementTree as ET

# =========================
# CONFIGURAÇÃO
# =========================

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
ADDONS_XML = os.path.join(BASE_DIR, "addons.xml")
ADDONS_MD5 = os.path.join(BASE_DIR, "addons.xml.md5")

EXCLUDED_DIRS = {
    ".git",
    ".svn",
    "__pycache__",
    ".idea"
}

# =========================
# FUNÇÕES AUXILIARES
# =========================

def indent(elem, level=0):
    """
    Indentação XML estável e compatível com Kodi.
    Apenas estética — não afeta parsing.
    """
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

# =========================
# GERA addons.xml
# =========================

def generate_addons_file():
    addons_root = ET.Element("addons")
    addons = []

    for entry in os.listdir(BASE_DIR):
        addon_dir = os.path.join(BASE_DIR, entry)

        if not os.path.isdir(addon_dir):
            continue
        if entry in EXCLUDED_DIRS:
            continue

        addon_xml_path = os.path.join(addon_dir, "addon.xml")
        if not os.path.isfile(addon_xml_path):
            continue

        try:
            tree = ET.parse(addon_xml_path)
            addon = tree.getroot()

            if addon.tag != "addon":
                print(f"Ignorado (root inválido): {addon_xml_path}")
                continue

            addons.append(addon)

        except ET.ParseError as e:
            print(f"Erro de XML em {addon_xml_path}: {e}")
        except Exception as e:
            print(f"Erro inesperado em {addon_xml_path}: {e}")

    # 🔤 Ordenação alfabética pelo ID (case-insensitive)
    addons.sort(key=lambda a: a.attrib.get("id", "").lower())

    for addon in addons:
        addons_root.append(addon)

    indent(addons_root)

    tree = ET.ElementTree(addons_root)
    tree.write(
        ADDONS_XML,
        encoding="UTF-8",
        xml_declaration=True
    )

# =========================
# GERA addons.xml.md5
# =========================

def generate_md5_file():
    with open(ADDONS_XML, "rb") as f:
        data = f.read()

    md5_hash = hashlib.md5(data).hexdigest()

    with open(ADDONS_MD5, "w", encoding="utf-8") as f:
        f.write(md5_hash)

# =========================
# MAIN
# =========================

def main():
    generate_addons_file()
    generate_md5_file()
    print("✔ addons.xml e addons.xml.md5 gerados com sucesso")

if __name__ == "__main__":
    main()
