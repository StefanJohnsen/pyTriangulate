
# Triangulate.py - Python script for triangulating polygons
#
# This script specializes in triangulating polygons using two techniques:
# - Fan method for convex polygons
# - Earcut technique for concave polygons
#
# Copyright (c) 2023 by FalconCoding
# Author: Stefan Johnsen
# Email: stefan.johnsen@outlook.com
#
# This software is released under the MIT License.

import math
import numpy as np
from enum import Enum

epsilon = 1e-6

class TurnDirection(Enum):
    Right = 1
    Left = -1
    NoTurn = 0

class Point:
    def __init__(self, x=0.0, y=0.0, z=0.0, i=None):
        self.x = x
        self.y = y
        self.z = z
        self.i = i

    def __add__(self, other):
        if isinstance(other, Point):
            return Point(self.x + other.x, self.y + other.y, self.z + other.z)
        else:
            raise ValueError("Addition is only supported between Point objects.")

    def __sub__(self, other):
        if isinstance(other, Point):
            return Point(self.x - other.x, self.y - other.y, self.z - other.z)
        else:
            raise ValueError("Subtraction is only supported between Point objects.")

    def __mul__(self, scalar):
        if isinstance(scalar, float):
            return Point(self.x * scalar, self.y * scalar, self.z * scalar)
        else:
            raise ValueError("Multiplication is only supported with scalar values.")

    def __truediv__(self, scalar):
        if isinstance(scalar, float):
            if scalar == 0.0:
                return Point.zero()
            return Point(self.x / scalar, self.y / scalar, self.z / scalar)
        else:
            raise ValueError("Division is only supported with scalar values.")

    def __eq__(self, other):
        if other is None: return False
        if abs(self.x - other.x) > epsilon: return False
        if abs(self.y - other.y) > epsilon: return False
        if abs(self.z - other.z) > epsilon: return False
        return True

    def copy(self):
        return Point(self.x, self.y, self.z, self.i)

    @classmethod
    def zero(cls):
        return cls(0.0, 0.0, 0.0)

def dot(u, v):
    return u.x * v.x + u.y * v.y + u.z * v.z

def cross(u, v):
    x = u.y * v.z - u.z * v.y
    y = u.z * v.x - u.x * v.z
    z = u.x * v.y - u.y * v.x
    return Point(x, y, z)

def length(u):
    return math.sqrt(u.x * u.x + u.y * u.y + u.z * u.z)

class Triangle:
    def __init__(self, p0, p1, p2):
        self.p0 = p0
        self.p1 = p1
        self.p2 = p2

def turn(p, u, n, q):
   
    v = cross(q - p, u)
     
    d = dot(v, n)

    if d > +epsilon: return TurnDirection.Right
    if d < -epsilon: return TurnDirection.Left

    return TurnDirection.NoTurn

def triangleAreaSquared(a, b, c):
    c = cross(b - a, c - a)
    return length(c)**2.0 / 4.0

def normalize(v):
    return v/length(v)

def normal(polygon):
    n = len(polygon)
    v = Point.zero()

    if n < 3: return v

    for index in range(n):
        
        item = polygon[index % n]
        next = polygon[(index + 1) % n]

        v.x += (next.y - item.y) * (next.z + item.z);
        v.y += (next.z - item.z) * (next.x + item.x);
        v.z += (next.x - item.x) * (next.y + item.y);

    return normalize(v)

def getBarycentricTriangleCoordinates(a, b, c, p):
    alpha = beta = gamma = -2.0 * epsilon

    v0 = c - a
    v1 = b - a
    v2 = p - a

    dot00 = dot(v0, v0)
    dot01 = dot(v0, v1)
    dot02 = dot(v0, v2)
    dot11 = dot(v1, v1)
    dot12 = dot(v1, v2)

    denom = dot00 * dot11 - dot01 * dot01

    if abs(denom) < epsilon:
        return alpha, beta, gamma

    alpha = (dot11 * dot02 - dot01 * dot12) / denom
    beta = (dot00 * dot12 - dot01 * dot02) / denom
    gamma = 1.0 - alpha - beta

    return alpha, beta, gamma

