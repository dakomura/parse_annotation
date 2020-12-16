import openslide
import xml.etree.ElementTree as ET
import os
from argparse import ArgumentParser
import random
import math
from PIL import Image

random.seed(10)


def get_option():
    argparser = ArgumentParser()

    #    argparser.add_argument('path_to_annotation', help='')
    argparser.add_argument('path_to_openslide', help='')
    argparser.add_argument('path_to_save_directory', help='')

    argparser.add_argument('-d', '--debug', type=bool,
                           default=False,
                           help='Debug the application. Read 200000 lines.')
    argparser.add_argument('-b', '--path_to_barcodes', type=str,
                           default='',
                           help='Debug the application. Read 200000 lines.')

    argparser.add_argument('-s', '--srcsize', type=int, default=512)
    argparser.add_argument('-p', '--patchsize', type=int, default=512)
    argparser.add_argument('-n', '--numpatch', type=int, default=30)

    return argparser.parse_args()


def get_coordination(args):
    openslide_path = args.path_to_openslide
    annotation_file = "{}.ndpa".format(openslide_path)
    wsi = openslide.OpenSlide(openslide_path)
    tree = ET.parse(annotation_file)
    mpp_x = float(wsi.properties['openslide.mpp-x'])
    mpp_y = float(wsi.properties['openslide.mpp-y'])
    annotations = {}
    total_len = 0

    prev_openslide_x_pixels_from_topleft, prev_openslide_y_pixels_from_topleft = 0, 0

    for idx, ndpviewstate in enumerate(tree.iter('ndpviewstate')):
        annot_type = ndpviewstate.find('annotation').get('displayname')
        if annot_type != "AnnotateFreehandLine":
            continue  # not closed

        annotations[idx] = (ndpviewstate.find('annotation').get('color'), [])

        for i, point in enumerate(ndpviewstate.find('annotation').find('pointlist')):
            x = int(point[0].text)
            y = int(point[1].text)

            openslide_x_nm_from_center = x - int(wsi.properties['hamamatsu.XOffsetFromSlideCentre'])
            openslide_y_nm_from_center = y - int(wsi.properties['hamamatsu.YOffsetFromSlideCentre'])
            openslide_x_nm_from_topleft = openslide_x_nm_from_center + int(
                wsi.properties['openslide.level[0].width']) * mpp_x * 1000 // 2
            openslide_y_nm_from_topleft = openslide_y_nm_from_center + int(
                wsi.properties['openslide.level[0].height']) * mpp_y * 1000 // 2
            openslide_x_pixels_from_topleft = openslide_x_nm_from_topleft // (1000 * mpp_x)
            openslide_y_pixels_from_topleft = openslide_y_nm_from_topleft // (1000 * mpp_y)

            if i > 0:
                annotations[idx][1].append(((int(prev_openslide_x_pixels_from_topleft),
                                            int(prev_openslide_y_pixels_from_topleft)),
                                           (int(openslide_x_pixels_from_topleft),
                                            int(openslide_y_pixels_from_topleft))))

                total_len += math.sqrt(
                    (int(prev_openslide_x_pixels_from_topleft) - int(openslide_x_pixels_from_topleft)) ** 2 + \
                    (int(prev_openslide_y_pixels_from_topleft) - int(openslide_y_pixels_from_topleft)) ** 2)

            prev_openslide_x_pixels_from_topleft = openslide_x_pixels_from_topleft
            prev_openslide_y_pixels_from_topleft = openslide_y_pixels_from_topleft

    return annotations, int(total_len)


def line_sampler(x1, y1, x2, y2):
    alpha = random.uniform(0, 1)
    xx = x1 + int(float(x2 - x1) * alpha)
    yy = y1 + int(float(y2 - y1) * alpha)

    return xx, yy


def crop_center(pil_img, crop_width, crop_height):
    img_width, img_height = pil_img.size
    return pil_img.crop(((img_width - crop_width) // 2,
                         (img_height - crop_height) // 2,
                         (img_width + crop_width) // 2,
                         (img_height + crop_height) // 2))


def save_patch(annotation, openslide_path, save_path, srcsize, patchsize, numpatch, total_len):
    directory_path = os.path.dirname(openslide_path)
    filename = os.path.splitext(os.path.basename(openslide_path))[0]
    save_path = "{}/{}".format(save_path, filename)
    os.makedirs(save_path, exist_ok=True)

    init_srcsize = 2 * srcsize

    op = openslide.OpenSlide(openslide_path)

    #select patches with probability proportional to the line length
    selected = random.sample(range(total_len), k=numpatch)
    current_len = 0

    for idx, annot_val in annotation.items():
        pos_array = annot_val[1]
        for k, pos in enumerate(pos_array):
            assert isinstance(pos, tuple)
            ((x1, y1), (x2, y2)) = pos

            l = math.sqrt((x1-x2)**2 + (y1-y2)**2) #line length
            n = len([x for x in selected if x >= current_len and x <= current_len + l])
            current_len += l

            for i in range(n):
                xx, yy = line_sampler(x1, y1, x2, y2)
                # extract patch
                init_patch = op.read_region(
                    (int(xx - init_srcsize / 2),
                     int(yy - init_srcsize / 2)),
                     0, (init_srcsize, init_srcsize))
                # random rotation
                patch = init_patch.rotate(random.randint(0, 360))
                patch = crop_center(patch, srcsize, srcsize).resize((patchsize, patchsize), Image.BICUBIC)
                patch.save("{}/{}_{}_{}_cyst.png".format(save_path, idx, k, i))


def main():
    args = get_option()
    annotations, total_len = get_coordination(args)
    save_patch(annotations,
               args.path_to_openslide,
               args.path_to_save_directory,
               args.srcsize,
               args.patchsize,
               args.numpatch,
               total_len)


main()
