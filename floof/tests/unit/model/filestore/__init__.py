import cStringIO
import random
import string


class IntentionalError(Exception): pass


class AlwaysFailDataManager(object):
    def abort(self, transaction): pass
    def tpc_begin(self, transaction): pass
    def commit(self, transaction): pass
    def tpc_finish(self, transaction): pass
    def tpc_abort(self, transaction): pass

    def tpc_vote(self, transaction):
        raise IntentionalError

    def sortKey(self):
        return '~~~~hopefullyLast'


def make_key():
    return u''.join((random.choice(string.hexdigits) for i in xrange(10)))


def storage_put(storage, data=None, class_='artwork'):
    if data is None:
        length = random.choice(range(10, 1000))
        data = ''.join((random.choice(string.printable)
                        for i in xrange(length)))

    data = cStringIO.StringIO(data)
    key = make_key()
    storage.put(class_, key, data)
    data.seek(0)

    return class_, key, data


def storage_put_tester(storage):
    stage_size = len(storage.stage)
    cls, key, data = storage_put(storage)

    # Check that something got inserted into storage.stage
    assert len(storage.stage) == stage_size + 1
    idx = storage._idx(cls, key)
    assert cls in idx
    assert key in idx
    assert idx in storage.stage

    # Check the values of the tuple inserted into storage.stage
    entry = storage.stage[idx]
    assert len(entry) == 3
    c, k, d = entry
    assert c == cls
    assert k == key
    d.seek(0)
    data.seek(0)
    assert d.read() == data.read()
