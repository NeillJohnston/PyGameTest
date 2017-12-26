import math


class Vector2:
    def __init__(self, x, y):
        self.x, self.y = x, y

    # Override abs to get the length
    def __abs__(self):
        return math.sqrt(self.x**2 + self.y**2)

    # Get the length
    def mag(self):
        return abs(self)

    # Get the angle in radians
    def ang(self):
        return math.atan2(self.y, self.x)

    # Return this vector rotated by theta radians as a new vector
    def rotated(self, theta):
        theta += self.ang()
        m = abs(self)
        return Vector2(m * math.cos(theta), m * math.sin(theta))

    # Get the angle between two vectors in radians
    def ang_to(self, other):
        dot = self * other
        return math.acos(dot / (abs(self) * abs(other)))

    # Compare
    def __eq__(self, other):
        return self.x == other.x and self.y == other.y

    # Not compare
    def __ne__(self, other):
        return not self == other

    # Override + to do vector addition
    def __add__(self, other):
        return Vector2(self.x + other.x, self.y + other.y)

    # Mutable vector addition
    def __iadd__(self, other):
        self.x += other.x
        self.y += other.y
        return self

    # Override - to do vector subtraction
    def __sub__(self, other):
        return Vector2(self.x - other.x, self.y - other.y)

    # Mutable vector subtraction
    def __isub__(self, other):
        self.x -= other.x
        self.y -= other.y
        return self

    # Override * to either multiply by a scalar, or find the dot product
    def __mul__(self, other):
        if type(other) is Vector2:
            return self.x * other.x + self.y * other.y
        else:
            return Vector2(other * self.x, other * self.y)

    def __rmul__(self, other):
        return Vector2(other * self.x, other * self.y)

    # Mutable scalar multiplication
    def __imul__(self, other):
        self.x *= other
        self.y *= other
        return self

    def __str__(self):
        return "Vector2(%f, %f)" % (self.x, self.y)


# The most basic physical body, a point mass that can have forces applied
class PointMass:
    def __init__(self, x, y, m):
        # Linear motion/mass: position, velocity, mass
        self.p = Vector2(x, y)
        self.v = Vector2(0, 0)
        self.m = m

    # Update by time
    def tick(self, delta_t):
        self.p += delta_t * self.v

    # Apply a force
    def apply_force(self, force, delta_t):
        a = force * (1/self.m)
        self.v += delta_t * a

    def __str__(self):
        return "PointMass(%f, %f)[mass %f, velocity (%f, %f)]" % (self.p.x, self.p.y, self.m, self.v.x, self.v.y)


# A solid body?
class Body(PointMass):
    def __init__(self, x, y, m, ang):
        # Linear motion/mass: position of center mass, velocity, mass
        self.p = Vector2(x, y)
        self.v = Vector2(0, 0)
        self.m = m
        # Angular motion: angle, angular speed, rotational inertia
        self.rp = ang
        self.rv = 0
        self.rm = m

    # Update by time
    def tick(self, delta_t):
        self.p += delta_t * self.v
        self.rp += delta_t * self.rv

    # Apply a force at a location
    def apply_force(self, force, p_force, delta_t):
        # Linear
        a = force * (1/self.m)
        self.v += delta_t * a
        # Angular
        lever_arm = p_force - self.p
        phi = lever_arm.ang_to(force)
        torque = math.sin(phi) * abs(force) * abs(lever_arm)
        a = torque * (1/self.rm)
        self.rv += delta_t * a

    def __str__(self):
        return "Body(%f, %f)[mass %f, vel (%f, %f), ang %f, angv %f]" % (self.p.x, self.p.y, self.m, self.v.x, self.v.y, self.rp, self.rv)


# A physical material
class Material:
    def __init__(self, density):
        self.density = density


class CircleBody(Body):
    def __init__(self, x, y, r, mat):
        self.p = Vector2(x, y)
        self.v = Vector2(0, 0)
        self.r = r
        self.m = mat.density * math.pi * r**2
        self.rp = 0
        self.rv = 0
        self.rm = (1/2) * self.m * r**2

    # Collision with a fellow CircleBody
    def collide_similar(self, other):
        dist = math.sqrt((self.x - other.x)**2 + (self.y - other.y)**2)
        if dist < self.r + other.r:
            return True
        return False

    # Collision with a line segment
    def collide_lineseg(self, other):
        return False


# Testing
if __name__ == "__main__":
    a = Body(0, 0, 5, 0)
    a.apply_force(Vector2(-10, 0), Vector2(.2, 1.8), .5)
    a.tick(.5)
    print(a)
