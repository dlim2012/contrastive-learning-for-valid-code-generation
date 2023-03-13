import os

from augment import augment


def apply(path, preserved_names):
    for name in os.listdir(path):
        new_path = os.path.join(path, name)

        if os.path.isdir(new_path):
            apply(new_path, preserved_names)
        elif os.path.isfile(new_path) and len(name) > 2 and name[-3:] == '.py':
            with open(new_path, 'r') as f:
                source = f.read()
            print(new_path)
            fixed, log = augment(source, None, 1, preserved_names)
            print(sorted(log.items()))
            with open(new_path, 'w') as f:
                f.write(fixed)
            print()


if __name__ == "__main__":
    base_dir = '/Users/imjeonghun/Desktop/696ds'

    apply(base_dir, {'augment'})
