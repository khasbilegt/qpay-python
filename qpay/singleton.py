import threading


class Singleton:
    __singleton_instance = None
    __singleton_lock = threading.Lock()

    @classmethod
    def instance(cls):
        if not cls.__singleton_instance:
            with cls.__singleton_lock:
                if not cls.__singleton_instance:
                    cls.__singleton_instance = cls()
        return cls.__singleton_instance
