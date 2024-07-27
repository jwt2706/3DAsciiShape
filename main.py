import argparse
import math
import curses
from PIL import Image, ImageDraw

def parse_arguments():
    parser = argparse.ArgumentParser(description="3D Shape Renderer")
    parser.add_argument("shape", choices=["cube", "pyramid"], help="Shape to render")
    parser.add_argument("size", type=int, help="Size of the shape")
    parser.add_argument("--x", type=float, default=0, help="Rotation angle around X-axis in degrees")
    parser.add_argument("--y", type=float, default=0, help="Rotation angle around Y-axis in degrees")
    parser.add_argument("--z", type=float, default=0, help="Rotation angle around Z-axis in degrees")
    parser.add_argument("--wireframe", action="store_true", help="Render as wireframe")
    return parser.parse_args()

def generate_cube(size):
    half = size / 2
    vertices = [
        (-half, -half, -half), (half, -half, -half), (half, half, -half), (-half, half, -half),
        (-half, -half, half), (half, -half, half), (half, half, half), (-half, half, half)
    ]
    edges = [
        (0, 1), (1, 2), (2, 3), (3, 0),
        (4, 5), (5, 6), (6, 7), (7, 4),
        (0, 4), (1, 5), (2, 6), (3, 7)
    ]
    faces = [
        (0, 1, 2, 3), (4, 5, 6, 7), (0, 1, 5, 4),
        (2, 3, 7, 6), (0, 3, 7, 4), (1, 2, 6, 5)
    ]
    return vertices, edges, faces

def generate_pyramid(size):
    half = size / 2
    vertices = [
        (0, half, 0),  # Top vertex
        (-half, -half, -half), (half, -half, -half), (half, -half, half), (-half, -half, half)
    ]
    edges = [
        (0, 1), (0, 2), (0, 3), (0, 4),
        (1, 2), (2, 3), (3, 4), (4, 1)
    ]
    faces = [
        (0, 1, 2), (0, 2, 3), (0, 3, 4), (0, 4, 1),
        (1, 2, 3, 4)
    ]
    return vertices, edges, faces

def rotate_y(vertex, angle):
    x, y, z = vertex
    rad = math.radians(angle)
    cos_a = math.cos(rad)
    sin_a = math.sin(rad)
    x_new = x * cos_a - z * sin_a
    z_new = x * sin_a + z * cos_a
    return (x_new, y, z_new)

def rotate_x(vertex, angle):
    x, y, z = vertex
    rad = math.radians(angle)
    cos_a = math.cos(rad)
    sin_a = math.sin(rad)
    y_new = y * cos_a - z * sin_a
    z_new = y * sin_a + z * cos_a
    return (x, y_new, z_new)

def rotate_z(vertex, angle):
    x, y, z = vertex
    rad = math.radians(angle)
    cos_a = math.cos(rad)
    sin_a = math.sin(rad)
    x_new = x * cos_a - y * sin_a
    y_new = x * sin_a + y * cos_a
    return (x_new, y_new, z)

def project_vertex(vertex):
    x, y, z = vertex
    return (int(x), int(y))

def draw_shape(vertices, edges, faces, angle_x, angle_y, angle_z, img_size, wireframe):
    img = Image.new('L', (img_size, img_size), color=255)
    draw = ImageDraw.Draw(img)
    
    rotated_vertices = [rotate_x(rotate_y(rotate_z(v, angle_z), angle_y), angle_x) for v in vertices]
    
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
            draw.line((x1 + img_size // 2, y1 + img_size // 2, x2 + img_size // 2, y2 + img_size // 2), fill=0, width=3)  # Dark edges
    return img

def image_to_ascii(img, chars):
    img = img.resize((img.width // 2, img.height // 2))
    pixels = img.getdata()
    new_pixels = [chars[pixel // 25] for pixel in pixels]
    new_pixels = ''.join(new_pixels)
    
    new_width = img.width
    ascii_image = [new_pixels[index:index + new_width] for index in range(0, len(new_pixels), new_width)]
    return "\n".join(ascii_image)

def render_shape(stdscr, vertices, edges, faces, angle_x, angle_y, angle_z, img_size, wireframe):
    stdscr.clear()
    img = draw_shape(vertices, edges, faces, angle_x, angle_y, angle_z, img_size, wireframe)
    chars = ["@", "#", "S", "%", "?", "*", "+", ";", ":", ",", "."]
    ascii_art = image_to_ascii(img, chars)
    
    max_y, max_x = stdscr.getmaxyx()
    
    ascii_lines = ascii_art.split('\n')
    
    # Ensure the ASCII art fits within the terminal dimensions
    for i, line in enumerate(ascii_lines):
        if i >= max_y:
            break
        stdscr.addstr(i, 0, line[:max_x])
    
    stdscr.refresh()

def main(stdscr):
    args = parse_arguments()
    if args.shape == "cube":
        vertices, edges, faces = generate_cube(args.size)
    elif args.shape == "pyramid":
        vertices, edges, faces = generate_pyramid(args.size)
    
    img_size = 100
    angle_x, angle_y, angle_z = args.x, args.y, args.z
    
    curses.curs_set(0)
    stdscr.nodelay(1)
    stdscr.timeout(100)
    
    while True:
        render_shape(stdscr, vertices, edges, faces, angle_x, angle_y, angle_z, img_size, args.wireframe)
        
        key = stdscr.getch()
        if key == curses.KEY_UP:
            angle_x -= 5
        elif key == curses.KEY_DOWN:
            angle_x += 5
        elif key == curses.KEY_LEFT:
            angle_y -= 5
        elif key == curses.KEY_RIGHT:
            angle_y += 5
        elif key == curses.KEY_PPAGE:
            angle_z -= 5
        elif key == curses.KEY_NPAGE:
            angle_z += 5
        elif key == ord('q'):
            break

if __name__ == "__main__":
    curses.wrapper(main)