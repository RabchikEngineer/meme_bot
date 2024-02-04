import pathlib,json

#variables
config_path = 'config.json'

with open(config_path, encoding='utf-8') as f:
    conf = json.load(f)

def create_dir(path):
    pathlib.Path(path).mkdir(parents=True, exist_ok=True)

def create_dirs(paths):
    for path in paths:
        create_dir(path)

create_dirs(conf['directories'].values())
