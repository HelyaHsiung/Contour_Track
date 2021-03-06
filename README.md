# 等高线自动追踪的Python可视化

这是我在参与完成Python三维可视化课程设计之后的一个记录，在这个过程中，我算是感受到三维可视化对于新手的不友好，一方面是由于我对Python的可视化框架不太熟悉，另一方面也包括等高线自动追踪算法比较复杂并且有多种实现。这里选用一种三角网格下的等高线自动追踪方法来展开描述。不足之处欢迎大家指出来呀。

## <span id = "content">目录</span>

1. [Python 三维可视化环境介绍](#0)
2. [Delaunay 三角网格剖分](#1)
3. [三角网格下的等高线追踪算法](#2)
4. [Python 三维可视化框架搭建](#3)
5. [借助 Qtimer 的等高线追踪效果动态延时展示](#4)
6. [源文件及参考文献](#5)

## 一. <span id = "0">Python三维可视化环境介绍</span>  <font size = 1>[返回目录](#content)</font>

正文开始之前，我们先简单了解一下此次使用的可视化第三方库。当前使用较多的Python可视化库有 TVTK 和 Mayavi 等等，这里我们使用TVTK，TVTK本身也是使用 Python 对 C++ 中的 VTK 进行包装，所以学习过程中我也参照了 VTK 的指导书来学习 TVTK。Python版本为 3.8.10，主窗口的创建使用 PyQt 5.15.4，TVTK 是第三方库 VTK 8.2.0 。这两个 whl 文件均从 <https://www.lfd.uci.edu/~gohlke/pythonlibs/> 中获取，也包含在了源文件压缩包当中。

## 二. <span id = "1">Delaunay三角网格剖分</span>  <font size = 1>[返回目录](#content)</font>

三角网格剖分我是在看了老师的框架和一位大哥的博客[^1]后写出来的，属于 Delaunay 三角剖分算法中的逐点插入法实现。

1. Delaunay三角网的特点

> (1) Delaunay 三角网是唯一的
> (2) 外边界构成了点集的凸多边形外壳
> (3) 三角形的外接圆内不包含任何点
> (4) 最接近于规则化

2. Delaunay三角剖分[^2]

这里我摘抄了百度百科关于Delaunay三角剖分的解释。

三角剖分：
假设 V 是二维实数域上的有限点集，边 e 是由点集中的点作为端点构成的封闭线段，E 为 e 的集合。那么该点集 V 的一个三角剖分 T=(V, E)是一个平面图 G ，该平面满足下面条件：

> (1) 除了端点，平面图中的边不包含点集中的任何点；
> (2) 没有相交边;
> (3) 平面图中的所有的面都是三角面，且所有三角面的合集是散点集的凸包。

Delaunay边：
假设 E 中的一条边 e (两个端点为a, b), e 满足下列条件，则称之为 Delaunay 边：

> 存在一个圆经过a, b两点，圆内 (注意是圆内, 圆上最多三个点共圆) 不含点集 V 中任何其他的点，这一特性又称为空圆特性。

Delaunay三角剖分：
如果点集 V 的一个三角剖分 T 只包含 Delaunay 边，那么该三角剖分称为 Delaunay 三角剖分。Delaunay 三角剖分有两个重要准则：

> (1) 空外接圆准则: 在 TIN 中，过每个三角形的外接圆均不包含点集中的其余任何点。

<div align = center>
<img
src = 'https://s4.ax1x.com/2022/01/09/7kOTRf.gif'
width = '190px'
height = '150px'/>
</div>

> (2) 最大最小角特性：在 TIN 中的两相邻三角形形成的凸四边形中，这两个三角形中的最小内角一定大于交换凸四边形对角线后形成的两三角形的最小内角。

<div align = center>
<img
src = https://s4.ax1x.com/2022/01/09/7kXX6O.gif
width = '330px'
height = '120px'/>
</div>

3. 逐点插入法

首先给出流程图：

<div align = center>
<img
src = https://s4.ax1x.com/2022/01/11/7mwjBD.png
width = '650px'
height = '1150px'
/>
</div>

接下来我们一起来详细看一下关键步骤。首先需要注意的是，这里进行三角剖分只需要点的 x、y 坐标，不需要 z 坐标，也即依据点数据的 XOY 平面投影点进行三角剖分，在最后绘制时才考虑高程值。因此三角剖分主要在 XOY 平面上进行。

(1) 创建虚拟的超大三角形
这一步生成一个 XOY 平面上的大三角形，使其包围所有点在 XOY 平面的投影，并且没有点位于三角形的边上。我是首先求出所有点的 Xmin、Xmax、Ymin、Ymax，即横纵坐标的范围，这样可以得到一个矩形包围圈。然后求出这个矩形的外接等边三角形。我这里还将矩形中心缩放2倍以避免点刚好落在三角形边上的特殊情况。这个三角形的创建方式也各式各样，只要可以达到目的就可以了。

<div align = center>
<img
src = https://s4.ax1x.com/2022/01/10/7E0Ptx.png
width = '350px'
height = '200px'
/>
<img
src = https://s4.ax1x.com/2022/01/10/7EgQlq.png
width = '280px'
height = '200px'
/>
</div>

(2) 判断点是否位于三角形外接圆内部
这里我们设三角形 ABC 和点 P，首先求出三角形外接圆的圆心 O，然后得到半径 r，再比较 r 与 OP 大小关系。
求解圆心的时候利用三角形外接圆的圆心到达三个顶点距离相等这一特性：

<div align = center>
<img
src = https://s4.ax1x.com/2022/02/28/bKJHxI.png
width = '500px'
height = '75px'
/>
</div>

对其进行整理可以得到：

<div align = center>
<img
src = https://s4.ax1x.com/2022/02/28/bKJqMt.png
width = '500px'
height = '75px'
/>
</div>

上式中 <img src = https://s4.ax1x.com/2022/02/28/bKJLsP.png width = '30px' height = '30px'/> 和 <img src = https://s4.ax1x.com/2022/02/28/bKJ4aD.png width = '30px' height = '30px'/> 为待求参数。利用克莱默法则可以计算出圆心的 x 和 y 坐标。记 <img src = https://s4.ax1x.com/2022/02/28/bKJhVO.png width = '180px' height = '30px'/>，<img src = https://s4.ax1x.com/2022/02/28/bKJRr6.png width = '180px' height = '30px'/>；<img src = https://s4.ax1x.com/2022/02/28/bKJWqK.png width = '240px' height = '30px'/>，<img src = https://s4.ax1x.com/2022/02/28/bKJ2Kx.png width = '180px' height = '30px'/>，<img src = https://s4.ax1x.com/2022/02/28/bKJ5Ie.png width = '180px' height = '30px'/>, <img src = https://s4.ax1x.com/2022/02/28/bKJoPH.png width = '240px' height = '30px'/>. 上式即：

<div align = center>
<img
src = https://s4.ax1x.com/2022/02/28/bKJTGd.png
width = '250px'
height = '75px'
/>
</div>

根据克莱默法则，

<div align = center>
<img
src = https://s4.ax1x.com/2022/02/28/bKJ7RA.png
width = '350px'
height = '280px'
/>
</div>

知道圆心之后就可以确定点到圆心的距离，并与圆的半径做比较，若点到圆心距离大于圆的半径则说明点在三角形外接圆外部。反之则点在圆的内部或者圆上。

4. 利用排序对逐点插入法进行优化

好了，其实走到这一步，三角网已经可以正确地显示出来了。但是仔细观察一下逐点插入法，我们发现这个算法其实特别慢。那么哪里消耗了运算时间呢？原因是每插入一个点，之前创建好的所有三角形都要挨个和这个点再判断一次：点是否位于三角形外接圆外部。于是我们就可以想到，当我插入一个点，如果只需要一部分三角形和它进行判断就可以节省相当一部分时间。这个思路也是从大佬[^1]那里参考来的。

(1) 我们首先将点数据根据它们的 x 坐标进行从小到大排序。具体的函数我是用 numpy 的 `argsort` 排序函数的，它返回的是从小到大排序后的索引。

(2) 我们看下面这个图片，如果一个点在三角形的右侧，因为点是按照从 x 坐标从小到大的顺序来插入的，所以后插入的点一定也在这个三角形的右侧。既然点在圆的右侧就不存在落在三角形外接圆内部的这种情况。那么我们就可以认定这个三角形已经是一个“成熟”的三角形了，以后就不用再把它拿出来做判断。具体操作是我们在向三角形列表 triangle_list 中加入三角形之前，设置一个缓冲区 triangle_buffer。这个缓冲区内的三角形有待继续检验，当某一个点在某一个三角形外接圆的右侧时，这一个三角形就可以从缓冲区中取出来放进最终结果的三角形列表当中，它就不用再接受检验了。

<div align = center>
<img
src = https://s4.ax1x.com/2022/01/11/7eJhNV.png
width = '240px'
height = '150px'
/>
</div>


4. 记录点与三角形的关联关系

当三角形被转移到最终结果的三角形列表 triangle_list 当中时，记录下三角形的三个顶点的关联三角形列表。

具体来操作：

(1) 在点的数据结构中设置一个成员，也即点的关联三角形索引列表。存储的是这个点的关联三角形的索引。

(2) 因为被插入的三角形是三角形列表中的最后一个，所以插入三角形之前的三角形列表的长度也就是这个三角形在三角形列表中的索引（序号）。

(3) 在三角形被转移到 triangle_list 之前，这个三角形的 3 个顶点的关联三角形列表中分别插入该三角形的索引，也即尾插三角形之前的 triangle_list 的长度。

这样，当三角网格创建完毕时，每一个点的的所有的关联三角形的索引都可以查出来了。这样做的目的是为了后边的等高线追踪更方便一些，即根据一个三角形和公共边查出其相邻的三角形。

## 三. <span id = "2">三角网格下的等高线追踪算法</span>  <font size = 1>[返回目录](#content)</font>

1. 两种常见的等高线创建算法

目前见过的创建等高线的算法有两种：

(1) 一种是直接对 triangle_list 进行遍历，每一个三角网格都和等高线的高程值 z 进行判断，只需创建出该三角网格内的等高线线段，所有的三角网格内的等高线线段都创建完毕之后，我们从表象上来看就可以将线段连接成等高线曲线。但是这样的结果中各个等高线线段彼此之间并没有任何关联，即使有两个线段是邻居，它们也互不认识。

创建等高线线段的过程也比较容易理解，如果单元网格是矩形单元格，那么其 4 个顶点的高程值和 z 值的关系有 $2^4 = 16$ 种；如果基本单元格是三角形，那么共有 $2^3 = 8$ 情况。

等高线线段的两个端点均根据等高线高程值和三角形边的两个端点的高程值进行线性插值得到。

<div align = center>
<img
src = https://s4.ax1x.com/2022/01/11/7egcJe.png
width = '270px'
height = '250px'
/>
<img
src = https://s4.ax1x.com/2022/01/11/7eg6iD.png
width = '250px'
height = '250px'
/>
</div>


(2) 另一种就是等高线追踪算法，其特点在于“追踪”，即完整地创建一条等高线之后创建下一条等高线。这一次选用的是三角网格下的等高线追踪，其等高线线段位置的情况比矩形单元格下更容易判断。

假设等高线的高程值有多个，从最低的等高线高程值开始，然后从底层向高层逐步创建等高线。设当前需要判断的等高线高程值为 z ，三角网格为 triangle_list。

当我们在这个三角网格中的等高线线段创建出来之后，可以发现这个线段和三角形相交于边 AB 和边 AC，那么下一次就可以访问这个三角形的以 AB 为公共边的相邻三角形，或者访问以 AC 为公共边的相邻三角形。为了防止重复访问，设置一个 flag 矩阵或者列表来使用标号法，我这里 flag = 1 代表可以访问，flag = 0 代表不可以访问。flag矩阵初始化为 1，访问过了就这个三角形的 flag 更改为 0 以避免下一次访问。为了减少运算次数，在等高线正式追踪之前，遍历一次 triangle_list，如果其 3 个顶点均大于 z 或者均小于等于 z ，那么就将其 flag 从 1 改为 0 表示无需访问。

<div align = center> 
<img
src = https://s4.ax1x.com/2022/01/11/7efc7t.png
width = '230px'
height = '200px'
/>
</div>

①  借助三个“游标”实现等高线追踪

首先我们先认识一下这三个游标：triangle_base, triangle_cur, triangle_leaf。第一，我们只需要知道它是三角形的索引。第二，我们了解一下这三个“游标”的意义： triangle_base 代表某一条等高线被访问的第一个线段所在的三角网格的索引；triangle_cur 代表当前访问的三角网格的索引；triangle_leaf 表示当我们访问到一条的等高线的腰部时，先任意沿着其中一个方向进行等高线追踪，另外一个方向用 triangle_leaf 记录下来。

<div align = center>
<img
src = https://s4.ax1x.com/2022/01/11/7eHNWt.png
width = '500px'
height = '230px'
/>
</div>


第一步：从 triangle_list 第一个三角形开始判断，直到找到第一个可以访问的三角网格，这代表着我们已经找到了一条等高线，这条等高线第一个被访问的线段所在的三角形用 triangle_base 记录下来，然后把这个等高线线段绘制出来；

第二步：上一步中当前访问的三角形在访问后需要将其 flag 从 1 更改为 0，然后我们就要考虑下一步该往哪里走。

> i  如果该三角形的沿等高线线段方向的**两个相邻三角形的 flag 均为 1**，即这条等高线有两个方向可以追踪，用 triangle_leaf 记录下其中一个方向，然后往另一个方向出发；
> 
> ii  如果该三角形的沿等高线线段方向的**两个相邻三角形的 flag 其中 1 个为 1、1 个为 0 **，那么表示单向行驶即可；
> 
> iii  如果该三角形的沿等高线线段方向的**两个相邻三角形的 flag 均为 0**，表示这个方向已经走到了尽头，如果之前有对 triangle_leaf 进行赋值，那么回到 triangle_leaf 去访问等高线的另一个方向，如果之前没有对 triangle_leaf 进行赋值，那么表示这条完整的等高线已经全部创建完毕。就回到 triangle_base，即这条等高线的起始访问位置，然后按照 triangle_list 索引顺序去寻找下一条等高线。

第三步：当 triangle_base 走到 triangle_list 的 end 时，表示这一个水平面上的等高线创建完毕，根据等高线列表的高程值列表将 z 值增大，继续创建更高层的等高线。

② 根据点和三角形的关联关系寻找三角形的共边相邻三角形

在创建等高线线段的时候，我们已经可以知道等高线线段和三角网格相交于哪两条边。两个三角形有一条公共边，根据这一条公共边的两个端点即可以找到共边相邻三角形。

<div align = center>
<img
src = https://s4.ax1x.com/2022/01/11/7eHtJI.png
width = '260px'
height = '220px'
/>
</div>
观察上图，右侧的绿色三角形为当前访问的三角形，红点表示公共边的两个端点，左上侧的红点有 4 个关联三角形，右下侧的红点有 5 个关联三角形，由于点的关联三角形存储的只是三角形的索引，因此对这长度为 4 的列表和长度为 5 的列表进行相交，并且将自身的索引排除，那么求得的结果的长度为 1 或者 0 。长度为 1 代表其相邻三角形的索引，长度为 0 代表当前访问的三角形在这条公共边上没有相邻三角形或者相邻三角形已经被访问过。

有了这个基础，我们就可以步步推进，沿着等高线方向进行追踪。

## 四. <span id = "3">Python三维可视化框架搭建</span>  <font size = 1>[返回目录](#content)</font>

1. 可视化主体为 MainWindow 主窗口，继承 `QMainwindow` 父类创建。MainWindow包含一个主界面、工具栏、菜单栏和状态栏。菜单栏上添加动作按钮以打开点数据文件。工具栏上设置动作按钮以打开 TVTKWindow 子窗口。
2. TVTKWindow 子窗口是展示三角网格和等高线的主窗口。在 TVTKWindow 子窗口中同样有一个工具栏，工具栏中添加一个动作按钮用来设置等高线的级数。
3. TVTKWindow 中继承 HasTrait 创建一个视图布局，并创建三角网实体和等高线实体。且等高线实体会在等高线创建的过程中不断地更新。

可视化框架如下：

<div align = center>
<img
src = https://s4.ax1x.com/2022/01/11/7mdcLD.png
width = '460px'
height = '400px'
/>
</div>



## 五. <span id = "4">借助Qtimer的等高线追踪效果动态延时展示</span>  <font size = 1>[返回目录](#content)</font>

这一步为附加步骤，其实经过前5步之后，已经可以完成等高线追踪的任务了。由于课程设计的需要，等高线追踪的过程需要动态延时展示，这也顺带可以作为一个 Demo 来了解等高线追踪的流程。我们不妨思考一下，动态展示说明每创建出一个等高线的线段以后，需将 TVTKViewer 视图布局中的等高线实体进行更新。并且将这个间隔设置为人眼可以分辨的时间间隔，这里选用 0.2 秒刷新一次界面。接下来对延时刷新的方法进行介绍。

这里引用百度百科对 `QTimer`的介绍[^3]：
> QTimer提供了定时器信号和单触发定时器。它在内部使用定时器事件来提供更通用的定时器。QTimer很容易使用：创建一个QTimer，使用start()来开始并且把它的timeout()连接到适当的槽。当这段时间过去了，它将会发射timeout()信号。注意当QTimer的父对象被销毁时，它也会被自动销毁。

创建定时器的一段代码如下：

```Python
self.timer = QTimer()  # 定义计时器, 来自QtCore
self.timerID = self.timer.start(200)  # 每隔200ms发送一个触发信号timeout
self.timer.timeout.connect(self.find_next_lineSlot)  # self.find_next_lineSlot 是一个自定义的函数，实现查找下一条等高线线段并刷新显示界面
```

等高线级数设置级数的对话框继承自`QDialog`，当设置等高线的对话框打开的时候，停止`self.timer`并且根据新设置的等高线级数来对等高线的高程值列表进行重新赋值，对游标、显示实体进行重新初始化。当重新初始化完成之后再恢复`self.timer`，停止计数器使用`stop()`函数，恢复计时器只需要重新执行`start(200)`即可。

最后，附上这个项目的流程图：

<div align = center>
<img
src = https://s4.ax1x.com/2022/01/11/7mYLX4.png
width = '500px'
height = '700px'
/>
</div>


## 六. <span id = "5">源文件及参考文献</span>  <font size = 1>[返回目录](#content)</font>

最终演示效果：
<div align = center>
<img
src = https://s4.ax1x.com/2022/01/11/7mamNR.gif
width = '500px'
height = '400px'
/>
</div>

项目源代码及whl文件：[Contour_Track](https://github.com/HelyaHsiung/Contour_Track.git)

参考文献：

[^1]: [三角剖分算法(delaunay)](https://www.cnblogs.com/zhiyishou/p/4430017.html)——纸异兽
[^2]:[Delaunay三角剖分算法](https://baike.baidu.com/item/Delaunay%E4%B8%89%E8%A7%92%E5%89%96%E5%88%86%E7%AE%97%E6%B3%95/3779918?fr=aladdin)——百度百科
[^3]:[QTimer](https://baike.baidu.com/item/QTimer/3131650?fr=aladdin)——百度百科
