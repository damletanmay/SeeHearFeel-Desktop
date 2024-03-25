# %%
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
import threading
import tkinter as tk
from tkinter import ttk
from moviepy.editor import *
from tkinter import filedialog
from tkinter import messagebox
from nltk.corpus import stopwords
from tkinter.ttk import Progressbar
from nltk.tokenize import word_tokenize
from nltk.stem import WordNetLemmatizer
from moviepy.video.fx.resize import resize

# %%
# this method is to get resource path when using assets for software
def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
        
    return os.path.join(base_path, relative_path)

#  Some essential public variables
cwd = os.getcwd()
os_name = platform.system().lower()
assets_file_path = os.path.join(cwd,"assets")
assets_file_path+='\\'

assets_file_path = resource_path(assets_file_path)
movie_paths = resource_path("movie_paths.txt")

# %%
# this function uses 
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

# %%
# extract text from vtt or srt files
def extract_text(srt_file_path):
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

# %%
# List all files in the directory
def list_files_in_directory(directory_path):
    files = os.listdir(resource_path(directory_path))
    
    # Convert each file name to string format
    files_string_format = [str(file).lower() for file in files]
    
    return files_string_format

# %%
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

# %%
def swap_commentary(video_clip,commentary_file,destination_path):
    
    # Load the new audio file

    audio_clip = AudioFileClip(resource_path(commentary_file))
    audio_clip.duration = video_clip.duration 
    # Replace the audio of the video clip with the new audio clip
    video_clip = video_clip.set_audio(audio_clip)

    # Write the modified video with the replaced audio to a new file
    video_clip.write_videofile(destination_path, codec="libx264")

    # Close the clips
    video_clip.close()
    audio_clip.close()

