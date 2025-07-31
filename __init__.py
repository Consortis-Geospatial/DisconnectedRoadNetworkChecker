def classFactory(iface):
    from .mainPlugin import DisconnectedRoadCheckerPlugin
    return DisconnectedRoadCheckerPlugin(iface)