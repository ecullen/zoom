import copy
import logging
import os.path
from kazoo.exceptions import NoNodeError

from zoom.agent.predicate.simple import SimplePredicate, create_dummy
from zoom.agent.predicate.zkhas_children \
    import ZookeeperHasChildren
from zoom.common.decorators import connected, catch_exception


class ZookeeperHasGrandChildren(SimplePredicate):
    def __init__(self, comp_name, zkclient, nodepath,
                 ephemeral_only=True, operational=False, parent=None):
        """
        :type comp_name: str
        :type zkclient: kazoo.client.KazooClient
        :type nodepath: str
        :type operational: bool
        :type parent: str or None
        """
        SimplePredicate.__init__(self, comp_name, operational=operational, parent=parent)
        self.node = nodepath
        self.zkclient = zkclient
        self._ephemeral_only = ephemeral_only
        self._children = list()
        self._log = logging.getLogger('sent.{0}.pred.hgc'.format(comp_name))
        self._log.info('Registered {0}'.format(self))

    @property
    def met(self):
        return all([d.met for d in self._children])

    @property
    def operationally_relevant(self):
        return any([d.operationally_relevant for d in self._children])

    @property
    def started(self):
        return all([
            self._started,
            all([d.started for d in self._children])
        ])

    def start(self):
        if not self._started:
            self._log.debug('Starting {0}'.format(self))
            self._started = True
            self._rewalk_tree()
        else:
            self._log.debug('Already started {0}'.format(self))

    def _callback(self):
        # TODO: This is the same logic as in SimplePrecicate.
        # We should change it so that we only have to update in one place
        for item in self._callbacks:
            for cb in item.values():
                self._log.debug('{0}: About to run callback.'.format(self))
                cb()

    @catch_exception(NoNodeError, msg='A node has been removed during walk.')
    @connected
    def _walk(self, node, node_list):
        """
        Recursively walk a ZooKeeper path and add all children to the _children
            list as ZookeeperHasChildren objects.
        :type node: str
        """
        children = self.zkclient.get_children(node)
        if children:
            for c in children:
                path = '/'.join([node, c])
                self._walk(path, node_list)
        else:
            data, stat = self.zkclient.get(node)
            if stat.ephemeralOwner == 0:  # not ephemeral
                node_list.append(node)
            else:
                node_list.append(os.path.dirname(node))

    @connected
    def _rewalk_tree(self, event=None):
        """
        Clear children list and rewalk the tree starting at self.node.
        If the node does not exist, set a watch.
        When the node is created the watch will trigger the recursive walk.
        :type event: kazoo.protocol.states.WatchedEvent or None
        """
        if self.zkclient.exists(self.node, watch=self._rewalk_tree):
            # setting a watch on grandparent node for additional children
            self.zkclient.get_children(self.node, watch=self._rewalk_tree)
            new_nodes = list()
            self._walk(self.node, new_nodes)
            self._update_children_list(new_nodes)
            map(lambda x: x.start(), self._children)
        else:
            # This is a placeholder for when the path the ZKHGC is given a path
            # that doesn't exist
            self._children.append(
                create_dummy(comp=self._comp_name, parent=self._parent))
            self._log.warning('Node {0} does not exist. Will wait until it '
                              'does.'.format(self.node))

    def _update_children_list(self, new_nodes):
        existing = copy.copy(self._children)
        for child in existing:
            if child == create_dummy(comp=self._comp_name, parent=self._parent):
                self._children.remove(child)
            elif child in set(existing) - set(new_nodes):
                self._children.remove(child)

        for node in set(new_nodes) - set(existing):
            zk_child = ZookeeperHasChildren(self._comp_name,
                                            self.zkclient,
                                            node,
                                            met_on_delete=True,
                                            parent='zk.has.gc')
            zk_child.add_callback({"zk_hgc": self._callback})
            self._children.append(zk_child)

    def __repr__(self):
        indent_count = len(self._parent.split('/'))
        indent = '\n' + '    ' * indent_count
        return ('{0}(component={1}, parent={2}, zkpath={3}, started={4}, '
                'ephemeral_only={5} operational={6}, met={7}, group=[{8}{9}])'
                .format(self.__class__.__name__,
                        self._comp_name,
                        self._parent,
                        self.node,
                        self.started,
                        self._ephemeral_only,
                        self._operational,
                        self.met,
                        indent,
                        indent.join([str(x) for x in self._children])))

    def __eq__(self, other):
        return all([
            type(self) == type(other),
            self.node == getattr(other, 'node', None)
        ])

    def __ne__(self, other):
        return any([
            type(self) != type(other),
            self.node != getattr(other, 'node', None)
        ])
