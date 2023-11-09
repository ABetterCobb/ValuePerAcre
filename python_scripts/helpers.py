from qgis.core import *
from qgis.gui import *


def add_legend_commas():
    """Adds comma separators to the legend for easier reading of large numbers.
    Have the layer you want to update already selected."""
    layer = iface.activeLayer()
    renderer = layer.renderer()
    if renderer.type() == "graduatedSymbol":
        myRenderer = renderer.clone()

        for index, data_range in enumerate(myRenderer.ranges()):
            lv = f"${int(data_range.lowerValue()):,}"
            uv = f"${int(data_range.upperValue()):,}"
            myRenderer.updateRangeLabel(index, lv + " - " + uv)
        layer.setRenderer(myRenderer)
        layer.triggerRepaint()


def remove_stroke_lines():
    """Remove stroke lines from all symbology ranges of the active layer."""
    layer = iface.activeLayer()
    renderer = layer.renderer().clone()
    symbol = QgsSymbol.defaultSymbol(layer.geometryType())
    symbol.symbolLayer(0).setStrokeStyle(Qt.PenStyle(Qt.NoPen))
    renderer.updateSymbols(symbol)
    layer.setRenderer(renderer)
    layer.triggerRepaint()


def attribute_percentiles(attribute):
    """Calculate percentiles of attribute. This helps you
    determine a starting point for building color ranges that
    fit your municipality."""
    import pandas as pd

    layer = iface.activeLayer()
    data = [row[attribute] for row in layer.getFeatures() if row[attribute] != NULL]
    series = pd.Series(data)
    quantiles = series.quantile(
        [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 0.95, 0.98, 0.99]
    )
    print(quantiles)
    return quantiles
