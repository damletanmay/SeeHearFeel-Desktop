#!/usr/bin/env python
# coding: utf-8

# In[2]:


import re
import os
import json
import sys
import nltk
import time
import shutil
import random
import pathlib
import platform
import tkinter as tk
from moviepy.editor import *
from tkinter import filedialog
from tkinter import messagebox
from nltk.corpus import stopwords
from tkinter.ttk import Progressbar
from nltk.tokenize import word_tokenize
from nltk.stem import WordNetLemmatizer

#  Some essential public variables
cwd = os.getcwd()
os_name = platform.system().lower()
assets_file_path = ""

if os_name == 'windows':
    assets_file_path = cwd + "\\assets\\"
else:
    assets_file_path = cwd + "/assets/"



# In[3]:


def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS2
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)


# In[4]:


def clean_text(text):
    #tokenizing the sentence
    text.lower()
    #tokenizing the sentence
    words = word_tokenize(text)

    tagged = nltk.pos_tag(words)
    tense = {}
    tense["future"] = len([word for word in tagged if word[1] == "MD"])
    tense["present"] = len([word for word in tagged if word[1] in ["VBP", "VBZ","VBG"]])
    tense["past"] = len([word for word in tagged if word[1] in ["VBD", "VBN"]])
    tense["present_continuous"] = len([word for word in tagged if word[1] in ["VBG"]])

    #stopwords that will be removed
    # stop_words = set(["I'm","mightn't", 're', 'wasn', 'wouldn', 'be', 'has', 'that', 'does', 'shouldn', 'do', "you've",'off', 'for', "didn't", 'm', 'ain', 'haven', "weren't", 'are', "she's", "wasn't", 'its', "haven't", "wouldn't", 'don', 'weren', 's', "you'd", "don't", 'doesn', "hadn't", 'is', 'was', "that'll", "should've", 'a', 'then', 'the', 'mustn', 'i', 'nor', 'as', "it's", "needn't", 'd', 'am', 'have',  'hasn', 'o', "aren't", "you'll", "couldn't", "you're", "mustn't", 'didn', "doesn't", 'll', 'an', 'hadn', 'whom', 'y', "hasn't", 'itself', 'couldn', 'needn', "shan't", 'isn', 'been', 'such', 'shan', "shouldn't", 'aren', 'being', 'were', 'did', 'ma', 't', 'having', 'mightn', 've', "isn't", "won't"])
    stop_words = [
        "i", "me", "my", "myself", "we", "our", "ours", "ourselves", "you", "your", "yours", "yourself", "yourselves",
        "he", "him", "his", "himself", "she", "her", "hers", "herself", "it", "its", "itself", "they", "them", "their",
        "theirs", "themselves", "what", "which", "who", "whom", "this", "that", "these", "those", "am", "is", "are", "was",
        "were", "be", "been", "being", "have", "has", "had", "having", "do", "does", "did", "doing", "a", "an", "the", "and",
        "but", "if", "or", "because", "as", "until", "while", "of", "at", "by", "for", "with", "about", "against", "between",
        "into", "through", "during", "before", "after", "above", "below", "to", "from", "up", "down", "in", "out", "on", "off",
        "over", "under", "again", "further", "then", "once", "here", "there", "when", "where", "why", "how", "all", "any",
        "both", "each", "few", "more", "most", "other", "some", "such", "no", "nor", "not", "only", "own", "same", "so",
        "than", "too", "very", "s", "t", "can", "will", "just", "don", "should", "now"
    ]

    #removing stopwords and applying lemmatizing nlp process to words
    lr = WordNetLemmatizer()
    filtered_text = []
    for w,p in zip(words,tagged):
        if w not in stop_words:
            if p[1]=='VBG' or p[1]=='VBD' or p[1]=='VBZ' or p[1]=='VBN' or p[1]=='NN':
                filtered_text.append(lr.lemmatize(w,pos='v'))
            elif p[1]=='JJ' or p[1]=='JJR' or p[1]=='JJS'or p[1]=='RBR' or p[1]=='RBS':
                filtered_text.append(lr.lemmatize(w,pos='a'))

            else:
                filtered_text.append(lr.lemmatize(w))

    #adding the specific word to specify tense
    words = filtered_text
    temp=[]
    for w in words:
        if w=='I':
            temp.append('Me')
        else:
            temp.append(w)
    words = temp
    probable_tense = max(tense,key=tense.get)

    if probable_tense == "past" and tense["past"]>=1:
        temp = ["Before"]
        temp = temp + words
        words = temp
    elif probable_tense == "future" and tense["future"]>=1:
        if "Will" not in words:
                temp = ["Will"]
                temp = temp + words
                words = temp
        else:
            pass
    elif probable_tense == "present":
        if tense["present_continuous"]>=1:
            temp = ["Now"]
            temp = temp + words
            words = temp
    return words


# In[5]:


