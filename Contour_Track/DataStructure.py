# Delaunay三角剖分算法的数据结构

class Point:
    def __init__(self, pointnum, x, y, z, AdjTriangle_list):
        self.PointNum = pointnum  # 点序号
        self.X = x  # X坐标
        self.Y = y  # Y坐标
        self.Z = z  # Z坐标
        self.ADJTriangle_list = AdjTriangle_list  # 与点关联的三角形列表

    def __eq__(self, other):
        if (self.X == other.X) and (self.Y == other.Y) and (self.Z == other.Z):
            return 1
        else:
            return 0

class Line:
    def __init__(self, point_b, point_e):
        self.BeginPoint = point_b
        self.EndPoint = point_e

    def __eq__(self, other):
        # 重载
        if (self.BeginPoint == other.EndPoint and
                self.EndPoint == other.BeginPoint):
            return 1
        elif (self.BeginPoint == other.BeginPoint and
              self.EndPoint == other.EndPoint):
            return 1
        else:
            return 0

class Triangle:
    def __init__(self, point_b, point_e, point_s):
        self.point0 = point_b
        self.point1 = point_e
        self.point2 = point_s
        self.BaseLine = Line(point_b, point_e)
        self.newLine1 = Line(point_e, point_s)
        self.newLine2 = Line(point_s, point_b)


    def __eq__(self, other):
        # 重载
        if(self.BaseLine==other.BaseLine and self.newLine1==other.newLine1 and self.newLine2==other.newLine2):
            return 1
        elif(self.BaseLine==other.BaseLine and self.newLine1==other.newLine2 and self.newLine2==other.newLine1):
            return 1
        elif(self.BaseLine==other.newLine1 and self.newLine1==other.newLine2 and self.newLine2==other.BaseLine):
            return 1
        elif(self.BaseLine==other.newLine1 and self.newLine1==other.BaseLine and self.newLine2==other.newLine2):
            return 1
        elif(self.BaseLine==other.newLine2 and self.newLine1==other.newLine1 and self.newLine2==other.BaseLine):
            return 1
        elif(self.BaseLine==other.newLine2 and self.newLine1==other.BaseLine and self.newLine2==other.newLine1):
            return 1
        else:
            return 0
