from PIL import Image,ImageDraw,ImageFont
from auxiliary import config_path
import json
import auxiliary as aux

with open(config_path, 'r', encoding='utf-8') as f:
    conf = json.load(f)

fonts_dir=conf['directories']['fonts']


if not hasattr(Image, 'Resampling'):  # Pillow<9.0
    Image.Resampling = Image


class PicMaker:

    def __init__(self, config):

        sizes = config['sizes']
        res = sizes['resolution']
        self.res=res
        self.x_full_add = int(res * sizes['x_full_add'] / 300)
        self.y_full_add = int(res * sizes['y_full_add'] / 300)
        self.y_text_add = int(res * sizes['y_text_add'] / 300)
        self.y_text_indent = int(res * sizes['y_text_indent'] / 300)
        self.x_indent = int(res * sizes['x_indent'] / 300)
        self.y_indent = int(res * sizes['y_indent'] / 300)
        self.big_text_size = int(res * sizes['big_text_size'] / 300)
        self.small_text_size = int(res * sizes['small_text_size'] / 300)
        self.rect_indent = int(res * sizes['rect_indent'] / 300)
        self.rect_width = int(res * sizes['rect_width'] / 300)

        self.font_filename=fonts_dir+config["font"]

    def _get_sizes(self,draw,text,font):
        x0,y0,x1,y1=draw.textbbox((0, 0), text, font=font)
        w=x1-x0
        h=y1-y0
        return w,h

    def _get_font(self,size):
        return ImageFont.truetype(font=self.font_filename, size=size, encoding='unic')

    def make_picture(self, text, filename):
        # levels_num=text.count('\n\n')
        text_list=[a.split('\n') for a in text.split('\n\n')]
        text_list_extended=[]
        _=[[text_list_extended.append((a[i],"full" if i==0 else "text")) for i in range(len(a))] for a in text_list]
        filename_end = filename[:-4] + '_done.png'
        init_pic=True
        for text_single, mode in text_list_extended:
            # if text_single.find("\n"):
            #     text_small="".join(text_single.split(sep='\n')[1:])
            if init_pic:
                image2 = Image.open(filename).convert('RGBA')
            else:
                image2 = Image.open(filename_end).convert('RGBA')
            x,y=image2.size
            image2=image2.resize((self.res,int(self.res*y/x)),Image.Resampling.LANCZOS)
            x,y=image2.size
            if mode=="full":
                font_size = self.big_text_size
                image=Image.new('RGBA', (x + self.x_full_add, y + self.y_full_add), (0, 0, 0))
                draw = ImageDraw.Draw(image)
                startx=int((x+self.x_indent)/2)-int(x/2)
                starty=int((y+self.y_indent)/2)-int(y/2)
                image.paste(image2,(startx,starty), image2)
                draw.rectangle((startx-self.rect_indent,starty-self.rect_indent,
                                startx+x+self.rect_indent,starty+y+self.rect_indent),
                                width = self.rect_width, outline=(255,255,255))
                font = self._get_font(font_size)
                w, h = self._get_sizes(draw, text_single, font)
                while w>self.res:
                    font = self._get_font(font_size)
                    w, h = self._get_sizes(draw, text_single, font)
                    font_size-=1
                draw.text((startx+int(x/2)-int(w/2),starty+y+self.y_text_indent-int(h/2)), text_single, font=font, fill=(255,255,255,255))
            else:
                font_size = self.small_text_size
                image=image=Image.new('RGBA',(x,y+self.y_text_add),(0,0,0))
                image.paste(image2, (0, 0), image2)
                draw = ImageDraw.Draw(image)
                font = self._get_font(font_size)
                w, h = self._get_sizes(draw, text_single, font)
                while w > self.res:
                    font = self._get_font(font_size)
                    w, h = self._get_sizes(draw, text_single, font)
                    font_size -= 1
                draw.text((int(x/2)-int(w/2),y-int(h/2)), text_single, font=font, fill=(255,255,255,255))


            init_pic=False
            # image.show()
            # file_name=file_name[:-4]+'_done.png'
            image.save(filename_end,'PNG')
        return filename_end

# make_picture("some text big\nsome text small\nsome text small\n\nnext_text",'1.jpg')
