from utils import arg_parse
from translate import make_translation


def translate(*args, **kwargs):
    if len(args) < 1:
        print("Make sure to input an <i18nKey>")
        return
    if len(args) > 1:
        print("Make sure to input only one <i18nKey>")
        return
    key = args[0]
    langs = {}
    for k in kwargs:
        if len(kwargs[k]) < 1:
            print("Make sure to input non empty translation")
            return
        if len(kwargs[k]) > 1:
            print("Make sure to input only one translation per key")
            return
        langs[k] = kwargs[k][0]
    make_translation(key, langs)


if __name__ == "__main__":
    cmd_name = "fast"
    commands = {
        "module": {
            "create": ["Create a new fast module", "<name>"],
        },
        "translate": ["Add a translation entry", "<i18nKey>", "[--lang]", "<translation>", translate],
    }
    arg_parse(cmd_name, commands)
