import logging

from spot.zoom.www.cache.application_state_cache import ApplicationStateCache
from spot.zoom.www.cache.application_dependency_cache \
    import ApplicationDependencyCache
from spot.zoom.www.cache.time_estimate_cache import TimeEstimateCache
from spot.zoom.www.cache.global_cache import GlobalCache
from spot.zoom.common.decorators import connected_with_return
from spot.zoom.www.entities.alert_manager import AlertManager

from spot.zoom.www.messages.application_states import ApplicationStatesMessage
from spot.zoom.www.messages.global_mode_message import GlobalModeMessage
from spot.zoom.www.messages.application_dependencies import ApplicationDependenciesMessage
from spot.zoom.www.messages.timing_estimate import TimeEstimateMessage


class DataStore(object):
    def __init__(self, configuration, zoo_keeper, task_server):
        """
        :type configuration: spot.zoom.config.configuration.Configuration
        :type zoo_keeper: spot.zoom.www.zoo_keeper.ZooKeeper
        :type task_server: spot.zoom.www.entities.task_server.TaskServer
        """
        self._configuration = configuration
        self._zoo_keeper = zoo_keeper
        self._task_server = task_server
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
        logging.info('Starting data store.')
        self._global_cache.start()
        self._application_state_cache.start()
        self._application_dependency_cache.start()
        self._time_estimate_cache.start()
        self._alert_manager.start()

    def stop(self):
        logging.info('Stopping data store.')
        self._global_cache.stop()
        self._application_state_cache.stop()
        self._application_dependency_cache.stop()
        self._time_estimate_cache.stop()
        self._alert_manager.stop()

    @connected_with_return(ApplicationStatesMessage())
    def load_application_state_cache(self):
        """
        :rtype: spot.zoom.messages.application_states.ApplicationStatesMessage
        """
        logging.info('Loading application states.')
        return self._application_state_cache.load()

    @connected_with_return(ApplicationDependenciesMessage())
    def load_application_dependency_cache(self):
        """
        :rtype: spot.zoom.messages.application_dependencies.ApplicationDependenciesMessage
        """
        logging.info('Loading application dependencies.')
        return self._application_dependency_cache.load()

    @connected_with_return(TimeEstimateMessage())
    def load_time_estimate_cache(self):
        """
        :rtype: spot.zoom.messages.timing_estimate.TimeEstimateMessage
        """
        return self._time_estimate_cache.load()

    @connected_with_return(GlobalModeMessage('{"mode":"Unknown"}'))
    def get_global_mode(self):
        """
        :rtype: spot.zoom.messages.global_mode_message.GlobalModeMessage
        """
        logging.info('Loading global mode.')
        return self._global_cache.get_mode()

    def reload(self):
        """
        Clear all cache objects and send reloaded data as updates.
        """
        # restart client to destroy any existing watches
        # self._zoo_keeper.restart()
        logging.info('Reloading all cache types.')
        self._task_server.clear_all_tasks()
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
        logging.info('Loading all cache types.')
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
