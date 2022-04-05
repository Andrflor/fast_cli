import subprocess
import os

from utils import dump_file, load_file


def find(name, path):
    for root, dirs, files in os.walk(path):
        if name in files:
            return os.path.join(root, name)


def find_all(name, path):
    result = []
    for root, dirs, files in os.walk(path):
        if name in files:
            result.append(os.path.join(root, name))
    return result


def getGitRoot():
    return subprocess.Popen(['git', 'rev-parse', '--show-toplevel'], stdout=subprocess.PIPE).communicate()[0].rstrip().decode('utf-8')


def make_translation(key, langs):
    root = getGitRoot()
    yaml_path = find("translations.yaml", os.path.join(root, "assets"))
    dart_path = find("app_translation.dart", os.path.join(root, "lib"))
    yaml_file = load_file(yaml_path, strip=False)
    dart_file = load_file(dart_path, strip=False)

    before = []
    define = []
    after = []
    delimiter = "static String get "
    static_found = False
    for line in dart_file:
        if delimiter in line:
            static_found = True
            define.append(line)
        else:
            if static_found:
                after.append(line)
            else:
                before.append(line)

    define.append("  " + delimiter + key + " => '" + key + "'.tr;")
    define = list(set(define))
    define.sort()
    dart_res = before + define + after
    dump_file(dart_path, "\n".join(dart_res))
    yamlDict = {}
    currentKey = ""
    for line in yaml_file:
        if line[0] != " " and line[0] != "\t":
            currentKey = line.replace(":", "")
            yamlDict[currentKey] = {}
        else:
            lang, tr = line.split(": ")
            lang = lang.replace("\t", "").replace(" ", "")
            yamlDict[currentKey][lang] = tr
    yamlDict[key] = {}
    for lang in langs:
        yamlDict[key][lang] = "\"" + langs[lang] + "\""
    yamlDict = {key: value for key, value in sorted(yamlDict.items())}
    lines = []
    for key in yamlDict:
        lines.append(key+":")
        for k in yamlDict[key]:
            lines.append("  " + k + ": " + yamlDict[key][k])
    dump_file(yaml_path, "\n".join(lines))
