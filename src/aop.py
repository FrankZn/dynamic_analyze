import rospy
from functools import wraps

def publisher_decorator(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        print('------ Publisher ------')
        return f(*args, **kwargs)
    return wrapper

rospy.Publisher.__init__ = publisher_decorator(rospy.Publisher.__init__)
