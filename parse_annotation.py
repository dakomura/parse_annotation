import openslide
import xml.etree.ElementTree as ET 
import os
from argparse import ArgumentParser
import sys

def get_option():
    argparser = ArgumentParser()
    
#    argparser.add_argument('path_to_annotation', help='')
    argparser.add_argument('path_to_openslide', help='') 
    argparser.add_argument('path_to_save_directory', help='') 
    
    
    argparser.add_argument('-d', '--debug', type=bool,
                           default=False,
                           help='Debug the application. Read 200000 lines.')
    argparser.add_argument('-b','--path_to_barcodes', type=str,
                           default='',
                           help='Debug the application. Read 200000 lines.')
    


    return argparser.parse_args()


def get_coordination(args):
    openslide_path = args.path_to_openslide
    annotation_file = "{}.ndpa".format(openslide_path)
    wsi=openslide.OpenSlide(openslide_path)
    tree = ET.parse(annotation_file) 
    mpp_x=float(wsi.properties['openslide.mpp-x'])
    mpp_y=float(wsi.properties['openslide.mpp-y'])
    annotations={}
    for idx,ndpviewstate in enumerate(tree.getiterator('ndpviewstate')):
        annot_type = int(ndpviewstate.find('annotation').get('closed'))
	if annot_type == 0: continue #not closed

        annotations[idx]=(ndpviewstate.find('annotation').get('color'),[])
        for point in ndpviewstate.find('annotation').find('pointlist'):
            x=int(point[0].text)
            y=int(point[1].text)
            
            openslide_x_nm_from_center=x-int(wsi.properties['hamamatsu.XOffsetFromSlideCentre'])
            openslide_y_nm_from_center=y-int(wsi.properties['hamamatsu.YOffsetFromSlideCentre'])
            openslide_x_nm_from_topleft=openslide_x_nm_from_center+int(wsi.properties['openslide.level[0].width'])*mpp_x*1000//2
            openslide_y_nm_from_topleft=openslide_y_nm_from_center+int(wsi.properties['openslide.level[0].height'])*mpp_y*1000//2
            openslide_x_pixels_from_topleft=openslide_x_nm_from_topleft//(1000*mpp_x)
            openslide_y_pixels_from_topleft=openslide_y_nm_from_topleft//(1000*mpp_y)
#            openslide_x_pixels_from_topleft=x//(1000*mpp_x)
#            openslide_y_pixels_from_topleft=y//(1000*mpp_y)
            
            annotations[idx][1].append((int(openslide_x_pixels_from_topleft),int(openslide_y_pixels_from_topleft)))
            
    return annotations



def annotation_to_string(annotations,openslide_path):
    file_name = os.path.basename(openslide_path)
    annotations_string=f'@{file_name}\n'
    for idx, (color, li) in annotations.items():
        length=len(li)
        annotations_string+=f'0 {idx} {length}\n'
        for (x,y) in li:
            annotations_string+=f'{x} {y}\n'
    return annotations_string


def save_txt(annotation_string,openslide_path,save_path):
    file_name = os.path.basename(openslide_path)
    directory_path=os.path.dirname(openslide_path)
    wsi_name= os.path.splitext(file_name)[0]
    kakutyosi=os.path.splitext(file_name)[1][1:]
    #save_path=f'./{wsi_name}_{kakutyosi}'
    filename = os.path.splitext(os.path.basename(openslide_path))[0]
    if not os.path.exists(save_path):
        os.mkdir(save_path)
    with open(os.path.join(save_path,filename+'.annot.txt'),mode='w') as f:
        f.write(annotation_string)
    return directory_path
    

def main():
    args=get_option()
    annotations=get_coordination(args)
    annotations_string = annotation_to_string(annotations, args.path_to_openslide)
    save_txt(annotations_string, args.path_to_openslide, args.path_to_save_directory)
    
main()    