def pointInsideOrEdgeTriangle(a, b, c, p):
    alpha, beta, gamma = getBarycentricTriangleCoordinates(a, b, c, p)
    return alpha >= -epsilon and beta >= -epsilon and gamma >= -epsilon

def isEar(index, polygon, normal):
    n = len(polygon)

    if n <  3: return False
    if n == 3: return True

    prevIndex = (index - 1 + n) % n
    itemIndex = index % n
    nextIndex = (index + 1) % n

    prev = polygon[prevIndex]
    item = polygon[itemIndex]
    next = polygon[nextIndex]

    u = normalize(item - prev)

    if turn(prev, u, normal, next) != TurnDirection.Right:
        return False

    for i in range(n):
        if i in (prevIndex, itemIndex, nextIndex):
            continue

        p = polygon[i]
        if pointInsideOrEdgeTriangle(prev, item, next, p):
            return False

    return True

def getBiggestEar(polygon, normal):
    n = len(polygon)

    if n == 3: return 0
    if n == 0: return -1

    maxIndex = -1
    maxArea = float("-inf")

    for index in range(n):
        if isEar(index, polygon, normal):
            prev = polygon[(index - 1 + n) % n]
            item = polygon[index % n]
            next = polygon[(index + 1) % n]

            area = triangleAreaSquared(prev, item, next)

            if area > maxArea:
                maxIndex = index
                maxArea = area

    return maxIndex

def convex(polygon, normal):
    n = len(polygon)

    if n <  3: return False
    if n == 3: return True

    polygonTurn = TurnDirection.NoTurn

    for index in range(n):
        prev = polygon[(index - 1 + n) % n]
        item = polygon[index % n]
        next = polygon[(index + 1) % n]

        u = normalize(item - prev)
        item_turn = turn(prev, u, normal, next)

        if item_turn == TurnDirection.NoTurn:
            continue

        if polygonTurn == TurnDirection.NoTurn:
            polygonTurn = item_turn

        if polygonTurn != item_turn:
            return False

    return True

def clockwiseOriented(polygon, normal):
    n = len(polygon)

    if n < 3: return False

    orientationSum = 0.0

    for index in range(n):
        prev = polygon[(index - 1 + n) % n]
        item = polygon[index % n]
        next = polygon[(index + 1) % n]

        edge = item - prev
        toNextPoint = next - item

        v = cross(edge, toNextPoint)
        orientationSum += dot(v, normal)

    return orientationSum < 0.0

def makeClockwiseOrientation(polygon, normal):
    if len(polygon) < 3:
        return

    if not clockwiseOriented(polygon, normal):
        polygon.reverse()

def fanTriangulation(polygon):
    triangles = []
    for index in range(1, len(polygon) - 1):
        triangles.append(Triangle(polygon[0], polygon[index], polygon[index + 1]))
    return triangles

def cutTriangulation(polygon, normal):
    
    triangles = []
    
    makeClockwiseOrientation(polygon, normal)

    while polygon:
        index = getBiggestEar(polygon, normal)

        if index == -1: return []

        n = len(polygon)

        prev = polygon[(index - 1 + n) % n]
        item = polygon[index % n]
        next = polygon[(index + 1) % n]

        triangles.append(Triangle(prev, item, next))

        del polygon[index]

        if len(polygon) < 3: break

    return triangles if len(polygon) < 3 else []

def removeConsecutiveEqualPoints(polygon):
    uniquePolygon = []
    n = len(polygon)
    for index in range(n):
        item = polygon[index % n]
        next = polygon[(index + 1) % n]
        if item.i == next.i: continue
        uniquePolygon.append(item)
    return uniquePolygon

def triangulate(polygon):
    
    polygon = removeConsecutiveEqualPoints(polygon)
    
    n = normal(polygon)
    
    if len(polygon) < 3: return [], n

    if len(polygon) == 3:
        t = Triangle(polygon[0], polygon[1], polygon[2])
        return [t], n

    if convex(polygon, n):
        return fanTriangulation(polygon), n

    return cutTriangulation(polygon, n), n