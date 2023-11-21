from qgis.core import *
from qgis.gui import *


@qgsfunction(args="auto", group="Custom", referenced_columns=[])
def get_value_color(value: int | float, context: QgsExpressionContext) -> str:
    """Return the symbology color that matches the input value.

    Useful for the QGIS 3D Map feature which requires setting up colors separately from the Symbology of the layer.

    Args:
        value (int | float): Number value to compare against the layer's existing symbology color ranges.
        context (QgsExpressionContext): Auto-populated from decorator. Gives access to various additional
            information like expression variables. E.g. `context.variable( 'layer' )`

    Returns:
        str: RGB color as CSV string.
    """
    renderer = context.variable("layer").renderer()
    for rg in renderer.ranges():
        if not value <= rg.upperValue():
            continue
        return ",".join(map(str, rg.symbol().symbolLayers()[0].color().getRgb()[:-1]))
