from PyQt5.QtWidgets import QWidget,QVBoxLayout
from PyQt5.QtCore import QTimer
from traits.api import *
from traitsui.api import *
from tvtk.api import tvtk
from tvtk.pyface.scene_editor import SceneEditor
from tvtk.pyface.scene import Scene
from tvtk.pyface.scene_model import SceneModel
import numpy as np
from tvtk.api import tvtk
from Algorithm import *
from DataStructure import *

class TVTKViewer(HasTraits):

    scene = Instance(SceneModel, ())  # SceneModel表示TVTK的场景模型

    # 建立视图布局
    view = View(
                Item(name = 'scene',
                     editor=SceneEditor(scene_class=Scene),  # 设置mayavi的编辑器，让它能正确显示scene所代表的模型
                     resizable=True,
                     ),
        resizable=True
    )

class TVTKQWidget(QWidget):
    def __init__(self, x, y, z, parent=None):
        QWidget.__init__(self, parent)
        layout = QVBoxLayout(self)  # 定义布局
        self.viewer = TVTKViewer()  # 定义TVTK界面对象
        ui = self.viewer.edit_traits(parent=self, kind='subpanel').control  # 使TVTK界面对象可以被调用
        layout.addWidget(ui)  # 将TVTK界面对象放到布局中

        self.x = x
        self.y = y
        self.z = z
        self.plot()  # 绘制三角网
        self.contour_num = 0  # 等间距等值线数目
        self.custom_contour = [0]  # 自定义等值线列表
        self.contour_value = np.append(
            np.linspace((self.z.max() - self.z.min()) / (self.contour_num + 1), self.z.max(), self.contour_num,
                        endpoint=False), np.array(self.custom_contour))
        self.flag_init()  # 对flag进行初始化，行数为等高线高程值列表的长度，列数为三角网格的数目
        self.points = []  # 平面等高线线段实体 self.actor_contour 的几何结构, 为二维列表
        self.points_ = []  # 立体等高线线段实体 self.actor_contour_ 的几何结构, 为二维列表
        self.lines = []  # 水平及立体等高线线段的拓扑结构，为二维列表，例如 slef.lines[0]存储第一条平面等高线线段的起点到终点在self.points中的编号
        self.contour_value_cur = 0  # 当前访问的等高线高程值在等高线高程值列表中的索引
        self.triangle_base = 0  # 当前等高线的第一个访问的三角形在三角形列表中的索引，可以理解为"根"或者"stem"
        self.triangle_leaf = -1  # 若等高线的第一个访问的三角形不是等高线的端点或者该等高线封闭，则存储另一个"枝叶"访问方向
        self.triangle_cur = 0  # 记录当前高程值下,当前访问三角形在三角形列表中的索引
        self.timer = QTimer()  # 定义计时器，来自QtCore
        self.timerID = self.timer.start(200)  # 每隔 200ms(0.2s)发送一个触发信号
        self.timer.timeout.connect(self.find_next_lineSlot)  # 每隔0.2秒触发一次self.find_next_lineSlot,注意这里不带括号

    def plot(self):
        '''
        使用Delaunay算法绘制三角网;
        实现对self.x进行从小到大排序以减小运算时间复杂度；
        将三角形从triangle_buffer转移到triangle_list进行判断：如果该三角形不包含大三角形的顶点则可以加入，否则丢弃，这样避免后续的删除三角形操作；
        在向triangle_list中加入三角形的同时将三个顶点的关联三角形在triangle_list中的序号存入以方便后续查找相邻三角形
        '''
        zmax = max(self.z)
        zmin = min(self.z)

        points = np.vstack([self.x, self.y, self.z]).T
        self.triangle_list = Delaunay(points)
        Triangles = List2Triangles(self.triangle_list)
        # Triangles = [[0, 2, 3], [0, 1, 3], [3, 5, 6], [3, 4, 6], [2, 3, 4], [1, 3, 5]]

        vertices = []
        for i in range(len(points)):
            vertices.append([i])
        # polyData = tvtk.PolyData(points=points_painter, polys=Triangles)
        polyData = tvtk.PolyData(points = points, verts = vertices, polys=Triangles)

        polyData.point_data.scalars = 1 + ( -1 ) * self.z

        polyDataMapper = tvtk.PolyDataMapper()
        polyDataMapper.set_input_data(polyData)
        polyDataMapper.scalar_range = (zmin, zmax)
        # 三角网格
        self.actor_tri = tvtk.Actor(mapper=polyDataMapper)
        self.actor_tri.property.representation = "w"
        self.actor_tri.property.point_size = 3
        self.viewer.scene.add_actor(self.actor_tri)
        # 水平面
        points_ = np.vstack([self.x, self.y, np.zeros(len(self.x))]).T
        polyData_ = tvtk.PolyData(points = points_, polys = Triangles)
        polyDataMapper_ = tvtk.PolyDataMapper()
        polyDataMapper_.set_input_data(polyData_)
        polyDataMapper_.scalar_range = (0, 0)
        self.actor_horizon = tvtk.Actor(mapper=polyDataMapper_)
        self.actor_horizon.property.color = (1, 1, 1)
        self.viewer.scene.add_actor(self.actor_horizon)

        self.viewer.scene.render()

    def update_actor_contour(self, line):
        '''
        @param: line: 等高线线段
        该函数根据新生成的等高线线段对场景中的actor_
        contour实体进行更新并且传回新创建的实体
        '''
        self.points.append([line.BeginPoint.X, line.BeginPoint.Y, 0])
        self.points.append([line.EndPoint.X, line.EndPoint.Y, 0])
        self.points_.append([line.BeginPoint.X, line.BeginPoint.Y, line.BeginPoint.Z])
        self.points_.append([line.EndPoint.X, line.EndPoint.Y, line.EndPoint.Z])
        temp = int(len(self.points)) - 2
        self.lines.append([temp, temp+1])
        # 水平等高线
        polyData = tvtk.PolyData(points=self.points, lines=self.lines)
        polyDataMapper = tvtk.PolyDataMapper()
        polyDataMapper.set_input_data(polyData)
        actor_contour = tvtk.Actor(mapper=polyDataMapper)
        actor_contour.property.color = (0, 0, 0)
        actor_contour.property.line_width = 4.0
        # 立体等高线
        polyData_ = tvtk.PolyData(points=self.points_, lines=self.lines)
        polyDataMapper_ = tvtk.PolyDataMapper()
        polyDataMapper_.set_input_data(polyData_)
        actor_contour_ = tvtk.Actor(mapper=polyDataMapper_)
        actor_contour_.property.color = (1, 0, 0)
        actor_contour_.property.line_width = 2.0
        return actor_contour, actor_contour_

    def point_inline(self, p1, p2, z):
        '''
        根据p1,p2的z值和等值线的高度，按比例在p1,p2之间插入一等值线端点p
        :param p1: Point类型（自定义数据类型，详见DataStructure_contour.py）
        :param p2: Point类型（自定义数据类型，详见DataStructure_contour.py）
        :param z: 某一级等值线的高度值
        :return: 返回插入的点p,p也为Point类型
        '''
        x1 = p1.X
        y1 = p1.Y
        z1 = p1.Z

        x2 = p2.X
        y2 = p2.Y
        z2 = p2.Z

        zp = z
        ratio = (zp - z1) / (z2 - z1)
        xp = x1 + ratio * (x2 - x1)
        yp = y1 + ratio * (y2 - y1)
        p = Point(0, xp, yp, zp, [])
        return p

    def flag_init(self):
        '''
        确定contour_value后对self.flag进行初始化;
        对三角形列表与所有等高线的高程值进行遍历，如果该三角形和该等高面相交则flag标记为1，否则标记为0;
        这一步可以去掉，但是提前将不与等高面相交的三角形标记为已经访问可以有效降低运算时间.
        '''
        self.flag = []
        m = len(self.contour_value)
        n = len(self.triangle_list)
        for i in range(m):
            temp = []
            for j in range(n):
                bool_1 = self.triangle_list[j].point0.Z > self.contour_value[i] and self.triangle_list[j].point1.Z > self.contour_value[i] and self.triangle_list[j].point2.Z > self.contour_value[i]
                bool_2 = self.triangle_list[j].point0.Z <= self.contour_value[i] and self.triangle_list[j].point1.Z <= self.contour_value[i] and self.triangle_list[j].point2.Z <= self.contour_value[i]

                if bool_1 or bool_2:
                    temp.append(0)
                else:
                    temp.append(1)

            self.flag.append(temp)

    def next_Index(self, pointa, pointb, contour_value_cur, triangle_cur):
        '''
        @param: pointa: 三角形某条边的一个端点
        @param: pointb: 三角形该条边的另一个端点
        @param: contour_value_cur: 当前的等高线的高程值
        @param: triangle_cur: 当前三角形的在三角形列表中的序号
        return: 当前三角形的相邻三角形的序号(如果该三角形没有空间相邻三角形或者空间相邻三角形已经被访问过，则返回None)
        '''
        a = pointa.ADJTriangle_list
        b = pointb.ADJTriangle_list
        c = list(set(a).intersection(set(b)))  # len(c) =1 or len(c) = 2
        c.remove(triangle_cur)  # c=[]    或者    c等于相邻下一个三角形的编号且长度为 1
        if c == [] or self.flag[contour_value_cur][c[0]] == 0:
            return None
        else:
            return c[0]

    def judge_Triangle(self, contour_value_cur, triangle_cur):
        '''
        @param: contour_value_cur: 当前等高线的高程值
        @param: triangle_cur: 待判断三角形在三角形列表中的编号
        return: line: 待判断三角形内部的等高线线段
        return: nextIndex1: 待判断三角形的相邻三角形序号(如果待判断三角形有相邻三角形并且该三角形没有被访问过则返回值， 否则返回None)
        return: nextIndex2: 待判断三角形的另一个方向的相邻三角形序号
        '''

        z = self.contour_value[contour_value_cur]
        triangle = self.triangle_list[triangle_cur]

        if triangle.point0.Z > z:
            if triangle.point1.Z > z:
                if triangle.point2.Z > z:  # 该种情况不会出现
                    pass
                else:
                    pointa = self.point_inline(triangle.point0, triangle.point2, z)
                    pointb = self.point_inline(triangle.point1, triangle.point2, z)
                    line = Line(pointa, pointb)
                    nextIndex1 = self.next_Index(triangle.point0, triangle.point2, contour_value_cur, triangle_cur)
                    nextIndex2 = self.next_Index(triangle.point1, triangle.point2, contour_value_cur, triangle_cur)
                    return line, nextIndex1, nextIndex2
            else:
                if triangle.point2.Z > z:
                    pointa = self.point_inline(triangle.point0, triangle.point1, z)
                    pointb = self.point_inline(triangle.point2, triangle.point1, z)
                    line = Line(pointa, pointb)
                    nextIndex1 = self.next_Index(triangle.point0, triangle.point1, contour_value_cur, triangle_cur)
                    nextIndex2 = self.next_Index(triangle.point2, triangle.point1, contour_value_cur, triangle_cur)
                    return line, nextIndex1, nextIndex2
                else:
                    pointa = self.point_inline(triangle.point1, triangle.point0, z)
                    pointb = self.point_inline(triangle.point2, triangle.point0, z)
                    line = Line(pointa, pointb)
                    nextIndex1 = self.next_Index(triangle.point1, triangle.point0, contour_value_cur, triangle_cur)
                    nextIndex2 = self.next_Index(triangle.point2, triangle.point0, contour_value_cur, triangle_cur)
                    return line, nextIndex1, nextIndex2
        else:
            if triangle.point1.Z > z:
                if triangle.point2.Z > z:
                    pointa = self.point_inline(triangle.point1, triangle.point0, z)
                    pointb = self.point_inline(triangle.point2, triangle.point0, z)
                    line = Line(pointa, pointb)
                    nextIndex1 = self.next_Index(triangle.point1, triangle.point0, contour_value_cur, triangle_cur)
                    nextIndex2 = self.next_Index(triangle.point2, triangle.point0, contour_value_cur, triangle_cur)
                    return line, nextIndex1, nextIndex2
                else:
                    pointa = self.point_inline(triangle.point0, triangle.point1, z)
                    pointb = self.point_inline(triangle.point2, triangle.point1, z)
                    line = Line(pointa, pointb)
                    nextIndex1 = self.next_Index(triangle.point0, triangle.point1, contour_value_cur, triangle_cur)
                    nextIndex2 = self.next_Index(triangle.point2, triangle.point1, contour_value_cur, triangle_cur)
                    return line, nextIndex1, nextIndex2
            else:
                if triangle.point2.Z > z:
                    pointa = self.point_inline(triangle.point0, triangle.point2, z)
                    pointb = self.point_inline(triangle.point1, triangle.point2, z)
                    line = Line(pointa, pointb)
                    nextIndex1 = self.next_Index(triangle.point0, triangle.point2, contour_value_cur, triangle_cur)
                    nextIndex2 = self.next_Index(triangle.point1, triangle.point2, contour_value_cur, triangle_cur)
                    return line, nextIndex1, nextIndex2
                else:  # 该种情况不会出现
                    pass

    def find_next_lineSlot(self):
        '''
        每隔一段时间自动追踪下一条等高线段
        '''
        new_line = None  # 初始化新创建的等高线线段
        label = 0  # 如果可以在循环结束之前找到新的等高线线段则label被置为1且立即跳出循环
        while self.contour_value_cur < len(self.contour_value):
            # 这里self.contour_value_cur在下一次进入该函数仍会接着上一次执行位置的下一步来开始
            while self.triangle_cur < len(self.triangle_list):
                # self.triangle_cur表示当前访问的三角形序号，更改后也会保存
                if self.flag[self.contour_value_cur][self.triangle_cur] != 0:
                    self.flag[self.contour_value_cur][self.triangle_cur] = 0  # 下次不要访问我了
                    # 下面这一句传回该三角形包围的等高线线段 line, 以及两个相邻三角形索引(不存在就返回None)
                    new_line, nextIndex1, nextIndex2 = self.judge_Triangle(self.contour_value_cur, self.triangle_cur)
                    if nextIndex1 == None:
                        if nextIndex2 == None:
                            # 此处表示访问到这条等高线的一个尽头
                            if self.triangle_leaf != -1 and self.flag[self.contour_value_cur][self.triangle_leaf] != 0:
                                self.triangle_cur = self.triangle_leaf  #如果这条等高线还有一部分没有被访问就去访问 leaf
                                self.triangle_leaf = -1  # -1只是表示他已经被用过一次了，下一次不要再用 leaf
                            else:
                                self.triangle_base += 1  # 这条等高线已经追踪完毕，马上去找下一条
                                self.triangle_cur = self.triangle_base
                        else:
                            self.triangle_cur = nextIndex2 # 单向行驶，没有顾虑
                    else:
                        if nextIndex2 == None:
                            self.triangle_cur = nextIndex1 # 单向行驶，没有顾虑
                        else:
                            self.triangle_leaf = nextIndex1 # 访问到一条新的等高线的"腰部"
                            self.triangle_cur = nextIndex2  # 先随便找一个方向去追踪，追踪完了再去另一头 leaf

                    label = 1  # 在循环结束之前找到新的等高线线段，那么就标志一下
                    break  # 跳出第一层循环
                else:  # 该三角网格内部没有等高线段，去找下一条等高线
                    self.triangle_base += 1
                    self.triangle_cur = self.triangle_base
            if label == 0:  # 代表这一层楼(等高面)已经被全部访问了，接下来更上一层楼
                self.contour_value_cur += 1  # 上楼之前把参数恢复到初始状态
                self.triangle_base = 0
                self.triangle_leaf = -1
                self.triangle_cur = 0
            else: # label == 1
                break # 在循环结束之前找到新的等高线线段，跳出第二层循环

        if label == 0:
            pass  # 没有等高线线段可以被找到，接下来什么也不用干，此处甚至可以关掉"闹钟" self.timer
        else:  # label ==1 有一条新的等高线线段生成，接下来对等高线实体进行更新
            if "actor_contour" in dir(self):
                self.viewer.scene.remove_actor(self.actor_contour)  # 如果原来有平面等高线实体就移除
                self.viewer.scene.remove_actor(self.actor_contour_)  # 如果原来有立体等高线实体就移除
                del self.actor_contour  # 删除self.actor_contour
                del self.actor_contour_  # 删除self.actor_contour_
            else:
                pass
            #update_actor_contour函数是自定义的，表示更新等高线实体
            self.actor_contour, self.actor_contour_ = self.update_actor_contour(new_line)
            self.viewer.scene.add_actor(self.actor_contour)  # 重新添加平面等高线实体
            self.viewer.scene.add_actor(self.actor_contour_)  # 重新添加立体等高线实体

        self.viewer.scene.render()  # 刷新界面(没有生成新的线段也可以刷新)

    def getContour(self, contour_num, custom_contour):
        # 等高线设置弹框点击确认之后_signal被发送到此处
        # 根据重新设置后的等高线重新对等高线进行设置
        self.viewer.scene.remove_actor(self.actor_tri)
        self.viewer.scene.remove_actor(self.actor_horizon)
        self.viewer.scene.remove_actor(self.actor_contour)
        self.viewer.scene.remove_actor(self.actor_contour_)
        del self.actor_tri
        del self.actor_horizon
        del self.actor_contour
        del self.actor_contour_
        self.plot()  # self.triangle_list, self.actot_tri, self.actor_horizon 在此处生成
        self.contour_num = contour_num
        self.custom_contour = custom_contour
        self.contour_value = np.append(
            np.linspace((self.z.max() - self.z.min()) / (self.contour_num + 1), self.z.max(), self.contour_num,
                        endpoint=False), np.array(self.custom_contour))
        self.flag_init()
        self.points = []
        self.points_ = []
        self.lines = []
        self.contour_value_cur = 0
        self.triangle_base = 0
        self.triangle_leaf = -1
        self.triangle_cur = 0
        self.timer.start(200)
