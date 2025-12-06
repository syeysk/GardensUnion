import math

from gi.repository import Gtk
from sqlalchemy import select, func

from db import models


class CircleWidget(Gtk.DrawingArea):
    def __init__(self):
        Gtk.DrawingArea.__init__(self)
        self.set_draw_func(self.draw)
        self.props.content_height = 800
        self.props.content_width = 800

    # cario.Context: https://pycairo.readthedocs.io/en/latest/reference/context.html
    def draw(self, widget, context, window_w, window_h):
        context.set_source_rgb(0.7, 0.7, 0.7)
        context.set_line_width(1)
        
        deg = math.pi / 180
        padding = 10
        circle_center_x = window_w / 2
        circle_center_y = window_h / 2
        radius = min(window_w, window_h) / 2 - padding

        # draw circles

        radius_partial = radius / len(models.CIRCLES)
        for circle_index, (circle_id, circle_name) in enumerate(models.CIRCLES.items(), 1):
            context.new_sub_path()
            context.arc(circle_center_x, circle_center_y, radius_partial * circle_index, 0, 360 * deg)
            context.stroke()

        # draw sectors (rotate a point around other one: https://foxford.ru/wiki/informatika/povorot-tochki)
        
        degree_partial = 360 / models.Sector.objects.count()
        diff_y = padding - circle_center_y
        for index_sector, sector in enumerate(models.Sector.objects.all()):
            rotate_degree = degree_partial * index_sector * deg
            x = circle_center_x - diff_y * math.sin(rotate_degree)
            y = circle_center_y + diff_y * math.cos(rotate_degree)
            context.new_sub_path()
            context.move_to(circle_center_x, circle_center_y)
            context.line_to(x, y)
            context.stroke()
        


class CircleMapWindow(Gtk.ApplicationWindow):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        circle_widget = CircleWidget()
        self.set_child(circle_widget)
