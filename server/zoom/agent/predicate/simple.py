import logging
from time import sleep
from zoom.common.constants import SENTINEL_METHODS


class SimplePredicate(object):
    def __init__(self, comp_name, operational=False, parent=None):
        """
        :type comp_name: str
        :type operational: bool
        :type parent: str or None
        """
        self._met = None
        self._parent = parent
        self._comp_name = comp_name
        self._operational = operational
        self._callbacks = list()
        self._started = False
        self._log = logging.getLogger('sent.{0}.pred'.format(comp_name))
        self._started = False

    @property
    def met(self):
        return self._met

    @property
    def operationally_relevant(self):
        return self._operational and not self._met

    @property
    def started(self):
        # must be started and the met value must have changed from None
        return self._started and self._met is not None

    def add_callback(self, cb):
        """
        :type cb: dict ({str: types.FunctionType})
        """
        self._callbacks.append(cb)
        self._sort_callbacks()

    def _sort_callbacks(self):
        """
        Sort callbacks based on CALLBACKS dictionary values
        """
        self._callbacks = sorted(self._callbacks,
                                 key=lambda item: [SENTINEL_METHODS.get(k, 99)
                                                   for k in item.keys()])

    def set_met(self, value, silent=False):
        """
        Helper function to set the dependency 'met' value.
        :type value: bool
        :type silent: bool
        """
        if self._met == value:
            if not silent:
                self._log.debug('"Met" value is still {0}. Skipping.'
                                .format(value))
            return

        if not silent:
            self._log.info('Setting "met" attribute from {0} to {1} for {2} '
                           .format(self._met, value, self))
        self._met = value

        for item in self._callbacks:
            for cb in item.values():
                self._log.debug('{0}: About to run callback.'.format(self))
                cb()

    def start(self):
        if self._started is False:
            self._log.debug('Starting {0}'.format(self))
            self._started = True
        else:
            self._log.debug('Already started {0}'.format(self))

    def stop(self):
        if self._started is True:
            self._log.debug('Stopping {0}'.format(self))
            self._started = False
        else:
            self._log.debug('Already stopped {0}'.format(self))

    def reset(self):
        self._log.info('Resetting predicate for {0}'.format(self))
        self._started = False

    def _block_until_started(self, timeout=10):
        counter = 0
        while not self.started and counter < timeout:
            sleep(1)
            self._log.debug('Still starting...')
            counter += 1

    def __repr__(self):
        return ('{0}(component={1}, parent={2}, operational={3}, met={4})'
                .format(self.__class__.__name__,
                        self._comp_name,
                        self._parent,
                        self._operational,
                        self.met)
                )

    def __str__(self):
        return self.__repr__()

    def __eq__(self, other):
        return all([
            type(self) == type(other),
            self._met == other._met,
            self._parent == other._parent,
            self._comp_name == other._comp_name])

    def __ne__(self, other):
        return any([
            type(self) != type(other),
            self._met != other._met,
            self._parent != other._parent,
            self._comp_name != other._comp_name])

    def __hash__(self):
        return hash(self.__repr__())


def create_dummy(comp='', parent=None, met=False):
    """
    Create a SimplePredicate that does nothing.
    :type comp: str
    :type parent: str or None
    :type met: bool
    :rtype: zoom.agent.predicate.simple.SimplePredicate
    """
    dummy = SimplePredicate(comp, parent=parent)
    dummy.set_met(met, silent=True)
    dummy.start()
    return dummy
