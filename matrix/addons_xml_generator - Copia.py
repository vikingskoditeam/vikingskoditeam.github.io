import os
import sys
import hashlib

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
ADDONS_XML = os.path.join(BASE_DIR, "addons.xml")
ADDONS_MD5 = os.path.join(BASE_DIR, "addons.xml.md5")

def generate_addons_file():
    # Inicia o conteúdo do XML
    addons_xml_content = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n<addons>\n'
    for entry in os.listdir(BASE_DIR):
        full_path = os.path.join(BASE_DIR, entry)
        # Verifica se é pasta válida (exclui .svn, .git e arquivos)
        if os.path.isdir(full_path) and entry not in (".svn", ".git"):
            addon_xml_path = os.path.join(full_path, "addon.xml")
            if os.path.isfile(addon_xml_path):
                try:
                    with open(addon_xml_path, "r", encoding="utf-8") as f:
                        for line in f:
                            # Ignora declaração <?xml ...?>
                            if line.strip().startswith("<?xml"):
                                continue
                            addons_xml_content += line.rstrip() + "\n"
                        addons_xml_content += "\n"
                except Exception as e:
                    print(f"Erro ao ler '{addon_xml_path}': {e}")
                    continue

    # Fecha a tag principal
    addons_xml_content = addons_xml_content.strip() + "\n</addons>\n"

    try:
        with open(ADDONS_XML, "w", encoding="utf-8") as f:
            f.write(addons_xml_content)
    except Exception as e:
        print(f"Erro ao salvar '{ADDONS_XML}': {e}")

def generate_md5_file():
    try:
        with open(ADDONS_XML, "rb") as f:
            data = f.read()
    except Exception as e:
        print(f"Erro ao ler '{ADDONS_XML}' para gerar MD5: {e}")
        return

    md5_hash = hashlib.md5(data).hexdigest()
    try:
        with open(ADDONS_MD5, "w", encoding="utf-8") as f:
            f.write(md5_hash)
    except Exception as e:
        print(f"Erro ao salvar '{ADDONS_MD5}': {e}")

def main():
    generate_addons_file()
    generate_md5_file()
    print("Finished updating addons.xml and addons.xml.md5")

if __name__ == "__main__":
    main()
