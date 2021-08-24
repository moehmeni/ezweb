def ok_file_name(string : str):
    # https://stackoverflow.com/a/295152/12696223
    return "".join(l for l in string if l.isalnum())

def create_file(path : str , content : str):
    dot_splited = path.split(".")
    file_name = dot_splited[-2]
    file_extension = dot_splited[-1]
    path = ok_file_name(file_name) + "." + file_extension
    with open(path, mode="w", encoding="utf-8") as f:
        f.write(content)

def read_file(path : str):
    with open(path, mode="r", encoding="utf-8") as f:
        return f.read()