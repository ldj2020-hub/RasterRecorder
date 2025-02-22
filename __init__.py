def classFactory(iface):
    from .raster_recorder import RasterRecorderPlugin
    return RasterRecorderPlugin(iface)