def extract_text_from_srt(srt_file_path):
    subtitles = []
    with open(resource_path(srt_file_path), 'r', encoding='utf-8') as file:
        lines = file.readlines()
        sub = None
        for line in lines:
            line = line.strip()
            if line.isdigit():
                if sub:
                    subtitles.append(sub)
                sub = {'index': int(line), 'text': ''}
            elif '-->' in line:
                pass  # Skip time stamps
            elif line:  # Non-empty line assumed to be subtitle text
                if sub:
                    sub['text'] += line + ' '
        if sub:  # Append the last subtitle if it exists
            subtitles.append(sub)

    sub_all = ""

    for sub in subtitles:
        sub_all+=sub['text'].strip() + " "

    sub_all = re.sub(r'[^A-Za-z0-9\s ]', '', sub_all) # replace everything except space

    return sub_all


# In[6]:


def list_files_in_directory(directory_path):
    # List all files in the directory
    files = os.listdir(resource_path(directory_path))

    # Convert each file name to string format
    files_string_format = [str(file).lower() for file in files]

    return files_string_format


# In[7]:


# get movie order of sign language
def make_video_order(words):
    assets = list_files_in_directory(assets_file_path) # get all assets

    video_order = []
    for word in words:
        if word.lower() +".mp4" not in assets:
            for w in word:
                video_order.append(w+".mp4")
        else:
            video_order.append(word+".mp4")
    return video_order


# In[8]:


# make movie
def make_movie(video_order,og_video_file_path,destination_path):
    video_clips = []
    sign_language_video = VideoFileClip(assets_file_path + video_order[0])

    og_video = VideoFileClip(resource_path(og_video_file_path))

    for i in video_order[1:]:
        try:
            video_clip = VideoFileClip(resource_path(assets_file_path.capitalize() + i))
            sign_language_video = concatenate_videoclips([sign_language_video,video_clip])
            # setting.exe
            if(round(sign_language_video.duration) >= round(og_video.duration)):
                sign_language_video.duration = og_video.duration # set same duration
                break

        except Exception as e:
            print(e)
            print("Error in File "+i)
            return False

    sign_language_video.write_videofile(destination_path + "/"+ "sign_language_video" + og_video_file_path[-4:], codec="libx264")
    return True


# In[9]:


def format_destination(directory_path):
    # Get list of all files in the directory
    files = os.listdir(resource_path(directory_path))
    if len(files) != 0:
        # Iterate over each file and delete it
        for file in files:
            file_path = os.path.join(directory_path, file)
            os.remove(file_path)


# In[13]:


def swap_commentary(video_file,commentary_file,destination_folder):
    # Load the video file
    video_clip = VideoFileClip(resource_path((video_file)))

    # Load the new audio file
    audio_clip = AudioFileClip(resource_path(commentary_file))

    audio_clip.duration = video_clip.duration
    # Replace the audio of the video clip with the new audio clip
    video_clip = video_clip.set_audio(audio_clip)

    # Write the modified video with the replaced audio to a new file
    video_clip.write_videofile(destination_folder+"/movie_with_commentary"+video_file[-4:], codec="libx264")

    # Close the clips
    video_clip.close()
    audio_clip.close()


# In[14]:


