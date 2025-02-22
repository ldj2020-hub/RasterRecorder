from qgis.PyQt.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton,
    QTextEdit, QMessageBox, QFileDialog, QAction
)
from qgis.PyQt.QtCore import Qt
from qgis.gui import QgsMapToolEmitPoint
from qgis.core import (
    QgsProject, QgsRasterLayer, QgsPointXY, QgsRaster,
    QgsCoordinateTransform, QgsCoordinateReferenceSystem
)


class RasterRecorderDialog(QDialog):
    def __init__(self, iface):
        super().__init__()
        self.iface = iface
        self.canvas = iface.mapCanvas()
        self.click_tool = None
        self.values = []  # 存储所有点击的像素值
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("像素值采集工具")
        self.setMinimumSize(500, 400)

        # 控制按钮
        self.btn_start = QPushButton("开始记录")
        self.btn_stop = QPushButton("停止记录")
        self.btn_stop.setEnabled(False)

        # 结果显示区
        self.txt_output = QTextEdit()
        self.txt_output.setReadOnly(True)

        # 主布局
        main_layout = QVBoxLayout()
        btn_layout = QHBoxLayout()
        btn_layout.addWidget(self.btn_start)
        btn_layout.addWidget(self.btn_stop)

        main_layout.addLayout(btn_layout)
        main_layout.addWidget(self.txt_output)
        self.setLayout(main_layout)

        # 信号连接
        self.btn_start.clicked.connect(self.start_recording)
        self.btn_stop.clicked.connect(self.stop_recording)

    def start_recording(self):
        layer = self.iface.activeLayer()
        if not isinstance(layer, QgsRasterLayer):
            QMessageBox.warning(self, "错误", "请先选择栅格图层！")
            return

        self.click_tool = QgsMapToolEmitPoint(self.canvas)
        self.click_tool.canvasClicked.connect(self.record_point)
        self.canvas.setMapTool(self.click_tool)

        self.values = []  # 重置存储
        self.btn_start.setEnabled(False)
        self.btn_stop.setEnabled(True)
        self.txt_output.setText("=== 开始采集 ===")

    def record_point(self, point: QgsPointXY):
        try:
            layer = self.iface.activeLayer()

            # 坐标转换
            canvas_crs = self.canvas.mapSettings().destinationCrs()
            layer_crs = layer.crs()
            transform = QgsCoordinateTransform(canvas_crs, layer_crs, QgsProject.instance())
            transformed_point = transform.transform(point)

            # 获取栅格值
            ident = layer.dataProvider().identify(
                transformed_point,
                QgsRaster.IdentifyFormatValue
            )

            if ident.isValid():
                values = ident.results()

                value = values[1] if values else 0.0
                self.values.append(f"{value}")
                self.txt_output.append(f"坐标({point.x():.2f}, {point.y():.2f}) 值: {value}")

        except Exception as e:
            QMessageBox.critical(self, "错误", str(e))

    def stop_recording(self):
        self.canvas.unsetMapTool(self.click_tool)
        self.btn_start.setEnabled(True)
        self.btn_stop.setEnabled(False)

        # 生成结果字符串
        if self.values:
            result_str = '=' + '+'.join(self.values)
            self.txt_output.append(f"\n=== 最终结果 ===\n{result_str}")
        else:
            self.txt_output.append("\n未采集到有效数据")


class RasterRecorderPlugin:
    def __init__(self, iface):
        self.iface = iface
        self.dialog = None

    def initGui(self):
        self.action = QAction("像素采集工具", self.iface.mainWindow())
        self.action.triggered.connect(self.show_dialog)
        self.iface.addPluginToMenu("&工具", self.action)

    def unload(self):
        self.iface.removePluginMenu("&工具", self.action)
        if self.dialog:
            self.dialog.close()

    def show_dialog(self):
        self.dialog = RasterRecorderDialog(self.iface)
        self.dialog.show()