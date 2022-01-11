# Delaunay三角剖分算法
from DataStructure import *
import numpy as np
import copy


def Points2List(points):
    '''
    将点以列表形式排列
    :param points:两列数值，分别为点的x值与y值
    :return:生成的点列表
    '''
    num = 0
    point_list = []
    for point in points:
        temp = Point(num, point[0], point[1], point[2], [])
        point_list.append(temp)
        num = num + 1
    return point_list
    # 这里对 for point in points 有一些提示说明:
    # 该用法中第一次从points提取第一个元素,第二次从points中提取第二个元素
    # 假如在第一次循环中删除第一个元素，则下一次的point是新的points的第二个元素，也即删除元素前的points的第三个元素
    # 所以for 临时元素 in 列表的用法是：按照索引递增，并且列表会动态变化
    # 建议：使用该用法时不要对列表进行增删操作，否则有一些难以发现的bug出现


def XYMaxMin(point_list):
    '''
    计算所有点横纵坐标的最大值和最小值
    :param point_list:点列表
    :return:横坐标的最大值和最小值，纵坐标的最大值和最小值
    '''
    xmax = point_list[0].X
    xmin = point_list[0].X
    ymax = point_list[0].Y
    ymin = point_list[0].Y
    
    for i in range(1, len(point_list)):
        if point_list[i].X > xmax :
            xmax = point_list[i].X
        if point_list[i].X < xmin :
            xmin = point_list[i].X
        if point_list[i].Y > ymax :
            ymax = point_list[i].Y
        if point_list[i].Y < ymin :
            ymin = point_list[i].Y
    
    return xmin, xmax, ymin, ymax


def BuildMaxTriangle(x_min, x_max, y_min, y_max):
    '''
    建立外围大三角形
    :param x_min:横坐标的最小值
    :param x_max:横坐标的最大值
    :param y_min:纵坐标的最小值
    :param y_max:纵坐标的最大值
    :return:外围大三角形
    '''
    a = y_max - y_min
    b = x_max - x_min
    midx = (x_min + x_max)/2
    midy = (y_min + y_max)/2
    point_b = Point(-1, midx - (2*a/(3**(0.5)) + b), midy - a, 0, [])
    point_e = Point(-2, midx + (2*a/(3**(0.5)) + b), midy - a, 0, [])
    point_s = Point(-3, midx, midy + a + b * (3**0.5), 0, [])
    maxtriangle = Triangle(point_b, point_e, point_s)
    return maxtriangle


def ContainsInCircumCircle(triangle, point):
    '''
    判断点是否在三角形的外接圆中(上)，点在圆上称之为退化
    :param triangle:限定范围的三角形
    :param point:需要判断的点
    :return: 0: 点point在三角形外接圆内(上); 1: 点point在三角形外接圆外,不在外接圆右侧; 2:点point在三角形外接圆右侧
    '''
    Xp = point.X
    Xa = triangle.point0.X
    Xb = triangle.point1.X
    Xc = triangle.point2.X
    Yp = point.Y
    Ya = triangle.point0.Y
    Yb = triangle.point1.Y
    Yc = triangle.point2.Y

    # 求圆心与半径

    a1 = 2 * (Xb - Xa)
    b1 = 2 * (Yb - Ya)
    c1 = Xb ** 2 + Yb ** 2 - Xa ** 2 - Ya ** 2

    a2 = 2 * (Xc - Xb)
    b2 = 2 * (Yc - Yb)
    c2 = Xc ** 2 + Yc ** 2 - Xb ** 2 - Yb ** 2

    X = ((c1 * b2) - (c2 * b1)) / ((a1 * b2) - (a2 * b1))
    Y = ((a1 * c2) - (a2 * c1)) / ((a1 * b2) - (a2 * b1))

    Radius = ((Xa - X) ** 2 + (Ya - Y) ** 2) ** 0.5
    Distance = ((Xp - X) ** 2 + (Yp - Y) ** 2) ** 0.5

    if Distance <= Radius:
        return   0
    elif Xp - X > Radius:
        return  2
    else:
        return 1


