from solver.settings import MAX_VALUE
import colorama


class Colors:
    purple = '\033[95m'
    blue = '\033[94m'
    green = '\033[92m'
    yellow = '\033[93m'
    red = '\033[91m'
    white = '\033[1m'
    end = '\033[0m'


def format_content(figure:str, content:str):
    color = ''

    value = figure  if figure != ' ' else content

    match figure:
        case 'A':
            color = Colors.red
        case 'M':
            color = Colors.yellow
        case 'C':
            color = Colors.purple
        case 'T':
            color = Colors.green
        case 'H':
            color = Colors.green
        case _:
            color = Colors.white

    return color + f' {value} ' + Colors.end


def format_aoe_content(value:str):
    return '   ' if value != 'A' else Colors.red + ' A ' + Colors.end

def format_numerical_label(value:int):
    if value == MAX_VALUE:
        return '999'
    if value < 10:
        return f' {value} '
    return f'{value}'

def format_axial_coordinate(value:tuple[int,int]):
    return f'{value[0]}{value[1]}'

def format_initiative(value:int):
    if value == 0:
        return '   '
    if value < 10:
        return f'{Colors.blue} {value} {Colors.end}'
    return f'{Colors.blue}{value}{Colors.end}'

def format_los(value:int):
    return '   ' if value else ' # '

def format_aoe(value:int):
    return ' % ' if value else '   '

def top_edge_glyph(walls:list[list[bool]], location:int, edge:int):
    return '___' if walls[location][edge] else '...'

def north_edge_glyph(walls:list[list[bool]], location:int, edge:int):
    return '/' if walls[location][edge] else '\''

def south_edge_glyph(walls:list[list[bool]], location:int, edge:int):
    return '\\' if walls[location][edge] else '\''

