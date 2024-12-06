import moviepy.editor as me
# import moviepy.video as mv
# import moviepy.video.fx.all as vfx
from PIL import Image #, ImageDraw, ImageFont
# import os


def normalize_picture(path_to_picture, size):
    img0 = Image.open(path_to_picture).convert('RGBA')
    x, y = img0.size
    # img0.show()
    # print(x, y)
    if x>size[0]:
        img0 = img0.resize((size[0]-50, int((size[0]-50) * y / x)), Image.ANTIALIAS)
        x, y = img0.size
        # print(x,y)
    if y>size[1]:
        img0 = img0.resize((int((size[1]-50) * x / y),size[1]-50), Image.ANTIALIAS)
        x, y = img0.size
        # print(x, y)
    startx = int(size[0] / 2 - x / 2)
    starty = int(size[1] / 2 - y / 2)
    img1 = Image.new('RGBA', (size[0], size[1]), (0, 0, 0))
    img1.paste(img0, (startx, starty), img0)
    path_to_picture_end = path_to_picture[:-4] + '_norm.png'
    img1.save(path_to_picture_end, 'PNG')
    return path_to_picture_end


def create_videofragment(path_to_picture, dur):
    vid = me.ImageClip(path_to_picture, duration=dur)
    return vid


data = {'x': 400, 'y': 400, 'vid_durations': [3, 3, 3], 'folder': 'test_folder', 'audio_dipl': -3}


def create_video(data):
    a = []
    sum_dur=0
    if data['audio_dipl']<0:
        a.append(create_videofragment(normalize_picture(f'videos/{data["folder"]}/0.png', (data['x'], data['y'])),abs(data['audio_dipl'])))
        audio1 = me.AudioFileClip(f'videos/{data["folder"]}/music.mp3').subclip(t_end=sum(data['vid_durations'])+abs(data['audio_dipl']))
        audio1.write_audiofile(f'videos/{data["folder"]}/music_norm.mp3')
        sum_dur = abs(data['audio_dipl'])
    for i in range(len(data['vid_durations'])):
        # print(i)
        # print(f'videos/{data["folder"]}/{i + 1}.png')
        # print(data['vid_durations'][i])
        # print()
        a.append(
            create_videofragment(
                normalize_picture(f'videos/{data["folder"]}/{i + 1}.png', (data['x'], data['y'])),data['vid_durations'][i]))
        sum_dur += data['vid_durations'][i]
    clip_fin = me.concatenate_videoclips(a)
    if data['audio_dipl']>=0:
        audio1 = me.AudioFileClip(f'videos/{data["folder"]}/music.mp3').subclip(t_start=abs(data['audio_dipl']),t_end=sum_dur+abs(data['audio_dipl']))
        audio1.write_audiofile(f'videos/{data["folder"]}/music_norm.mp3')
    fin_path=f'videos/{data["folder"]}/fin.mp4'
    clip_fin.write_videofile(fin_path, fps=24,
                             audio=f'videos/{data["folder"]}/music_norm.mp3',
                             audio_codec='libmp3lame', audio_bitrate='50k')
    return fin_path

# import json
# with open('presets.json','r') as f:
#     data=json.load(f)
# create_video(data['в главных ролях'])