def RemoveRepeatedLine(line_list):
    '''
    去除边表中的重复边，连根拔除,元素数量小于3的表直接返回不处理
    :param line_list: 边表
    :return : 没有重复边的边表
    '''
    if len(line_list) > 2:
        i = 0
        while (i < len(line_list) - 1):
            line_1 = line_list[i]
            for j in range(i + 1, len(line_list), 1):
                line_2 = line_list[j]
                if line_1 == line_2:
                    line_list.pop(i)
                    line_list.pop(j - 1)
                    i -= 1
                    break
                else:
                    pass
            i += 1
    else:
        pass

    return line_list


def Delaunay(points):
    '''
    Delaunay三角剖分算法
    :param points:两列数值，分别为点的x值与y值
    :return:根据输入的两列数值生成的三角形列表
    '''
    triangle_list = []
    point_list = Points2List(points)
    x_min, x_max, y_min, y_max = XYMaxMin(point_list)
    maxtriangle = BuildMaxTriangle(x_min, x_max, y_min, y_max)

    triangle_list = []  # 存储三角形
    triangle_buffer = []  # 临时存储三角形
    triangle_buffer.append(maxtriangle)

    # 请在此处添加代码，完成Delaunay三角网算法
    for point in point_list:  # 对所有点进行遍历
        line_list = []  # 用来储存拆下三角形产生的临时边
        i = 0   # 计数器
        while(i < len(triangle_buffer)):
            temp = ContainsInCircumCircle(triangle_buffer[i], point)
            if temp == 0:
                line_list.append(triangle_buffer[i].BaseLine)
                line_list.append(triangle_buffer[i].newLine1)
                line_list.append(triangle_buffer[i].newLine2)
                triangle_buffer.pop(i)
                i -= 1
            elif temp == 2:
                poped_triangle = triangle_buffer.pop(i)
                i -= 1
                if poped_triangle.point0.PointNum >= 0 and poped_triangle.point1.PointNum >= 0 and poped_triangle.point2.PointNum >= 0:
                    #  不加入包含有大三角形顶点的三角形
                    poped_triangle.point0.ADJTriangle_list.append(len(triangle_list))
                    poped_triangle.point1.ADJTriangle_list.append(len(triangle_list))
                    poped_triangle.point2.ADJTriangle_list.append(len(triangle_list))
                    triangle_list.append(poped_triangle)
                else:
                    pass
            else:  # ContainsInCircumCircle(triangle_buffer[i], point) == 1
                pass
            i += 1

        line_list = RemoveRepeatedLine(line_list)  # 对边表进行除重处理 (连根拔除)

        for line in line_list:
            if (line.EndPoint.Y - point.Y) * (point.X - line.BeginPoint.X)  == (point.Y - line.BeginPoint.Y) * (line.EndPoint.X - point.X):
                pass  # 若点在直线上
            else:
                temp_triangle = Triangle(line.BeginPoint, line.EndPoint, point)
                triangle_buffer.append(temp_triangle)

    # 最后把三角形缓冲表中所有三角形放入最终的Dealnuay三角形列表中
    for triangle in triangle_buffer:
        if triangle.point0.PointNum >= 0 and triangle.point1.PointNum >= 0 and triangle.point2.PointNum >= 0:
            triangle.point0.ADJTriangle_list.append(len(triangle_list))
            triangle.point1.ADJTriangle_list.append(len(triangle_list))
            triangle.point2.ADJTriangle_list.append(len(triangle_list))
            triangle_list.append(triangle)
        else:
            pass

    return triangle_list


def List2Triangles(triangle_list):
    '''
    构建三角形顶点列表
    :param triangle_list:
    :return: 每个三角形三个顶点的编号
    '''
    Triangles = []
    for triangle in triangle_list:
        Triangles.append([triangle.point0.PointNum, triangle.point1.PointNum, triangle.point2.PointNum])
    return Triangles



