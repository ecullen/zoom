from spot.zoom.www.cache.application_state_cache import ApplicationStateCache
from spot.zoom.www.cache.application_dependency_cache \
    import ApplicationDependencyCache
from spot.zoom.www.cache.time_estimate_cache import TimeEstimateCache
from spot.zoom.www.cache.global_cache import GlobalCache
from spot.zoom.www.entities.alert_manager import AlertManager


class DataStore(object):
    def __init__(self, configuration, zoo_keeper):
        """
        :type configuration: spot.zoom.config.configuration.Configuration
        :type zoo_keeper: spot.zoom.www.zoo_keeper.ZooKeeper
        """
        self._configuration = configuration
        self._zoo_keeper = zoo_keeper
        self._alert_manager = AlertManager(configuration.alert_path, zoo_keeper)

        self._web_socket_clients = list()

        self._time_estimate_cache = TimeEstimateCache(self._configuration,
                                                      self._web_socket_clients)

        self._application_dependency_cache = \
            ApplicationDependencyCache(self._configuration,
                                       self._zoo_keeper,
                                       self._web_socket_clients,
                                       self._time_estimate_cache)

        self._application_state_cache = \
            ApplicationStateCache(self._configuration,
                                  self._zoo_keeper,
                                  self._web_socket_clients,
                                  self._time_estimate_cache)

        self._global_cache = GlobalCache(self._configuration,
                                         self._zoo_keeper,
                                         self._web_socket_clients)

    def start(self):
        self._global_cache.start()
        self._application_state_cache.start()
        self._application_dependency_cache.start()
        self._time_estimate_cache.start()
        self._alert_manager.start()

    def stop(self):
        self._global_cache.stop()
        self._application_state_cache.stop()
        self._application_dependency_cache.stop()
        self._time_estimate_cache.stop()
        self._alert_manager.stop()

    def load_application_state_cache(self):
        """
        :rtype: spot.zoom.messages.application_states.ApplicationStatesMessage
        """
        return self._application_state_cache.load()

    def load_application_dependency_cache(self):
        """
        :rtype: spot.zoom.messages.global_mode_message.ApplicationDependenciesMessage
        """
        return self._application_dependency_cache.load()

    def load_time_estimate_cache(self):
        """
        :rtype: spot.zoom.messages.global_mode_message.TimeEstimateMessage
        """
        return self._time_estimate_cache.load()

    def get_global_mode(self):
        """
        :rtype: spot.zoom.messages.global_mode_message.GlobalModeMessage
        """
        return self._global_cache.get_mode()

    def reload(self):
        """
        Clear all cache objects and send reloaded data as updates.
        """
        # restart client to destroy any existing watches
        # self._zoo_keeper.restart()
        self._global_cache.on_update()
        self._application_state_cache.reload()
        self._application_dependency_cache.reload()
        self._time_estimate_cache.reload()
        self._alert_manager.start()
        return {'cache_clear': 'okay'}

    def load(self):
        """
        Clear all cache objects and send reloaded data as updates.
        """
        self._global_cache.on_update()
        self._application_state_cache.load()
        self._application_dependency_cache.load()
        self._time_estimate_cache.load()
        return {'cache_load': 'okay'}

    @property
    def web_socket_clients(self):
        """
        :rtype: list
        """
        return self._web_socket_clients
