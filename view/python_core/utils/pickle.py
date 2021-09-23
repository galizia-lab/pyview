import pickle


def dump_to_pickle(filename, obj):

    with open(filename, 'wb') as fh:
        pickle.dump(file=fh, obj=obj)


def load_from_pickle(filename):

    with open(filename, 'rb') as fh:
        return pickle.load(file=fh)