def print_map(grid_width:int, grid_height:int, walls:list[list[bool]], top_label:list[str], bottom_label:list[str], extra_label:list[str]=[]):
    colorama.init()
    grid_size = grid_width * grid_height

    if not extra_label:
        extra_label = [' '] * grid_size

    extra_label = [Colors.yellow + extra_label[i] + Colors.end for i in range(0, grid_size)]

    out = ''
    for j in range(0, grid_width // 2):
        location = 2 * grid_height + 2 * j * grid_height - 1
        out += f'       {top_edge_glyph(walls, location, 1)}'

    print(out)

    out = ' '
    for j in range(0, grid_width // 2):
        location = 2 * grid_height + 2 * j * grid_height - 1
        out += f'     {north_edge_glyph(walls, location, 2)} {extra_label[location]} {south_edge_glyph(walls, location, 0)}'
        
    print(out)

    out = '  '
    for j in range(0, grid_width // 2):
        label_location = 2 * grid_height + 2 * j * grid_height - 1
        base_edge_location = grid_height + 2 * j * grid_height - 1
        out += f'{top_edge_glyph(walls, base_edge_location, 1)}{north_edge_glyph(walls, label_location, 2)} {top_label[label_location]} {south_edge_glyph(walls, label_location, 0)}'

    if grid_width % 2:
        base_edge_location = grid_height + (grid_width - 1) * grid_height - 1
        out += f'{top_edge_glyph(walls, base_edge_location, 1)}'

    print(out)

    for i in range(0, grid_height - 1):
        left_location = grid_height - i - 1

        out = f' {north_edge_glyph(walls, left_location, 2)}'
        for j in range(0, grid_width // 2):
            extra_label_location = grid_height - i + j * 2 * grid_height - 1
            label_location = 2 * grid_height - i + j * 2 * grid_height - 1
            out += f' {extra_label[extra_label_location]} {south_edge_glyph(walls, extra_label_location, 0)} {bottom_label[label_location]} {north_edge_glyph(walls, label_location, 5)}'

        if grid_width % 2:
            extra_label_location = grid_height - \
                i + (grid_width - 1) * grid_height - 1
            out += f' {extra_label[extra_label_location]} {south_edge_glyph(walls, extra_label_location, 0)}'
        print(out)

        out = f'{north_edge_glyph(walls, left_location, 2)}'
        for j in range(0, grid_width // 2):
            label_location = grid_height - i + j * 2 * grid_height - 1
            edge_location = 2 * grid_height - i + j * 2 * grid_height - 1
            out += f' {top_label[label_location]} {south_edge_glyph(walls, label_location, 0)}{top_edge_glyph(walls, edge_location, 4)}{north_edge_glyph(walls, edge_location, 5)}'
        if grid_width % 2:
            label_location = grid_height - i + (grid_width - 1) * grid_height - 1
            out += f' {top_label[label_location]} {south_edge_glyph(walls, label_location, 0)}'
        print(out)

        out = f'{south_edge_glyph(walls, left_location, 3)}'
        for j in range(0, grid_width // 2):
            label_location = grid_height - i + j * 2 * grid_height - 1
            edge_location = 2 * grid_height - i + j * 2 * grid_height - 2
            out += f' {bottom_label[label_location]} {north_edge_glyph(walls, label_location, 5)} { extra_label[edge_location]} {south_edge_glyph(walls, edge_location, 0)}'
        if grid_width % 2:
            label_location = grid_height - i + (grid_width - 1) * grid_height - 1
            out += f' {bottom_label[label_location]} {north_edge_glyph(walls, label_location, 5)}'
        print(out)

        out = f' {south_edge_glyph(walls, left_location, 3)}'
        for j in range(0, grid_width // 2):
            label_location = 2 * grid_height - i + j * 2 * grid_height - 2
            base_edge_location = grid_height - i + j * 2 * grid_height - 1
            out += f'{top_edge_glyph(walls, base_edge_location, 4)}{north_edge_glyph(walls, base_edge_location, 5)} {top_label[label_location]} {south_edge_glyph(walls, label_location, 0)}' 

        if grid_width % 2:
            base_edge_location = grid_height - i + (grid_width - 1) * grid_height - 1
            out += f'{top_edge_glyph(walls, base_edge_location, 4)}{north_edge_glyph(walls, base_edge_location, 5)}'
        print(out)

    out = f' {north_edge_glyph(walls, 0, 2)}'
    for j in range(0, grid_width // 2):
        location = grid_height + j * 2 * grid_height
        label_location = j * 2 * grid_height
        out += f' {extra_label[label_location]} {south_edge_glyph(walls, label_location, 0)} {bottom_label[location]} {north_edge_glyph(walls, location, 5)}'
    if grid_width % 2:
        label_location = (grid_width - 1) * grid_height
        out += f' {extra_label[label_location]} {south_edge_glyph(walls, label_location, 0)}'
    print(out)

    out = f'{north_edge_glyph(walls, 0, 2)}'
    for j in range(0, grid_width // 2):
        label_location = j * 2 * grid_height
        edge_location = grid_height + j * 2 * grid_height
        out += f' {top_label[label_location]} {south_edge_glyph(walls, label_location, 0)}{top_edge_glyph(walls, edge_location, 4)}{north_edge_glyph(walls, edge_location, 5)}'

    if grid_width % 2:
        label_location = (grid_width - 1) * grid_height
        out += f' {top_label[label_location]} {south_edge_glyph(walls, label_location, 0)}'
    print(out)

    out = ''
    for j in range(0, grid_width // 2):
        location = j * 2 * grid_height
        out += f'{south_edge_glyph(walls, location, 3)} {bottom_label[location]} {north_edge_glyph(walls, location, 5)}   '
    if grid_width % 2:
        location = (grid_width - 1) * grid_height
        out += f'{south_edge_glyph(walls, location, 3)} {bottom_label[location]} {north_edge_glyph(walls, location, 5)}'
    print(out)

    out = ''
    for j in range(0, grid_width // 2):
        location = j * 2 * grid_height
        out += f' {south_edge_glyph(walls, location, 3)}{top_edge_glyph(walls, location, 4)}{north_edge_glyph(walls, location, 5)}    '
    if grid_width % 2:
        location = (grid_width - 1) * grid_height
        out += f' {south_edge_glyph(walls, location, 3)}{top_edge_glyph(walls, location, 4)}{north_edge_glyph(walls, location, 5)}'
    print(out)
