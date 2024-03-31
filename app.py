import sys
import os
import re
import threading
from http.server import HTTPServer

# import matplotlib.pyplot as plt
from functools import partial
import pydeck as pdk
# from keplergl import KeplerGl

# import PyQt5
from PyQt5.QtWidgets import QGraphicsItem,QApplication,QGraphicsView,QGraphicsPixmapItem, QMainWindow,QGraphicsScene,QVBoxLayout 
from PyQt5.QtGui import QPixmap,QWheelEvent,QPainter
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5 import QtCore

from ui.mainfrm_bak import Ui_MainWindow
from dpio import input
from core.utils import *

class ImageViewer(QGraphicsView):
    """ 图片查看器 """

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.zoomInTimes = 0
        self.maxZoomInTimes = 22

        # 创建场景
        self.graphicsScene = QGraphicsScene()

        # 图片
        self.pixmap = QPixmap("example.jpg")
        self.pixmapItem = QGraphicsPixmapItem(self.pixmap)
        self.displayedImageSize = QtCore.QSize(0, 0)

        # 初始化小部件
        
        self.__initWidget()

    def __initWidget(self):
        """ 初始化小部件 """
        # self.resize(1000,600)
        self.resize(self.parent().width(),self.parent().height())
        # 隐藏滚动条
        self.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)

        # 以鼠标所在位置为锚点进行缩放
        self.setTransformationAnchor(self.AnchorUnderMouse)

        # 平滑缩放
        self.pixmapItem.setTransformationMode(QtCore.Qt.SmoothTransformation)
        self.setRenderHints(QPainter.Antialiasing |
                            QPainter.SmoothPixmapTransform)

        # 设置场景
        self.graphicsScene.addItem(self.pixmapItem)
        self.setScene(self.graphicsScene)

    def wheelEvent(self, e: QWheelEvent):
        """ 滚动鼠标滚轮缩放图片 """
        if e.angleDelta().y() > 0:
            self.zoomIn()
        else:
            self.zoomOut()

    def resizeEvent(self, e):
        """ 缩放图片 """
        super().resizeEvent(e)

        if self.zoomInTimes > 0:
            return

        # 调整图片大小
        ratio = self.__getScaleRatio()
        self.displayedImageSize = self.pixmap.size()*ratio
        if ratio < 1:
            self.fitInView(self.pixmapItem, QtCore.Qt.IgnoreAspectRatio)
        else:
            self.resetTransform()

    def setImage(self, imagePath: str):
        """ 设置显示的图片 """
        self.resetTransform()

        # 刷新图片
        self.pixmap = QPixmap(imagePath)
        self.pixmapItem.setPixmap(self.pixmap)

        # 调整图片大小
        self.setSceneRect(QtCore.QRectF(self.pixmap.rect()))
        ratio = self.__getScaleRatio()
        self.displayedImageSize = self.pixmap.size()*ratio
        if ratio < 1:
            self.fitInView(self.pixmapItem, QtCore.Qt.KeepAspectRatio)

    def resetTransform(self):
        """ 重置变换 """
        super().resetTransform()
        self.zoomInTimes = 0
        self.__setDragEnabled(False)

    def __isEnableDrag(self):
        """ 根据图片的尺寸决定是否启动拖拽功能 """
        v = self.verticalScrollBar().maximum() > 0
        h = self.horizontalScrollBar().maximum() > 0
        return v or h

    def __setDragEnabled(self, isEnabled: bool):
        """ 设置拖拽是否启动 """
        self.setDragMode(
            self.ScrollHandDrag if isEnabled else self.NoDrag)

    def __getScaleRatio(self):
        """ 获取显示的图像和原始图像的缩放比例 """
        if self.pixmap.isNull():
            return 1

        pw = self.pixmap.width()
        ph = self.pixmap.height()
        rw = min(1, self.width()/pw)
        rh = min(1, self.height()/ph)
        return min(rw, rh)

    def fitInView(self, item: QGraphicsItem, mode=QtCore.Qt.KeepAspectRatio):
        """ 缩放场景使其适应窗口大小 """
        super().fitInView(item, mode)
        self.displayedImageSize = self.__getScaleRatio()*self.pixmap.size()
        self.zoomInTimes = 0

    def zoomIn(self, viewAnchor=QGraphicsView.AnchorUnderMouse):
        """ 放大图像 """
        if self.zoomInTimes == self.maxZoomInTimes:
            return

        self.setTransformationAnchor(viewAnchor)

        self.zoomInTimes += 1
        self.scale(1.1, 1.1)
        self.__setDragEnabled(self.__isEnableDrag())

        # 还原 anchor
        self.setTransformationAnchor(self.AnchorUnderMouse)

    def zoomOut(self, viewAnchor=QGraphicsView.AnchorUnderMouse):
        """ 缩小图像 """
        if self.zoomInTimes == 0 and not self.__isEnableDrag():
            return

        self.setTransformationAnchor(viewAnchor)

        self.zoomInTimes -= 1

        # 原始图像的大小
        pw = self.pixmap.width()
        ph = self.pixmap.height()

        # 实际显示的图像宽度
        w = self.displayedImageSize.width()*1.1**self.zoomInTimes
        h = self.displayedImageSize.height()*1.1**self.zoomInTimes

        if pw > self.width() or ph > self.height():
            # 在窗口尺寸小于原始图像时禁止继续缩小图像比窗口还小
            if w <= self.width() and h <= self.height():
                self.fitInView(self.pixmapItem)
            else:
                self.scale(1/1.1, 1/1.1)
        else:
            # 在窗口尺寸大于图像时不允许缩小的比原始图像小
            if w <= pw:
                self.resetTransform()
            else:
                self.scale(1/1.1, 1/1.1)

        self.__setDragEnabled(self.__isEnableDrag())

        # 还原 anchor
        self.setTransformationAnchor(self.AnchorUnderMouse)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.setFixedSize(self.width(),self.height())
        self.read_config('config.ini')
        self.server_address = ('127.0.0.1', 8000)

        self.ui.pushButton.clicked.connect(self.handle_button_click)
        self.ui.comboBox.currentIndexChanged.connect(self.handle_combobox_change)
        self.ui.lineEdit.editingFinished.connect(partial(self.handel_timestamp_input_change,self.ui.lineEdit))
        self.ui.lineEdit_2.editingFinished.connect(partial(self.handel_timestamp_input_change,self.ui.lineEdit_2))

        # self.open_cam_image()
        self.ui.graphicsView = ImageViewer(self.ui.graphicsView)
        # self.ui.graphicsView.fitInView(scene.sceneRect(),mode=QtCore.Qt.IgnoreAspectRatio)
        # self.ui.graphicsView.fitInView(0,0,width/4,height/4, mode=QtCore.Qt.KeepAspectRatio)
        # self.ui.graphicsView.fitInView(rect_item, mode = QtCore.Qt.IgnoreAspectRatio)

        #WebEngineWidgets
        self.web_view = QWebEngineView()
        # self.visualize_feature("https://raw.githubusercontent.com/visgl/deck.gl-data/master/examples/geojson/vancouver-blocks.json")
        # self.visualize_feature("F:\BaiduSyncdisk\workspace\py\data_playerslice.json")
        
        file_server_thread = threading.Thread(target=self.run_file_server)
        file_server_thread.start()

        target_geojson_file = "slice.geojson"
        file_server_address  =self.server_address
        self.visualize_feature("http://127.0.0.1:8000/slice.geojson")
        # self.visualize_feature("https://raw.githubusercontent.com/visgl/deck.gl-data/master/examples/geojson/vancouver-blocks.json")
        
        layout = QVBoxLayout()
        layout.addWidget(self.web_view)
        self.ui.frame.setLayout(layout)

    def read_config(self,_path):
        feature_file_path,location_file_path,vision_file_path = input.read_config_file(_path)
        self.feature_file_path = feature_file_path
        self.location_file_path = location_file_path
        self.vision_file_path = vision_file_path

        # set the combox item of routes
        routes = os.listdir(feature_file_path)
        route_alias_pattern = r'^[a-zA-Z]+\d+$'  # 匹配以字母开头，后跟数字的命名格式 
        
        for route in routes:
            if re.match(route_alias_pattern,route):
                self.ui.comboBox.addItem(route)
        
    
        
    # widgets binding
    def handle_combobox_change(self, index):
        selected_text = self.ui.comboBox.currentText()
        current_target_feature_file_path = os.path.join(self.feature_file_path,selected_text)
        
        self.ui.comboBox_2.clear()
        pattern_data = r'^\d{4}-\d{2}-\d{2}$'
        for _date in os.listdir(current_target_feature_file_path):
            if re.match(pattern_data,_date):
                self.ui.comboBox_2.addItem(_date)

    def handel_timestamp_input_change(self,lineEditItem):
        text = lineEditItem.text()
        tsp = TimeStampProcessor()
        text = tsp.check_timestamp_format(text)
        text2show = tsp.trans_timestamp_to_general_format(text)
        if lineEditItem == self.ui.lineEdit:
            self.ui.label_5.setText(text2show) 
        elif lineEditItem == self.ui.lineEdit_2:
            self.ui.label_6.setText(text2show)
    
        mPeriod = Period(self.ui.lineEdit.text(),self.ui.lineEdit_2.text())
        time_span = tsp.calculate_time_interval(mPeriod)
        self.ui.label_7.setText(time_span)

    def handle_button_click(self):
        mPeriod = Period('1690353405','1690353415')

        mTSP = TimeStampProcessor()
        mPeriod = mTSP.check_period(mPeriod)
        # mTSP.get_raw_data_package_timestamp('C385_505442_2023-07-25_14-29-37.csv')

        # get the vec \ loc \ vis files during the target period
        mDataFilter = DataFilter(mPeriod)
        selected_route = self.ui.comboBox.currentText()
        selected_date = self.ui.comboBox_2.currentText()
        _ = os.path.join(self.feature_file_path,selected_route)
        __vec_path = os.path.join(_,selected_date)
        select_file = mDataFilter.search_vec_data(__vec_path,mPeriod)
        self.ui.textBrowser.setText(select_file.__str__())
        # self.ui.plainTextEdit.setText(select_file.__str__())


        # print(mPeriod.end_time)
        # print(self.feature_file_path)

    def visualize_feature(self,target_geojson):
        host, port = self.server_address
        url = "http://{}:{}".format(host, port)

        layer = pdk.Layer(
            'GeoJsonLayer',
            target_geojson,
            opacity=0.8,
            stroked=True,
            filled=True,
            extruded=True,
            wireframe=True,
            get_elevation='properties.valuePerSqm / 20',
            get_fill_color='[255, 255, 255, 255]',
            get_line_color=[255, 255, 255],
        )

        view_state = pdk.ViewState(
            latitude=29.662,
            longitude=106.757,
            zoom=17,
            bearing=0,
            pitch=0,
        )
        deck = pdk.Deck(layers=[layer], initial_view_state=view_state)

        html = deck.to_html('demo.html',open_browser=False)
        with open("demo.html", "r") as file:
            html_string = file.read()
        self.web_view.setHtml(html_string)
    def run_file_server(self):
        with HTTPServer(self.server_address, DP_GeoJSONHandler) as httpd:
            print('Server running at localhost:8000...')
            httpd.serve_forever()
    
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())