class VideoUploader:

    def __init__(self, root):

        self.root = root
        self.root.title("See Hear Feel")
        self.root.geometry("400x500")

        # title
        self.title_label = tk.Label(root, text="SeeHearFeel", borderwidth=3, relief="solid", font=("Helvetica", 20))
        self.title_label.pack(padx=10, pady=10)

        # Instructions
        self.text = tk.Label(root, text="Enter all required files to create the Movie")
        self.text.pack(pady=10)

        # Progress Bar
        self.progress = Progressbar(self.root, orient="horizontal", length=300, mode="determinate", style="TProgressbar")
        self.progress.pack(pady=10)
        self.progress["maximum"] = 100

        # Select Movie button
        self.movie_button = tk.Button(self.root, text="Select Movie", command=lambda: self.upload_file("movie"), width=30)
        self.movie_button.pack(pady=10)

        # Select Subtitles button
        self.subtitles_button = tk.Button(self.root, text="Select Subtitles", command=lambda: self.upload_file("subtitles"), width=30)
        self.subtitles_button.pack(pady=10)

        # Select Audio Commentary button
        self.commentary_button = tk.Button(self.root, text="Select Audio Commentary", command=lambda: self.upload_file("commentary"), width=30)
        self.commentary_button.pack(pady=10)

        # Select Folder button
        self.folder_button = tk.Button(self.root, text="Select Destination Folder", command=lambda: self.upload_file("folder"), width=30)
        self.folder_button.pack(pady=10)

        # create DCP button
        self.dcp_button = tk.Button(self.root, text="Create Movie", command = self.display_textbox, width=20)
        self.dcp_button.pack(pady=10)
        self.dcp_button.config(state=tk.DISABLED)

        self.uploaded_files = {"movie": None, "subtitles": None, "commentary": None,"folder":None}

    def handle_choice(self,choice):
        # if user clicks yes
        if choice:
            self.create_dcp()

    def display_textbox(self):
        choice = messagebox.askyesno("Alert", "The {} folder will be completely erased and Movie will be created, Click Yes to continue".format(self.uploaded_files["folder"]))
        self.handle_choice(choice)

    def change_dcp_box(self):
        if (self.uploaded_files["movie"] is not None) and (self.uploaded_files["subtitles"] is not None) and (self.uploaded_files["commentary"] is not None) and (self.uploaded_files["folder"] is not None):
            self.dcp_button.config(state=tk.NORMAL)
        else:
            self.dcp_button.config(state=tk.DISABLED)

    def upload_file(self, file_type):

        if file_type == "movie":
            self.uploaded_files["movie"] = filedialog.askopenfilename(filetypes=[("Video Files", "*.mp4 *.avi")])
            if (self.uploaded_files["movie"] != ""):
                self.movie_button.config(text=self.uploaded_files["movie"][self.uploaded_files["movie"].rfind('/')+1:])
                self.change_dcp_box()
        if file_type == "subtitles":
            self.uploaded_files["subtitles"] = filedialog.askopenfilename(filetypes=[("Subtitle Files", "*.srt *.vtt")])
            if (self.uploaded_files["subtitles"] != ""):
                self.subtitles_button.config(text=self.uploaded_files["subtitles"][self.uploaded_files["subtitles"].rfind('/')+1:])
                self.change_dcp_box()
        if file_type == "commentary":
            self.uploaded_files["commentary"] = filedialog.askopenfilename(filetypes=[("MP3 Files", "*.mp3")])
            if (self.uploaded_files["commentary"] != ""):
                self.commentary_button.config(text=self.uploaded_files["commentary"][self.uploaded_files["commentary"].rfind('/')+1:])
                self.change_dcp_box()
        if file_type == "folder":
            self.uploaded_files["folder"] = filedialog.askdirectory(title="Select Folder")
            if (self.uploaded_files["folder"] != ""):
                self.folder_button.config(text=self.uploaded_files["folder"][self.uploaded_files["folder"].rfind('/')+1:])
                self.change_dcp_box()

    def movie_created(self):
        # display message
        messagebox.showinfo("Movie Successfully Created!","Movie created in folder {}".format(self.uploaded_files["folder"]))

        # reset everything
        self.progress["value"] = 0

        self.uploaded_files = {"movie": None, "subtitles": None, "commentary": None,"folder":None}

        self.movie_button.config(text="Select Movie")
        self.subtitles_button.config(text="Select Subtitles")
        self.commentary_button.config(text="Select Audio Commentary")
        self.folder_button.config(text="Select Destination Folder")

        self.change_dcp_box()

    def create_dcp(self):

        format_destination(self.uploaded_files["folder"]) # format destination folder

        self.progress["value"] = 2
        self.root.update_idletasks()

        subtitles = extract_text_from_srt(self.uploaded_files["subtitles"])

        self.progress["value"] = 7
        self.root.update_idletasks()

        words = clean_text(subtitles) # get all the words


        self.progress["value"] = 15
        self.root.update_idletasks()


        video_order = make_video_order(words) # get video order


        self.progress["value"] = 20
        self.root.update_idletasks()


        isMovieDone = make_movie(video_order, self.uploaded_files["movie"], self.uploaded_files["folder"]) # make sign language video

        self.progress["value"] = 35
        self.root.update_idletasks()

        if isMovieDone:
            og_video_destination = self.uploaded_files["folder"]
            subtitles_destination = self.uploaded_files["folder"]
            subtitles_destination_2 = self.uploaded_files["folder"]

            # configure paths
#             if os_name == 'windows':
            og_video_destination += "//movie" + self.uploaded_files["movie"][-4:]
            subtitles_destination += "//movie" + self.uploaded_files["subtitles"][-4:]
            subtitles_destination_2 += "//movie_with_commentary" + self.uploaded_files["subtitles"][-4:]
#             else:
#                 og_video_destination += "//movie" + self.uploaded_files["movie"][-4:]
#                 subtitles_destination += "//movie" + self.uploaded_files["subtitles"][-4:]
#                 subtitles_destination_2 += "//movie_with_commentary" + self.uploaded_files["subtitles"][-4:]


            self.progress["value"] = 45
            self.root.update_idletasks()

            # copy files
            shutil.copy(self.uploaded_files["subtitles"],subtitles_destination) # copy subtitles

            self.progress["value"] = 57
            self.root.update_idletasks()

            shutil.copy(self.uploaded_files["movie"],og_video_destination) # copy original video file

            self.progress["value"] = 65
            self.root.update_idletasks()

            shutil.copy(self.uploaded_files["subtitles"],subtitles_destination_2) # copy original video file

            self.progress["value"] = 75
            self.root.update_idletasks()

            swap_commentary(self.uploaded_files["movie"],self.uploaded_files["commentary"],self.uploaded_files["folder"])

            self.progress["value"] = 100
            self.root.update_idletasks()

            self.movie_created()

        else:
            messagebox.showinfo("Alert!","Movie creation failed")


# In[15]:


if __name__ == "__main__":
    root = tk.Tk()
    style = tk.ttk.Style()
    style.configure("TButton", font=("Helvetica", 12), padding=5)
    style.configure("TProgressbar", thickness=15)
    uploader = VideoUploader(root)
    root.mainloop()