# %%
# make movie
def make_movie(video_order,og_video_file_path,audio_commentary_file_path,destination_path,progress_bar,root):

    progress_bar["value"] = 35
    root.update_idletasks()

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
            return False,None

    progress_bar["value"] = 50
    root.update_idletasks()

    # Resize the sign language video to 30% of its original size
    sign_language_video = resize(sign_language_video,width=og_video.w // 3)
    
    # Create a composite video with main video on the left and sign language video on the bottom right
    # sign_language_video = clips_array([[og_video, sign_language_video.set_position(("right", "bottom"))]])
    
    sign_language_video = CompositeVideoClip([og_video.set_duration(sign_language_video.duration), sign_language_video.set_position(("right", "bottom"))])

    progress_bar["value"] = 70
    root.update_idletasks()

    # write integrated video to destination video
    destination_path_video = os.path.join(destination_path, "movie" + og_video_file_path[-4:])
    
    swap_commentary(sign_language_video,audio_commentary_file_path,destination_path_video)

    progress_bar["value"] = 80
    root.update_idletasks()

    return True


# %%
# To open File Explorer
def open_file_explorer(path):
    os.startfile(os.path.abspath(path))

# To add movie path to each file
def add_movie_path(filename, path):
    with open(filename, 'a') as file:
        file.write(path + '\n')

def load_movie_paths(filename):
    unique_paths = set()  # Use a set to eliminate duplicates
    if os.path.exists(filename):
        with open(filename, 'r') as file:
            for line in file:
                path = line.strip()
                if os.path.exists(path):
                    unique_paths.add(path)
    return list(unique_paths)  # Convert set back to a list

# %%
def format_destination(directory_path):
    # Get list of all files in the directory
    files = os.listdir(resource_path(directory_path))
    if len(files) != 0:
        # Iterate over each file and delete it
        for file in files:
            file_path = os.path.join(directory_path, file)
            os.remove(file_path)

# %%
class VideoUploader:
    
    def __init__(self, root):
        # creating a notebook
        self.notebook = ttk.Notebook(root,width=800, height=500)
        self.notebook.pack(fill='both', expand=True)

        # creating main window (to create movies)
        self.root = ttk.Frame(self.notebook)
        self.notebook.add(self.root,text = "Create Movie")
        self.notebook.select(0) # preselect first window
        
        # title
        self.title_label = tk.Label(self.root, text="SeeHearFeel", borderwidth=3, relief="solid", font=("Helvetica", 20))
        self.title_label.pack(padx=10, pady=10)
        
        # Instructions
        self.text = tk.Label(self.root, text="Enter all required files to create the Movie")
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
        
        self.dcp_button = tk.Button(self.root, text="Create Movie", command = threading.Thread(target=self.display_textbox).start, width=20)
        self.dcp_button.pack(pady=10)
        self.dcp_button.config(state=tk.DISABLED)
        
        self.uploaded_files = {"movie": None, "subtitles": None, "commentary": None,"folder":None}

        # create library page
        self.library = ttk.Frame(self.notebook)
        self.notebook.add(self.library,text = "Movie Library")
        self.processed_movies_path = load_movie_paths(movie_paths) # get all movie paths

        # a text box 
        self.library_text_box = tk.Label(self.library, text="Double Click a Folder to open it")
        self.library_text_box.pack(padx=10, pady=10)

        if len(self.processed_movies_path) == 0:
            # If Libary is empty display below button
            self.library_text_box = self.library_text_box.config(text="Library is empty!")

        # scroll bar
        self.scrollbar = tk.Scrollbar(self.library)
        self.scrollbar = tk.Scrollbar(self.library, highlightthickness=10, borderwidth=10)
        self.scrollbar.pack(side="right", fill="y")

        self.listbox = tk.Listbox(self.library, yscrollcommand=self.scrollbar.set, selectmode=tk.SINGLE)

        for path in self.processed_movies_path:
            self.listbox.insert(tk.END, path)

        self.listbox.pack(side="right", fill="both", expand=True)

        self.scrollbar.config(command=self.listbox.yview)

        self.listbox.bind("<Double-1>", self.on_select)

    # on double click of a movie path, handle 
    def on_select(self,event):
        selected_index = self.listbox.curselection()
        if selected_index:
            selected_path = self.listbox.get(selected_index[0])
            open_file_explorer(selected_path)
  
    # display alert 
    def display_textbox(self):
        choice = messagebox.askyesno("Alert", "The {} folder will be completely erased and Movie will be created, Click Yes to continue".format(self.uploaded_files["folder"]))
         # when user clicks yes create 
        if choice:
            # try to create a movie
            try:
                self.create_movie()
            except Exception as e:
                print(e)
                self.reset_everything() # reset everything if some error occurs 
                messagebox.showinfo("Alert!","Movie creation failed")        
    
    # change_dcP_box whenever each file is updated
    def change_dcp_box(self):
        # if all files are uploaded, disable the button else keep it normal
        if (self.uploaded_files["movie"] is not None) and (self.uploaded_files["subtitles"] is not None) and (self.uploaded_files["commentary"] is not None) and (self.uploaded_files["folder"] is not None):
            self.dcp_button.config(state=tk.NORMAL)
        else:
            self.dcp_button.config(state=tk.DISABLED)
    
    # upload file paths to uploaded_files variable
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

    # reset buttons once process is over
    def reset_everything (self):
        # reset everything 
        self.progress["value"] = 0
        
        self.uploaded_files = {"movie": None, "subtitles": None, "commentary": None,"folder":None}
        
        self.movie_button.config(text="Select Movie")
        self.subtitles_button.config(text="Select Subtitles")
        self.commentary_button.config(text="Select Audio Commentary")
        self.folder_button.config(text="Select Destination Folder")
        
        self.change_dcp_box()
        
    def create_movie(self):
        self.dcp_button.config(state=tk.DISABLED) # disable the state
        
        format_destination(self.uploaded_files["folder"]) # format destination folder
        
        # update progress bar
        self.progress["value"] = 2
        self.root.update_idletasks()
        
        # extract text from subtitles
        subtitles = extract_text(self.uploaded_files["subtitles"])
        
         # update progress bar
        self.progress["value"] = 7
        self.root.update_idletasks()
        
         # get words inside subtitles
        words = clean_text(subtitles) # get all the words     

        # update progress bar 
        self.progress["value"] = 15
        self.root.update_idletasks()
        
        # get video order 
        video_order = make_video_order(words)
               
        # update progress bar
        self.progress["value"] = 20
        self.root.update_idletasks()
        
        isMovieDone = make_movie(video_order, self.uploaded_files["movie"],self.uploaded_files["commentary"], self.uploaded_files["folder"],self.progress,self.root) # make sign language video

        if isMovieDone:
            
            add_movie_path(movie_paths,self.uploaded_files["folder"]) # add movie path, when movie is done

            # copy subtitles
            subtitles_destination = self.uploaded_files["folder"]
            subtitles_destination = os.path.join(self.uploaded_files["folder"],"movie"+ self.uploaded_files["subtitles"][-4:])
            shutil.copy(self.uploaded_files["subtitles"],subtitles_destination) # copy subtitles
            
            self.progress["value"] = 100
            self.root.update_idletasks()

            # display message
            messagebox.showinfo("Movie Successfully Created!","Movie created in folder {}".format(self.uploaded_files["folder"]))
            self.listbox.update()
            self.reset_everything()
            
        else:
            self.reset_everything()
            messagebox.showinfo("Alert!","Movie creation failed")

# %%
if __name__ == "__main__":
    root = tk.Tk()
    root.resizable(width=False,height=False)
    style = tk.ttk.Style()
    style.configure("TButton", font=("Helvetica", 12), padding=5)
    style.configure("TProgressbar", thickness=15)
    uploader = VideoUploader(root)
    root.mainloop()


