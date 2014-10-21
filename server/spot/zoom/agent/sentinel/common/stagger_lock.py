import logging
import platform
import time
from threading import Thread

from kazoo.client import KazooClient, KazooState
from kazoo.exceptions import LockTimeout

from spot.zoom.common.constants import ZK_CONN_STRING


class StaggerLock(object):
    def __init__(self, temp_path, timeout, parent='None', acquire_lock=None):
        """
        :type temp_path: str
        :type timeout: int
        """
        self._path = temp_path
        self._timeout = timeout
        self._parent = parent
        self._thread = None
        self._prev_state = None
        self._zk = KazooClient(hosts=ZK_CONN_STRING)
        self._zk.add_listener(self._zk_listener)
        self._log = logging.getLogger('sent.{0}.sl'.format(parent))
        self._counter = 0
        self._acquire_lock = acquire_lock

    def join(self):
        try:
            if self._thread is not None and self._zk.connected():
                self._thread.join()
                self._zk.stop()
                self._zk.close()
                self._thread = None
            else:
                return
        except TypeError as e:
            self._log.info('### join {0}'.format(e))
        except Exception as e:
            self._log.info('### some exception: {0}'.format(e))

    def start(self):
        """
        This method is to implement a staggered startup.
        A new KazooClient is instantiated b/c of thread-safety issues with the
        election.
        """
        self._zk.start()
        self._acquire()
        self._log.info('### Passing Acquire')

    def _acquire(self):
        try:
            self._log.info('### acquire_lock value: {0}'.format(self._acquire_lock.value))
            lock = self._zk.Lock(self._path, identifier=platform.node())
            while self._acquire_lock.value:
                if lock.acquire(blocking=True, timeout=5):
                    self._log.info('### Got that lock')
                    self._thread = Thread(target=self._sleep_and_unlock,
                                          args=(lock,),
                                          name=str(self))
                    self._thread.daemon = True
                    self._thread.start()
                    break
                else:
                    self._log.info("In the else of self.acquire()")

        except LockTimeout as e:
            self._log.info('###Lock timed out. Re-running Acquire')
            self._acquire()

    def _sleep_and_unlock(self, lck):
        self._log.info('Got stagger lock. Sleeping for {0} seconds.'
                       .format(self._timeout))
        time.sleep(self._timeout)
        lck.release()
        self._log.info('Released stagger lock.')

    def _reset_after_connection_loss(self):
        try:
            self._log.info("### ZK Connection about to Close")
            self._thread = None
            self._acquire_lock.set_value(False)
            self._zk.stop()
            self._zk.close()

        except TypeError as e:
            self._log.info('### {0}'.format(e))
        except Exception as e:
            self._log.info('### some exception: {0}'.format(e))


    def _zk_listener(self, state):
        """
        The callback function that runs when the connection state to Zookeeper
        changes.
        Either passes or immediately spawns a new thread that resets any
        watches, etc., so that it can listen to future connection state changes.
        """
        try:
            self._log.info('###Zookeeper Connection went from {0} to {1}'
                           .format(self._prev_state, state))
            if self._prev_state is None and state == KazooState.CONNECTED:
                pass
            elif (self._prev_state == KazooState.LOST
                  and state == KazooState.CONNECTED):
                self._zk.handler.spawn(self._reset_after_connection_loss)
            elif (self._prev_state == KazooState.CONNECTED
                  and state == KazooState.SUSPENDED):
                self._zk.handler.spawn(self._reset_after_connection_loss)
            elif (self._prev_state == KazooState.CONNECTED
                  and state == KazooState.LOST):
                self._zk.handler.spawn(self._reset_after_connection_loss)
            elif (self._prev_state == KazooState.SUSPENDED
                  and state == KazooState.LOST):
                self._zk.handler.spawn(self._reset_after_connection_loss)
            elif (self._prev_state == KazooState.SUSPENDED
                  and state == KazooState.CONNECTED):
                self._zk.handler.spawn(self._reset_after_connection_loss)
            elif state == KazooState.CONNECTED:
                self._zk.handler.spawn(self._reset_after_connection_loss)
            else:
                self._log.info('Zookeeper Connection in unknown state: {0}'
                               .format(state))
                return
            self._prev_state = state

        except Exception:
            self._log.exception('An uncaught exception has occurred')

    def __repr__(self):
        return 'StaggerLock(path={0}, timeout={1})'.format(self._path,
                                                           self._timeout)

    def __str__(self):
        return self.__repr__()