from qpay.singleton import Singleton


def test_singleton_returns_same_instance():
    class Klass(Singleton):
        pass

    assert hasattr(Klass, "instance")
    assert callable(Klass.instance)

    obj1 = Klass.instance()
    assert obj1 == Klass.instance()
    assert obj1 == Klass.instance()
    assert obj1 == Klass.instance()
