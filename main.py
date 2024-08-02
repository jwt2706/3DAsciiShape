import argparse
import math
import curses
import time
from PIL import Image, ImageDraw

def parse_arguments():
    parser = argparse.ArgumentParser(description="3D Shape Renderer")
    parser.add_argument("shape", choices=["cube", "pyramid"], nargs='?', default="cube", help="Shape to render")
    parser.add_argument("size", type=int, nargs='?', default=40, help="Size of the shape")
    parser.add_argument("--x", type=float, default=0, help="Rotation angle around X-axis in degrees")
    parser.add_argument("--y", type=float, default=0, help="Rotation angle around Y-axis in degrees")
    parser.add_argument("--z", type=float, default=0, help="Rotation angle around Z-axis in degrees")
    parser.add_argument("--wireframe", action="store_true", help="Render as wireframe")
    parser.add_argument("--auto", action="store_true", help="Enable automatic rotation")
    return parser.parse_args()


# --- SHAPES ---
def cube(size):
    half = size / 2
    vertices = [
        (-half, -half, -half),
        (half, -half, -half),
        (half, half, -half),
        (-half, half, -half),
        (-half, -half, half),
        (half, -half, half),
        (half, half, half),
        (-half, half, half)
    ]
    edges = [
        (0, 1), (1, 2), (2, 3), (3, 0),  #bottom edges
        (4, 5), (5, 6), (6, 7), (7, 4),  #top edges
        (0, 4), (1, 5), (2, 6), (3, 7)   #vertical edges
    ]
    faces = [
        (0, 1, 2, 3),  #bottom face
        (4, 5, 6, 7),  #top face
        (0, 1, 5, 4),  #front face
        (2, 3, 7, 6),  #back face
        (0, 3, 7, 4),  #left face
        (1, 2, 6, 5)   #right face
    ]
    return vertices, edges, faces

def pyramid(size):
    half = size / 2
    vertices = [
        (0, half, 0),
        (-half, -half, -half), (half, -half, -half), (half, -half, half), (-half, -half, half)
    ]
    edges = [
        (0, 1), (0, 2), (0, 3), (0, 4),  #vertical edges
        (1, 2), (2, 3), (3, 4), (4, 1)   #base edges
    ]
    faces = [
        (0, 1, 2), (0, 2, 3), (0, 3, 4), (0, 4, 1),  #side faces
        (1, 2, 3, 4)  #base face
    ]
    return vertices, edges, faces

def rotate(vertex, angle_x, angle_y, angle_z):
    x, y, z = vertex
    rad_x, rad_y, rad_z = math.radians(angle_x), math.radians(angle_y), math.radians(angle_z)
    cos_x, sin_x = math.cos(rad_x), math.sin(rad_x)
    cos_y, sin_y = math.cos(rad_y), math.sin(rad_y)
    cos_z, sin_z = math.cos(rad_z), math.sin(rad_z)
    
    y, z = y * cos_x - z * sin_x, y * sin_x + z * cos_x
    x, z = x * cos_y - z * sin_y, x * sin_y + z * cos_y
    x, y = x * cos_z - y * sin_z, x * sin_z + y * cos_z
    
    return (x, y, z)

def project_vertex(vertex):
    x, y, _ = vertex #ignore z coord
    return (int(x), int(y))

def draw_shape(vertices, edges, faces, angle_x, angle_y, angle_z, img_size, wireframe):
    img = Image.new('L', (img_size, img_size), color=255)
    draw = ImageDraw.Draw(img)
    
    rotated_vertices = [rotate(v, angle_x, angle_y, angle_z) for v in vertices]
    
    if wireframe:
        for edge in edges:
            start, end = edge
            x1, y1 = project_vertex(rotated_vertices[start])
            x2, y2 = project_vertex(rotated_vertices[end])
            draw.line((x1 + img_size // 2, y1 + img_size // 2, x2 + img_size // 2, y2 + img_size // 2), fill=0, width=3)
    else:
        for face in faces:
            polygon = [project_vertex(rotated_vertices[vertex]) for vertex in face]
            polygon = [(x + img_size // 2, y + img_size // 2) for x, y in polygon]
            draw.polygon(polygon, outline=0, fill=150)
        for edge in edges:
            start, end = edge
            x1, y1 = project_vertex(rotated_vertices[start])
            x2, y2 = project_vertex(rotated_vertices[end])
            draw.line((x1 + img_size // 2, y1 + img_size // 2, x2 + img_size // 2, y2 + img_size // 2), fill=0, width=3)  #Dark edges
    return img

def image_to_ascii(img, chars):
    img = img.resize((img.width // 2, img.height // 2))
    pixels = img.getdata()
    new_pixels = ''.join(chars[pixel // 25] for pixel in pixels)
    
    new_width = img.width
    ascii_image = [new_pixels[index:index + new_width] for index in range(0, len(new_pixels), new_width)]
    return "\n".join(ascii_image)

def render_shape(stdscr, vertices, edges, faces, angle_x, angle_y, angle_z, img_size, wireframe, auto_rotate):
    stdscr.clear()
    img = draw_shape(vertices, edges, faces, angle_x, angle_y, angle_z, img_size, wireframe)
    chars = ["@", "#", "S", "%", "?", "*", "+", ";", ":", ".", " "]
    ascii_art = image_to_ascii(img, chars)
    
    max_y, max_x = stdscr.getmaxyx()
    
    ascii_lines = ascii_art.split('\n')
    
    #ensure the ASCII art fits within the terminal dimensions
    for i, line in enumerate(ascii_lines):
        if i >= max_y:
            break
        stdscr.addstr(i, 0, line[:max_x])
    
    stdscr.refresh()

    if auto_rotate:
        return angle_x + 1, angle_y + 0.8, angle_z + 0.3
    else:
        key = stdscr.getch()
        if key == curses.KEY_UP:
            angle_x += 5
        elif key == curses.KEY_DOWN:
            angle_x -= 5
        elif key == curses.KEY_LEFT:
            angle_y -= 5
        elif key == curses.KEY_RIGHT:
            angle_y += 5
        return angle_x, angle_y, angle_z

def main(stdscr):
    args = parse_arguments()
    if args.shape == "cube":
        vertices, edges, faces = cube(args.size)
    elif args.shape == "pyramid":
        vertices, edges, faces = pyramid(args.size)
    
    img_size = 100
    angle_x, angle_y, angle_z = args.x, args.y, args.z
    
    curses.curs_set(0)
    stdscr.nodelay(1)
    stdscr.timeout(100)
    
    while True:
        angle_x, angle_y, angle_z = render_shape(stdscr, vertices, edges, faces, angle_x, angle_y, angle_z, img_size, args.wireframe, args.auto)
        time.sleep(1/100)

if __name__ == "__main__":
    curses.wrapper(main)