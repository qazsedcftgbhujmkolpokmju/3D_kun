import time
import numpy as np
from multiprocessing import Pool
from osgeo import gdal, osr
import matplotlib.path as mplPath
from rtree import index
from svg.path import parse_path
from xml.dom import minidom
from tqdm import tqdm
import rasterio
import matplotlib.pyplot as plt

# 1. 读取输入文件
input_path = r"..." # 缓存文件路径
with open(input_path, "r") as f:
    t = f.read().splitlines()

# 2. 解析SVG文件
doc = minidom.parse(t[1])

# 获取SVG元素的宽和高
svg_elem = doc.getElementsByTagName('svg')[0]
width_str = svg_elem.getAttribute('width').replace('px', '')
height_str = svg_elem.getAttribute('height').replace('px', '')
width = float(width_str)
height = float(height_str)

# 获取并处理视口尺寸
view_box = svg_elem.getAttribute('viewBox')
if view_box:
    _, _, view_width, view_height = map(float, view_box.split())
else:
    view_width, view_height = width, height

scale_x = width / view_width
scale_y = height / view_height

# 解析所有的path元素
path_strings = [path.getAttribute('d') for path in doc.getElementsByTagName('path')]
doc.unlink()

# 3. 创建空间索引
idx = index.Index()
paths = []

for i, path_string in enumerate(path_strings):
    path_data = parse_path(path_string)
    verts = [(segment.start.real * scale_x, segment.start.imag * scale_y) for segment in path_data]

    min_x = min(v[0] for v in verts)
    min_y = min(v[1] for v in verts)
    max_x = max(v[0] for v in verts)
    max_y = max(v[1] for v in verts)

    path = mplPath.Path(np.array(verts))
    paths.append((path, i + 1))
    idx.insert(i, (min_x, min_y, max_x, max_y))

# 初始化高程数据
elevation = np.zeros((int(height), int(width)))

# 4. 处理每一行，确定每个像素的高程值
def process_row(y):
    row_elevation = np.zeros(int(width))
    for x in range(int(width)):
        path_ids = list(idx.intersection((x, y, x, y)))
        for path_id in path_ids:
            path, h = paths[path_id]
            if path.contains_point((x, y)):
                row_elevation[x] = h
    return row_elevation

if __name__ == "__main__":
    with Pool() as p:
        elevation_rows = list(tqdm(p.imap(process_row, range(int(height))), total=int(height)))
        elevation = np.array(elevation_rows)

    # 5. 创建GeoTIFF
    driver = gdal.GetDriverByName("GTiff")
    output_path = t[2] + '/out_dem' + t[0] + '.tif'
    ds = driver.Create(output_path, int(width), int(height), 1, gdal.GDT_Float32)
    srs = osr.SpatialReference()
    srs.ImportFromEPSG(4326)
    ds.SetProjection(srs.ExportToWkt())
    ds.SetGeoTransform((0, 0.0001, 0, height, 0, -0.0001))
    ds.GetRasterBand(1).WriteArray(elevation)
    ds = None

    # 延迟确保文件写入完成
    time.sleep(0.5)

    # 6. 读取和显示高程数据
    with rasterio.open(output_path) as dataset:
        elevation_data = dataset.read(1)
        transform = dataset.transform

    x = np.arange(0, elevation_data.shape[1])
    y = np.arange(0, elevation_data.shape[0])
    x, y = np.meshgrid(x, y)
    x = width - x

    aspect_ratio = width / height
    fig = plt.figure(figsize=(16 * aspect_ratio, 14))
    ax = fig.add_subplot(111, projection='3d', box_aspect=[aspect_ratio, 1, 0.3])
    ax.view_init(elev=70, azim=90)
    surf = ax.plot_surface(x, y, elevation_data, cmap='jet', edgecolor='none', rstride=1, cstride=1, linewidth=0, antialiased=False)

    ax.set_xlabel('X')
    ax.set_ylabel('Y')
    ax.set_zlabel('Z')
    ax.set_title('3D Ji Ni Tai Mei' + t[0], fontsize=20)

    colorbar = fig.colorbar(surf, ax=ax, shrink=0.5, aspect=10)
    colorbar.set_ticks(np.linspace(elevation_data.min(), elevation_data.max(), 10))

    x_bars = x[-1, :]
    y_bars = np.full_like(x_bars, np.max(y))
    z_bars = np.zeros_like(x_bars)
    dx = dy = 1
    dz = elevation_data[-1, :]
    for i in range(len(x_bars)):
        ax.bar3d(x_bars[i], y_bars[i], z_bars[i], dx, dy, dz[i], color='aqua', zsort='average')

    # 7. 保存3D图像
    plt.savefig(t[2] + '/3d_elevation_plot' + t[0] + '.png', dpi=400)
