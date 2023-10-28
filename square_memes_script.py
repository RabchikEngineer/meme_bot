from PIL import Image,ImageDraw,ImageFont
import json

config_path = 'config.json'

with open(config_path, 'r') as f:
    conf = json.load(f)

sizes=conf['sizes']
res = sizes['resolution']
x_full_add = int(res * sizes['x_full_add'] / 300)
y_full_add = int(res * sizes['y_full_add'] / 300)
y_text_add = int(res * sizes['y_text_add'] / 300)
y_text_indent = int(res * sizes['y_text_indent'] / 300)
x_indent = int(res * sizes['x_indent'] / 300)
y_indent = int(res * sizes['y_indent'] / 300)
big_text_size = int(res * sizes['big_text_size'] / 300)
small_text_size = int(res * sizes['small_text_size'] / 300)
rect_indent = int(res * sizes['rect_indent'] / 300)
rect_width = int(res * sizes['rect_width'] / 300)


if not hasattr(Image, 'Resampling'):  # Pillow<9.0
    Image.Resampling = Image


def get_sizes(draw,text,font):
    x0,y0,x1,y1=draw.textbbox((0, 0), text, font=font)
    w=x1-x0
    h=y1-y0
    return w,h


def get_font(size):
    return ImageFont.truetype(font='arial.ttf', size=size, encoding='unic')


def make_picture(text, filename):
    levels_num=text.count('\n\n')
    text_list=[a.split('\n') for a in text.split('\n\n')]
    text_list_extended=[]
    _=[[text_list_extended.append((a[i],"full" if i==0 else "text")) for i in range(len(a))] for a in text_list]
    filename_end = filename[:-4] + '_done.png'
    init_pic=True
    for text_single, mode in text_list_extended:
        if text_single.find("\n"):
            text_small="".join(text_single.split(sep='\n')[1:])
        if init_pic:
            image2 = Image.open(filename).convert('RGBA')
        else:
            image2 = Image.open(filename_end).convert('RGBA')
        x,y=image2.size
        image2=image2.resize((res,int(res*y/x)),Image.Resampling.LANCZOS)
        x,y=image2.size
        if mode=="full":
            font_size = big_text_size
            image=Image.new('RGBA', (x + x_full_add, y + y_full_add), (0, 0, 0))
            draw = ImageDraw.Draw(image)
            startx=int((x+x_indent)/2)-int(x/2)
            starty=int((y+y_indent)/2)-int(y/2)
            image.paste(image2,(startx,starty), image2)
            draw.rectangle((startx-rect_indent,starty-rect_indent,startx+x+rect_indent,starty+y+rect_indent),
                           width = rect_width, outline=(255,255,255))
            font = get_font(font_size)
            w, h = get_sizes(draw, text_single, font)
            while w>res:
                font = get_font(font_size)
                w, h = get_sizes(draw, text_single, font)
                font_size-=1
            draw.text((startx+int(x/2)-int(w/2),starty+y+y_text_indent-int(h/2)), text_single, font=font, fill=(255,255,255,255))
        else:
            font_size = small_text_size
            image=image=Image.new('RGBA',(x,y+y_text_add),(0,0,0))
            image.paste(image2, (0, 0), image2)
            draw = ImageDraw.Draw(image)
            font = get_font(font_size)
            w, h = get_sizes(draw, text_single, font)
            while w > res:
                font = get_font(font_size)
                w, h = get_sizes(draw, text_single, font)
                font_size -= 1
            draw.text((int(x/2)-int(w/2),y-int(h/2)), text_single, font=font, fill=(255,255,255,255))


        init_pic=False
        # image.show()
        # file_name=file_name[:-4]+'_done.png'
        image.save(filename_end,'PNG')
    return filename_end

# make_picture("some text big\nsome text small\nsome text small\n\nnext_text",'1.jpg')