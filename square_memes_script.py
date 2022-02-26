from PIL import Image,ImageDraw,ImageFont

def make_picture(text,file_name):
    num=text.count('\n')
    text=text.split(sep='\n')
    file_name_end = file_name[:-4] + '_done.png'
    for i in range(num+1):
        text_small=text[i]
        font_size=20
        if i==0:
            image2=Image.open(file_name).convert('RGBA')
        else:
            image2 = Image.open(file_name_end).convert('RGBA')
        x,y=image2.size
        image2=image2.resize((300,int(300*y/x)),Image.ANTIALIAS)
        x,y=image2.size
        image=Image.new('RGBA',(x+50,y+70),(0,0,0))
        draw = ImageDraw.Draw(image)
        startx=int((x+50)/2)-int(x/2)
        starty=int((y+50)/2)-int(y/2)
        image.paste(image2,(startx,starty),  image2)
        draw.rectangle((startx-5,starty-5,startx+x+5,starty+y+5),outline=(255,255,255))
        font = ImageFont.truetype(font='arial.ttf', size=font_size, encoding='unic')
        # text='HELLO пидарас'
        w, h = draw.textsize(text_small,font=font)
        while w>300:
            font = ImageFont.truetype(font='arial.ttf', size=font_size, encoding='unic')
            w, h = draw.textsize(text_small, font=font)
            font_size-=1
        draw.text((startx+int(x/2)-int(w/2),starty+y+20-int(h/2)), text_small, font=font, fill=(255,255,255,255))
        # image.show()
        # file_name=file_name[:-4]+'_done.png'
        image.save(file_name_end,'PNG')
    return file_name_end