import threading


class Singleton:
    __singleton_instance = None
    __singleton_lock = threading.Lock()

    @classmethod
    def instance(cls, *args, **kwargs):
        if not cls.__singleton_instance:
            with cls.__singleton_lock:
                if not cls.__singleton_instance:
                    cls.__singleton_instance = cls(*args, **kwargs)
        return cls.__singleton_instance
